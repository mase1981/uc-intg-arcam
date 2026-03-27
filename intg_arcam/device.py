"""
Arcam FMJ device implementation for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import functools
import logging
import time
from typing import Any
from arcam.fmj import (
    CommandCodes, ResponsePacket, SourceCodes,
    AmxDuetRequest, ResponseException, NotConnectedException,
    UnsupportedZone, CommandInvalidAtThisTime, CommandNotRecognised,
    ApiModel,
    APIVERSION_450_SERIES, APIVERSION_860_SERIES,
    APIVERSION_HDA_SERIES, APIVERSION_SA_SERIES,
    APIVERSION_PA_SERIES, APIVERSION_ST_SERIES,
)
from ucapi.media_player import Attributes as MediaAttributes, States as MediaStates
from ucapi.remote import Attributes as RemoteAttributes, States as RemoteStates
from ucapi.sensor import Attributes as SensorAttributes, States as SensorStates
from ucapi.select import Attributes as SelectAttributes, States as SelectStates
from ucapi_framework import ExternalClientDevice, DeviceEvents
from intg_arcam.config import ArcamConfig, PollingMode

_LOG = logging.getLogger(__name__)


def _tracks_interaction(method):
    """Decorator to track user interaction timing for poll suppression."""
    @functools.wraps(method)
    async def wrapper(self, *args, **kwargs):
        self._last_command_time = time.monotonic()
        return await method(self, *args, **kwargs)
    return wrapper


RC5_COMMANDS = {
    "CURSOR_UP": (0x10, 0x56),
    "CURSOR_DOWN": (0x10, 0x55),
    "CURSOR_LEFT": (0x10, 0x51),
    "CURSOR_RIGHT": (0x10, 0x50),
    "OK": (0x10, 0x57),
    "MENU": (0x10, 0x52),
    "BACK": (0x10, 0x33),
    "INFO": (0x10, 0x37),
    "DISPLAY": (0x10, 0x3B),
    "MODE": (0x10, 0x20),
    "DIRECT": (0x10, 0x0A),
    "TUNER_BAND": (0x10, 0x44),
    "PRESET_UP": (0x10, 0x1E),
    "PRESET_DOWN": (0x10, 0x1D),
    "INPUT_CD": (0x10, 0x76),
    "INPUT_BD": (0x10, 0x62),
    "INPUT_AV": (0x10, 0x5E),
    "INPUT_SAT": (0x10, 0x1B),
    "INPUT_PVR": (0x10, 0x60),
    "INPUT_VCR": (0x10, 0x75),
    "INPUT_AUX": (0x10, 0x63),
    "INPUT_FM": (0x10, 0x1C),
    "INPUT_DAB": (0x10, 0x48),
    "INPUT_NET": (0x10, 0x5C),
    "INPUT_USB": (0x10, 0x5D),
    "INPUT_STB": (0x10, 0x64),
    "INPUT_UHD": (0x10, 0x7D),
    "INPUT_BT": (0x10, 0x7A),
    "INPUT_GAME": (0x10, 0x61),
    "STEREO": (0x10, 0x6B),
    "DOLBY_PLII_MOVIE": (0x10, 0x6E),
    "DOLBY_PLII_MUSIC": (0x10, 0x6E),
    "DTS_NEO6_CINEMA": (0x10, 0x6F),
    "DTS_NEO6_MUSIC": (0x10, 0x70),
}


class ArcamDevice(ExternalClientDevice):
    """Arcam FMJ receiver using external client pattern."""

    def __init__(self, device_config: ArcamConfig, **kwargs):
        super().__init__(
            device_config,
            **kwargs,
            enable_watchdog=True,
            watchdog_interval=10,
            reconnect_delay=5,
            max_reconnect_attempts=0,
        )
        self._device_config = device_config
        self._client = None
        self._arcam_state = None
        self._process_task: asyncio.Task | None = None
        self._maintain_task: asyncio.Task | None = None

        # Validate polling config
        try:
            self._polling_mode = PollingMode(device_config.polling_mode)
        except ValueError:
            _LOG.warning("%s Unknown polling_mode '%s', falling back to 'essential'",
                        f"[{device_config.name} ({device_config.host})]",
                        device_config.polling_mode)
            self._polling_mode = PollingMode.ESSENTIAL
        self._poll_interval = max(30, min(600, device_config.poll_interval))

        self._last_command_time: float = 0.0
        self._debounce_tasks: dict[int, asyncio.Task] = {}
        self._initial_sync_complete: bool = False
        self._model_detected: bool = False
        self._trickle_task: asyncio.Task | None = None

        # Staleness tracking — all command codes start stale
        self._stale: set[CommandCodes] = set()
        self._mark_all_stale()

        self._power = False
        self._volume = 0
        self._muted = False
        self._source = None
        self._source_list = []
        self._sound_mode = None
        self._sound_mode_list = []
        self._audio_format = None
        self._room_eq = None
        self._room_eq_index: int = 0
        self._room_eq_names: dict[int, str] = {}

    @property
    def identifier(self) -> str:
        return self._device_config.identifier

    @property
    def name(self) -> str:
        return self._device_config.name

    @property
    def address(self) -> str:
        return self._device_config.host

    @property
    def log_id(self) -> str:
        return f"[{self.name} ({self.address})]"

    @property
    def power(self) -> bool:
        return self._power

    @property
    def volume(self) -> int:
        return self._volume

    @property
    def muted(self) -> bool:
        return self._muted

    @property
    def source(self) -> str | None:
        return self._source

    @property
    def source_list(self) -> list[str]:
        return self._source_list

    @property
    def sound_mode(self) -> str | None:
        return self._sound_mode

    @property
    def sound_mode_list(self) -> list[str]:
        return self._sound_mode_list

    @property
    def audio_format(self) -> str | None:
        return self._audio_format

    @property
    def room_eq(self) -> str | None:
        return self._room_eq

    # All command codes tracked for staleness (Groups 1, 2, 3)
    _ALL_TRACKED_COMMANDS: set[CommandCodes] = {
        # Group 1 — Immediate
        CommandCodes.POWER, CommandCodes.VOLUME,
        CommandCodes.MUTE, CommandCodes.CURRENT_SOURCE,
        # Group 2 — Trickle
        CommandCodes.DECODE_MODE_STATUS_2CH, CommandCodes.DECODE_MODE_STATUS_MCH,
        CommandCodes.INCOMING_AUDIO_FORMAT, CommandCodes.INCOMING_AUDIO_SAMPLE_RATE,
        CommandCodes.ROOM_EQUALIZATION, CommandCodes.ROOM_EQ_NAMES,
        CommandCodes.MENU,
        CommandCodes.INCOMING_VIDEO_PARAMETERS,
        # Group 3 — Tuner
        CommandCodes.DAB_STATION, CommandCodes.DLS_PDT_INFO,
        CommandCodes.RDS_INFORMATION, CommandCodes.TUNER_PRESET,
    }

    _TUNER_SOURCES = {"FM", "DAB"}

    _TUNER_COMMANDS = [
        CommandCodes.DAB_STATION, CommandCodes.DLS_PDT_INFO,
        CommandCodes.RDS_INFORMATION, CommandCodes.TUNER_PRESET,
    ]

    def _mark_all_stale(self) -> None:
        """Mark all tracked command codes as stale."""
        self._stale = set(self._ALL_TRACKED_COMMANDS)

    async def create_client(self) -> Any:
        """Create the Arcam client (required by ExternalClientDevice)."""
        from arcam.fmj.client import Client
        from arcam.fmj.state import State

        self._client = Client(self._device_config.host, self._device_config.port)
        self._arcam_state = State(self._client, self._device_config.zone)
        return self._client

    async def connect_client(self) -> None:
        """Connect the Arcam client (required by ExternalClientDevice)."""
        self._initial_sync_complete = False
        self._model_detected = False
        self._mark_all_stale()

        _LOG.info("%s Starting Arcam client", self.log_id)
        await self._client.start()

        _LOG.info("%s Registering state listener", self.log_id)
        await self._arcam_state.start()

        _LOG.info("%s Starting response processor with data listener", self.log_id)
        self._process_task = asyncio.create_task(self._run_process_loop_with_listener())

        await asyncio.sleep(0.5)

        # Group 0 + Group 1: synchronous immediate sync
        _LOG.info("%s Syncing immediate state (Group 0+1)", self.log_id)
        try:
            await self._sync_immediate_state()
        except Exception as err:
            _LOG.warning("%s Immediate state sync failed: %s, using defaults", self.log_id, err)
        finally:
            self._initial_sync_complete = True

        await self._initialize_state()

        # Start trickle background task for Groups 2/3
        self._trickle_task = asyncio.create_task(self._trickle_remaining_state())

        if self._polling_mode != PollingMode.OFF:
            self._maintain_task = asyncio.create_task(self._maintain_connection_loop())

    async def disconnect_client(self) -> None:
        """Disconnect the Arcam client (required by ExternalClientDevice)."""
        self._initial_sync_complete = False
        self._model_detected = False
        self._mark_all_stale()

        for task in self._debounce_tasks.values():
            if not task.done():
                task.cancel()
        self._debounce_tasks.clear()

        if self._trickle_task and not self._trickle_task.done():
            self._trickle_task.cancel()
            try:
                await self._trickle_task
            except asyncio.CancelledError:
                pass
            self._trickle_task = None

        if self._maintain_task and not self._maintain_task.done():
            self._maintain_task.cancel()
            try:
                await self._maintain_task
            except asyncio.CancelledError:
                pass
            self._maintain_task = None

        if self._process_task and not self._process_task.done():
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
            self._process_task = None

        if self._arcam_state:
            try:
                await self._arcam_state.stop()
            except Exception:
                pass

        if self._client:
            _LOG.info("%s Closing client connection", self.log_id)
            try:
                await self._client.stop()
            except Exception as err:
                _LOG.debug("%s Error during client stop: %s", self.log_id, err)
            finally:
                self._client = None
                self._arcam_state = None

    def check_client_connected(self) -> bool:
        """Check if the Arcam client is connected (required by ExternalClientDevice)."""
        if not self._client or not self._arcam_state:
            return False
        return self._client.connected

    async def maintain_connection(self) -> None:
        """Required by ExternalClientDevice but we use our own background task."""
        pass

    def _on_data_received(self, packet) -> None:
        """Callback when data is received from device - debounced per command code."""
        if not isinstance(packet, ResponsePacket):
            return
        self._stale.discard(packet.cc)
        existing = self._debounce_tasks.get(packet.cc)
        if existing and not existing.done():
            existing.cancel()
        self._debounce_tasks[packet.cc] = asyncio.create_task(
            self._debounced_update(packet.cc)
        )

    async def _debounced_update(self, cc: int) -> None:
        """Wait for debounce window then emit state update."""
        await asyncio.sleep(0.08)
        await self._handle_state_update()

    async def _run_process_loop_with_listener(self) -> None:
        """Run the arcam-fmj client process loop with data listener."""
        try:
            _LOG.debug("%s Starting client process loop with listener", self.log_id)
            with self._client.listen(self._on_data_received):
                await self._client.process()
        except asyncio.CancelledError:
            _LOG.debug("%s Client process loop cancelled", self.log_id)
            raise
        except Exception as err:
            _LOG.warning("%s Client process loop ended: %s (%s)",
                        self.log_id, err, type(err).__name__)
            self.events.emit(DeviceEvents.DISCONNECTED, self.identifier)

    async def _maintain_connection_loop(self) -> None:
        """Background task for periodic state refresh, mode-aware."""
        _LOG.info("%s Starting %s polling loop (interval=%ds)",
                 self.log_id, self._polling_mode.value, self._poll_interval)

        try:
            while True:
                # Wait for initial sync (Group 0+1) and trickle to complete
                if not self._initial_sync_complete:
                    await asyncio.sleep(1)
                    continue
                if self._trickle_task and not self._trickle_task.done():
                    await asyncio.sleep(1)
                    continue

                if self._polling_mode == PollingMode.ESSENTIAL:
                    if self._power:
                        codes = [CommandCodes.POWER, CommandCodes.VOLUME,
                                 CommandCodes.MUTE, CommandCodes.CURRENT_SOURCE]
                    else:
                        codes = [CommandCodes.POWER]

                    stagger_delay = self._poll_interval / len(codes)
                    for cc in codes:
                        await asyncio.sleep(stagger_delay)
                        if not (self._arcam_state and self._client and self._client.connected):
                            break
                        if time.monotonic() - self._last_command_time < self._poll_interval * 0.5:
                            _LOG.debug("%s Skipping poll, recent user interaction", self.log_id)
                            break
                        try:
                            await self._client.request(
                                self._device_config.zone, cc, bytes([0xF0]))
                        except asyncio.CancelledError:
                            raise
                        except Exception as err:
                            _LOG.debug("%s Poll error for %s: %s", self.log_id, cc, err)

                elif self._polling_mode == PollingMode.ALL:
                    await asyncio.sleep(self._poll_interval)
                    if not (self._arcam_state and self._client and self._client.connected):
                        continue
                    if time.monotonic() - self._last_command_time < self._poll_interval * 0.5:
                        _LOG.debug("%s Skipping poll, recent user interaction", self.log_id)
                        continue
                    # Query Group 1 directly, then mark remaining stale and re-trickle
                    for cc in [CommandCodes.POWER, CommandCodes.VOLUME,
                               CommandCodes.MUTE, CommandCodes.CURRENT_SOURCE]:
                        if not await self._query_command(cc, delay=0.3):
                            break
                    self._mark_all_stale()
                    self._trickle_task = asyncio.create_task(self._trickle_remaining_state())

        except asyncio.CancelledError:
            _LOG.debug("%s Polling loop cancelled", self.log_id)
            raise
        except Exception as err:
            _LOG.error("%s Error in polling loop: %s (%s)",
                      self.log_id, err, type(err).__name__)

    async def _query_command(self, cc: CommandCodes, delay: float = 0.3) -> bool:
        """Query a single command code with error handling.

        Returns True if query succeeded or was skipped (non-fatal error),
        False if connection was lost (caller should abort).
        """
        if not self._client or not self._client.connected:
            return False
        try:
            await self._client.request(self._device_config.zone, cc, bytes([0xF0]))
            self._stale.discard(cc)
        except UnsupportedZone:
            _LOG.debug("%s Unsupported zone for %s", self.log_id, cc)
            self._stale.discard(cc)
        except (CommandNotRecognised, CommandInvalidAtThisTime):
            _LOG.debug("%s Command not supported: %s", self.log_id, cc)
            self._stale.discard(cc)
        except ResponseException as e:
            _LOG.debug("%s Response error for %s: %s", self.log_id, cc, e)
        except NotConnectedException:
            _LOG.warning("%s Not connected querying %s", self.log_id, cc)
            return False
        except asyncio.TimeoutError:
            _LOG.warning("%s Timeout querying %s", self.log_id, cc)
        if delay > 0:
            await asyncio.sleep(delay)
        return True

    def _map_model_from_amx(self, data) -> bool:
        """Map an AMX duet response to an API model series.

        Matches the device_model string from the AMX response against the
        known model sets in the arcam-fmj library. Sets _api_model on the
        State object and _model_detected on this device.

        Returns True if the model string matched a known series.
        """
        model = data.device_model
        if model in APIVERSION_450_SERIES:
            self._arcam_state._api_model = ApiModel.API450_SERIES
        elif model in APIVERSION_860_SERIES:
            self._arcam_state._api_model = ApiModel.API860_SERIES
        elif model in APIVERSION_HDA_SERIES:
            self._arcam_state._api_model = ApiModel.APIHDA_SERIES
        elif model in APIVERSION_SA_SERIES:
            self._arcam_state._api_model = ApiModel.APISA_SERIES
        elif model in APIVERSION_PA_SERIES:
            self._arcam_state._api_model = ApiModel.APIPA_SERIES
        elif model in APIVERSION_ST_SERIES:
            self._arcam_state._api_model = ApiModel.APIST_SERIES
        else:
            return False
        self._model_detected = True
        return True

    async def _sync_immediate_state(self) -> None:
        """Group 0 (AMX duet) + Group 1 (power, volume, mute, source).

        Runs synchronously during connect. After completion, the UI can show
        meaningful media player state.
        """
        if not self._client or not self._client.connected:
            return

        # Group 0 — Model detection
        #
        # Determines the receiver's protocol series (450, 860, HDA, SA, PA, ST),
        # which controls source codes, RC5 command tables, and available features.
        # Getting this wrong means every source switch and mode change sends the
        # wrong RC5 code, and HDA-only sources like UHD become unavailable.
        #
        # Three detection methods are tried in order:
        #
        #   1. AMX beacon — the receiver may have already sent an unsolicited
        #      beacon that State._listen() stored in _amxduet. However, _listen()
        #      does NOT map _api_model from the beacon data, so we must do it here.
        #      Without this step, a beacon arriving before Group 0 would cause
        #      detection to be silently skipped (the old bug).
        #
        #   2. AMX duet query — direct request/response. Some receivers (e.g. JBL
        #      Synthesis SDP-58) don't respond to direct queries but do send
        #      periodic beacons. If a beacon happens to arrive during the 6-second
        #      request window, the library treats it as the response (any
        #      AmxDuetResponse resolves any AmxDuetRequest). This is why detection
        #      was intermittent before — it depended on beacon timing.
        #
        #   3. Capability probe — send SETUP (0x27), an HDA-specific command.
        #      If the receiver responds, it supports HDA commands → HDA series.
        #      If it responds with CommandNotRecognised, it doesn't → non-HDA.
        #      This is the reliable fallback for receivers where AMX duet is
        #      completely unavailable.
        #
        # If all three fail, _api_model stays at the library default (API450_SERIES).

        if self._model_detected:
            _LOG.debug("%s Model already detected (%s), skipping Group 0",
                      self.log_id, self._arcam_state._api_model)
        else:

            # Step 1: Check for AMX beacon already received by State._listen()
            if self._arcam_state._amxduet is not None:
                if self._map_model_from_amx(self._arcam_state._amxduet):
                    _LOG.info("%s Model detected via AMX beacon: %s → %s",
                             self.log_id,
                             self._arcam_state._amxduet.device_model,
                             self._arcam_state._api_model)

            # Step 2: AMX duet query (only if no beacon resolved the model)
            if not self._model_detected:
                try:
                    _LOG.debug("%s Querying AMX duet", self.log_id)
                    data = await self._client.request_raw(AmxDuetRequest())
                    self._arcam_state._amxduet = data
                    if self._map_model_from_amx(data):
                        _LOG.info("%s Model detected via AMX query: %s → %s",
                                 self.log_id, data.device_model,
                                 self._arcam_state._api_model)
                    else:
                        _LOG.warning(
                            "%s AMX duet returned unrecognized model: '%s'",
                            self.log_id, data.device_model)
                except ResponseException as e:
                    _LOG.debug("%s AMX duet response error: %s", self.log_id, e)
                except NotConnectedException:
                    _LOG.debug("%s Not connected during AMX duet query",
                              self.log_id)
                    return
                except asyncio.TimeoutError:
                    _LOG.debug("%s AMX duet query timeout, will try probe",
                              self.log_id)

            # Step 3: Capability probe — send HDA-specific SETUP command (0x27).
            # This reliably distinguishes HDA receivers from non-HDA when AMX
            # duet is unavailable. Non-HDA receivers reject the command with
            # CommandNotRecognised; HDA receivers return setup data.
            if not self._model_detected:
                try:
                    _LOG.debug("%s Probing with SETUP command (HDA-specific)",
                              self.log_id)
                    await self._client.request(
                        self._device_config.zone,
                        CommandCodes.SETUP, bytes([0xF0]))
                    self._arcam_state._api_model = ApiModel.APIHDA_SERIES
                    self._model_detected = True
                    _LOG.info("%s Model detected via probe: "
                             "SETUP command responded → HDA series",
                             self.log_id)
                except CommandNotRecognised:
                    # Receiver explicitly rejected the HDA command — it's not
                    # HDA. The API450_SERIES default is the best remaining guess.
                    self._model_detected = True
                    _LOG.info("%s Model probe: SETUP rejected "
                             "(CommandNotRecognised) → non-HDA, "
                             "using default %s",
                             self.log_id, self._arcam_state._api_model)
                except CommandInvalidAtThisTime:
                    # Receiver knows the command but can't handle it right now
                    # (e.g. during boot). Treat as HDA since it recognized it.
                    self._arcam_state._api_model = ApiModel.APIHDA_SERIES
                    self._model_detected = True
                    _LOG.info("%s Model detected via probe: "
                             "SETUP returned CommandInvalidAtThisTime → "
                             "HDA series (command recognized)",
                             self.log_id)
                except (asyncio.TimeoutError, ResponseException) as e:
                    _LOG.warning("%s Model probe failed: %s (%s), "
                                "using default %s", self.log_id,
                                e, type(e).__name__,
                                self._arcam_state._api_model)
                except NotConnectedException:
                    _LOG.debug("%s Not connected during model probe",
                              self.log_id)
                    return

            # Summary log — always emitted so every connect shows the model
            model_name = (self._arcam_state._amxduet.device_model
                          if self._arcam_state._amxduet else "unknown")
            _LOG.info("%s Model detection complete: %s → %s",
                     self.log_id, model_name,
                     self._arcam_state._api_model)

        # Group 1 — Immediate state
        _LOG.debug("%s Group 1: Querying power, volume, mute, source", self.log_id)
        for cc in [CommandCodes.POWER, CommandCodes.VOLUME,
                    CommandCodes.MUTE, CommandCodes.CURRENT_SOURCE]:
            if not await self._query_command(cc, delay=0.3):
                return

        _LOG.info("%s Immediate state sync complete", self.log_id)

    async def _trickle_remaining_state(self) -> None:
        """Background task: Groups 2 (trickle) and 3 (tuner).

        Queries remaining state with staleness checks — push events that
        arrive during trickle automatically skip redundant queries.
        """
        try:
            # Group 2 — Trickle by importance
            _LOG.debug("%s Group 2: Trickling secondary state", self.log_id)
            for cc in [
                CommandCodes.DECODE_MODE_STATUS_2CH,
                CommandCodes.DECODE_MODE_STATUS_MCH,
                CommandCodes.INCOMING_AUDIO_FORMAT,
                CommandCodes.INCOMING_AUDIO_SAMPLE_RATE,
                CommandCodes.ROOM_EQUALIZATION,
                CommandCodes.ROOM_EQ_NAMES,
                CommandCodes.MENU,
                CommandCodes.INCOMING_VIDEO_PARAMETERS,
            ]:
                if cc not in self._stale:
                    continue
                if not await self._query_command(cc, delay=0.4):
                    return

            # Parse room EQ names if available, update display
            self._parse_room_eq_names()
            if self._room_eq_index > 0:
                new_display = self._format_room_eq(self._room_eq_index)
                if new_display != self._room_eq:
                    self._room_eq = new_display
                    self._emit_update()

            # Group 3 — Tuner (conditional)
            if self._source in self._TUNER_SOURCES:
                _LOG.debug("%s Group 3: Trickling tuner state", self.log_id)
                for cc in self._TUNER_COMMANDS:
                    if self._source not in self._TUNER_SOURCES:
                        _LOG.debug("%s Group 3: Source changed away from tuner, aborting", self.log_id)
                        break
                    if cc not in self._stale:
                        continue
                    if not await self._query_command(cc, delay=0.4):
                        return

            _LOG.info("%s Trickle state sync complete", self.log_id)

        except asyncio.CancelledError:
            _LOG.debug("%s Trickle task cancelled", self.log_id)
            raise
        except Exception as err:
            _LOG.error("%s Error in trickle sync: %s (%s)",
                      self.log_id, err, type(err).__name__)

    async def _trickle_tuner_state(self) -> None:
        """Background task: query Group 3 tuner state only."""
        try:
            _LOG.debug("%s Trickling tuner state (runtime trigger)", self.log_id)
            for cc in self._TUNER_COMMANDS:
                if self._source not in self._TUNER_SOURCES:
                    _LOG.debug("%s Source changed away from tuner, aborting", self.log_id)
                    break
                if cc not in self._stale:
                    continue
                if not await self._query_command(cc, delay=0.4):
                    return
        except asyncio.CancelledError:
            _LOG.debug("%s Tuner trickle cancelled", self.log_id)
            raise
        except Exception as err:
            _LOG.error("%s Error in tuner trickle: %s (%s)",
                      self.log_id, err, type(err).__name__)

    async def _initialize_state(self) -> None:
        """Initialize local state from device state."""
        if not self._arcam_state:
            return

        try:
            power = self._arcam_state.get_power()
            self._power = power if power is not None else False

            raw_volume = self._arcam_state.get_volume()
            if raw_volume is not None:
                self._volume = self._arcam_vol_to_percent(raw_volume)
            else:
                self._volume = 0

            muted = self._arcam_state.get_mute()
            self._muted = muted if muted is not None else False

            source = self._arcam_state.get_source()
            if source is not None:
                self._source = source.name
            else:
                self._source = None

            source_list = self._arcam_state.get_source_list()
            if source_list:
                self._source_list = [src.name for src in source_list]
            else:
                self._source_list = []

            decode_mode = self._arcam_state.get_decode_mode()
            if decode_mode is not None:
                self._sound_mode = decode_mode.name

            decode_modes = self._arcam_state.get_decode_modes()
            if decode_modes:
                self._sound_mode_list = [m.name for m in decode_modes]

            audio_fmt = self._arcam_state.get_incoming_audio_format()
            if audio_fmt and isinstance(audio_fmt, tuple) and len(audio_fmt) >= 2:
                fmt, config = audio_fmt
                if fmt is not None:
                    self._audio_format = fmt.name

            room_eq_data = self._arcam_state._state.get(CommandCodes.ROOM_EQUALIZATION)
            if room_eq_data is not None:
                self._room_eq_index = int.from_bytes(room_eq_data, "big")
                self._room_eq = self._format_room_eq(self._room_eq_index)

            _LOG.info("%s Initial state: Power=%s Volume=%d Muted=%s Source=%s Sources=%s",
                     self.log_id, self._power, self._volume, self._muted, self._source,
                     self._source_list[:5] if self._source_list else [])

            self._emit_update()

        except Exception as err:
            _LOG.error("%s Failed to initialize state: %s (%s)",
                      self.log_id, err, type(err).__name__)

    async def _handle_state_update(self) -> None:
        """Handle state update from Arcam client."""
        if not self._arcam_state:
            return

        # Don't emit intermediate states during initial sync;
        # _initialize_state() will emit the authoritative state after sync.
        if not self._initial_sync_complete:
            return

        try:
            changed = False

            # Suppress power state changes briefly after user commands to avoid
            # ON→OFF→ON bounce during device power transitions.
            command_suppression = time.monotonic() - self._last_command_time < 3.0

            power = self._arcam_state.get_power()
            if power is not None and power != self._power and not command_suppression:
                self._power = power
                changed = True

            raw_volume = self._arcam_state.get_volume()
            if raw_volume is not None:
                volume = self._arcam_vol_to_percent(raw_volume)
                if volume != self._volume:
                    self._volume = volume
                    changed = True

            muted = self._arcam_state.get_mute()
            if muted is not None and muted != self._muted:
                self._muted = muted
                changed = True

            source = self._arcam_state.get_source()
            source_name = source.name if source else None
            if source_name is not None and source_name != self._source:
                old_source = self._source
                self._source = source_name
                changed = True
                # Trigger Group 3 trickle if switched to tuner and trickle is not running
                if (source_name in self._TUNER_SOURCES
                        and (old_source is None or old_source not in self._TUNER_SOURCES)
                        and (self._trickle_task is None or self._trickle_task.done())):
                    tuner_stale = any(cc in self._stale for cc in self._TUNER_COMMANDS)
                    if tuner_stale:
                        _LOG.debug("%s Source changed to tuner, triggering Group 3 trickle",
                                  self.log_id)
                        self._trickle_task = asyncio.create_task(
                            self._trickle_tuner_state()
                        )

            decode_mode = self._arcam_state.get_decode_mode()
            if decode_mode is not None:
                if decode_mode.name != self._sound_mode:
                    self._sound_mode = decode_mode.name
                    changed = True

            decode_modes = self._arcam_state.get_decode_modes()
            if decode_modes:
                modes = [m.name for m in decode_modes]
                if modes != self._sound_mode_list:
                    self._sound_mode_list = modes

            audio_fmt = self._arcam_state.get_incoming_audio_format()
            if audio_fmt and isinstance(audio_fmt, tuple) and len(audio_fmt) >= 2:
                fmt, config = audio_fmt
                if fmt is not None:
                    if fmt.name != self._audio_format:
                        self._audio_format = fmt.name
                        changed = True

            room_eq_data = self._arcam_state._state.get(CommandCodes.ROOM_EQUALIZATION)
            if room_eq_data is not None:
                idx = int.from_bytes(room_eq_data, "big")
                self._room_eq_index = idx
                room_eq = self._format_room_eq(idx)
                if room_eq != self._room_eq:
                    self._room_eq = room_eq
                    changed = True

            if changed:
                _LOG.debug("%s State updated: Power=%s Volume=%d Muted=%s Source=%s",
                          self.log_id, self._power, self._volume, self._muted, self._source)
                self._emit_update()

        except Exception as err:
            _LOG.error("%s Error handling state update: %s", self.log_id, err)

    def _emit_update(self):
        """Emit device state update for all entities."""
        self._state = "ON" if self._power else "OFF"

        media_player_id = f"media_player.{self.identifier}"
        media_player_data = {
            MediaAttributes.STATE: MediaStates.ON if self._power else MediaStates.OFF,
            MediaAttributes.VOLUME: self._volume,
            MediaAttributes.MUTED: self._muted,
            MediaAttributes.SOURCE: self._source if self._source else "",
            MediaAttributes.SOURCE_LIST: self._source_list,
        }
        _LOG.debug("%s Emitting media player update: state=%s vol=%d muted=%s src=%s",
                  self.log_id, "ON" if self._power else "OFF",
                  self._volume, self._muted, self._source)
        self.events.emit(DeviceEvents.UPDATE, media_player_id, media_player_data)

        audio_format_id = f"sensor.{self.identifier}.audio_format"
        audio_format_data = {
            SensorAttributes.STATE: SensorStates.ON.value if self._audio_format else SensorStates.UNKNOWN.value,
            SensorAttributes.VALUE: self._audio_format if self._audio_format else "",
        }
        self.events.emit(DeviceEvents.UPDATE, audio_format_id, audio_format_data)

        room_eq_id = f"sensor.{self.identifier}.room_eq"
        room_eq_data = {
            SensorAttributes.STATE: SensorStates.ON.value if self._room_eq else SensorStates.UNKNOWN.value,
            SensorAttributes.VALUE: self._room_eq if self._room_eq else "",
        }
        self.events.emit(DeviceEvents.UPDATE, room_eq_id, room_eq_data)

        sound_mode_sensor_id = f"sensor.{self.identifier}.sound_mode"
        sound_mode_sensor_data = {
            SensorAttributes.STATE: SensorStates.ON.value if self._sound_mode else SensorStates.UNKNOWN.value,
            SensorAttributes.VALUE: self._sound_mode if self._sound_mode else "",
        }
        self.events.emit(DeviceEvents.UPDATE, sound_mode_sensor_id, sound_mode_sensor_data)

        sound_mode_select_id = f"select.{self.identifier}.sound_mode"
        sound_mode_select_data = {
            SelectAttributes.STATE: SelectStates.ON.value if self._power else SelectStates.UNAVAILABLE.value,
            SelectAttributes.CURRENT_OPTION: self._sound_mode if self._sound_mode else "",
            SelectAttributes.OPTIONS: self._sound_mode_list,
        }
        self.events.emit(DeviceEvents.UPDATE, sound_mode_select_id, sound_mode_select_data)

        remote_id = f"remote.{self.identifier}"
        remote_data = {
            RemoteAttributes.STATE: (RemoteStates.ON if self._power else RemoteStates.OFF).value,
        }
        self.events.emit(DeviceEvents.UPDATE, remote_id, remote_data)

    def _format_room_eq(self, index: int) -> str | None:
        """Format room EQ index as a display string, using name if available.

        Returns None if the name is not yet known (waiting for ROOM_EQ_NAMES).
        """
        if index == 0:
            return "Off"
        return self._room_eq_names.get(index)

    def _parse_room_eq_names(self) -> None:
        """Parse room EQ names from state data (0x34 response).

        Response contains up to 3 names of 20 ASCII characters each,
        packed into a single response (20, 40, or 60 bytes total).
        """
        data = self._arcam_state._state.get(CommandCodes.ROOM_EQ_NAMES)
        if not data:
            return
        names: dict[int, str] = {}
        for i in range(min(3, len(data) // 20)):
            chunk = data[i * 20:(i + 1) * 20]
            name = chunk.decode("ascii", errors="replace").rstrip("\x00").strip()
            if name:
                names[i + 1] = name
        if names != self._room_eq_names:
            self._room_eq_names = names
            _LOG.info("%s Room EQ names: %s", self.log_id, names)

    @_tracks_interaction
    async def turn_on(self) -> bool:
        """Turn device on."""
        if not self._arcam_state:
            _LOG.error("%s Turn on failed: state not initialized", self.log_id)
            return False
        try:
            power_state = self._arcam_state.get_power()
            _LOG.info("%s Turning on (API model: %s, current power state: %s)",
                     self.log_id, self._arcam_state._api_model, power_state)
            await self._arcam_state.set_power(True)
            self._power = True
            self._emit_update()
            return True
        except asyncio.TimeoutError:
            _LOG.warning("%s Turn on timeout - setting state optimistically", self.log_id)
            self._power = True
            self._emit_update()
            return True
        except Exception as err:
            _LOG.error("%s Turn on failed: %s (%s)", self.log_id, err, type(err).__name__)
            return False

    @_tracks_interaction
    async def turn_off(self) -> bool:
        """Turn device off."""
        if not self._arcam_state:
            _LOG.error("%s Turn off failed: state not initialized", self.log_id)
            return False
        try:
            _LOG.info("%s Turning off (API model: %s)", self.log_id, self._arcam_state._api_model)
            await self._arcam_state.set_power(False)
            self._power = False
            self._emit_update()
            return True
        except asyncio.TimeoutError:
            _LOG.warning("%s Turn off timeout - setting state optimistically", self.log_id)
            self._power = False
            self._emit_update()
            return True
        except Exception as err:
            _LOG.error("%s Turn off failed: %s (%s)", self.log_id, err, type(err).__name__)
            return False

    @_tracks_interaction
    async def set_volume(self, volume: int) -> bool:
        """Set volume level (0-100)."""
        if not self._arcam_state:
            _LOG.error("%s Set volume failed: state not initialized", self.log_id)
            return False
        try:
            arcam_vol = self._percent_to_arcam_vol(volume)
            _LOG.info("%s Setting volume to %d (%d raw)", self.log_id, volume, arcam_vol)
            await self._arcam_state.set_volume(int(arcam_vol))
            self._volume = volume
            self._emit_update()
            return True
        except asyncio.TimeoutError:
            _LOG.error("%s Set volume failed: timeout", self.log_id)
            return False
        except Exception as err:
            _LOG.error("%s Set volume failed: %s (%s)", self.log_id, err, type(err).__name__)
            return False

    async def volume_up(self) -> bool:
        """Increase volume by one step."""
        new_volume = min(100, self._volume + 1)
        return await self.set_volume(new_volume)

    async def volume_down(self) -> bool:
        """Decrease volume by one step."""
        new_volume = max(0, self._volume - 1)
        return await self.set_volume(new_volume)

    @_tracks_interaction
    async def mute(self, mute: bool) -> bool:
        """Set mute state."""
        if not self._arcam_state:
            _LOG.error("%s Mute failed: state not initialized", self.log_id)
            return False
        try:
            _LOG.info("%s Setting mute to %s", self.log_id, mute)
            await self._arcam_state.set_mute(mute)
            self._muted = mute
            self._emit_update()
            return True
        except asyncio.TimeoutError:
            _LOG.error("%s Mute failed: timeout", self.log_id)
            return False
        except Exception as err:
            _LOG.error("%s Mute failed: %s (%s)", self.log_id, err, type(err).__name__)
            return False

    @_tracks_interaction
    async def select_source(self, source: str) -> bool:
        """Select input source."""
        if not self._arcam_state:
            _LOG.error("%s Select source failed: state not initialized", self.log_id)
            return False
        try:
            _LOG.info("%s Selecting source: %s (API model: %s)",
                     self.log_id, source, self._arcam_state._api_model)
            try:
                source_enum = SourceCodes[source]
            except KeyError:
                _LOG.error("%s Unknown source: %s. Available: %s",
                          self.log_id, source, self._source_list)
                return False
            await self._arcam_state.set_source(source_enum)
            self._source = source
            self._emit_update()
            return True
        except asyncio.TimeoutError:
            _LOG.error("%s Select source failed: timeout", self.log_id)
            return False
        except Exception as err:
            _LOG.error("%s Select source failed: %s (%s)", self.log_id, err, type(err).__name__)
            return False

    def _arcam_vol_to_percent(self, arcam_vol: int) -> int:
        """Convert Arcam volume (0-99) to percentage (0-100)."""
        return min(100, max(0, arcam_vol))

    def _percent_to_arcam_vol(self, percent: int) -> int:
        """Convert percentage (0-100) to Arcam volume (0-99)."""
        return min(99, max(0, percent))

    @_tracks_interaction
    async def send_rc5_command(self, command: str) -> bool:
        """Send RC5 IR simulation command."""
        if not self._client:
            _LOG.error("%s RC5 command failed: client not initialized", self.log_id)
            return False

        if command not in RC5_COMMANDS:
            _LOG.error("%s Unknown RC5 command: %s", self.log_id, command)
            return False

        try:
            sys_code, cmd_code = RC5_COMMANDS[command]
            _LOG.info("%s Sending RC5 command: %s (0x%02X, 0x%02X)",
                     self.log_id, command, sys_code, cmd_code)
            await self._client.send(
                self._device_config.zone,
                CommandCodes.SIMULATE_RC5_IR_COMMAND,
                bytes([sys_code, cmd_code])
            )
            return True
        except asyncio.TimeoutError:
            _LOG.error("%s RC5 command timeout: %s", self.log_id, command)
            return False
        except Exception as err:
            _LOG.error("%s RC5 command failed: %s (%s)", self.log_id, err, type(err).__name__)
            return False

    @_tracks_interaction
    async def set_decode_mode(self, mode: str) -> bool:
        """Set decode/sound mode."""
        if not self._arcam_state:
            _LOG.error("%s Set decode mode failed: state not initialized", self.log_id)
            return False

        try:
            _LOG.info("%s Setting decode mode to: %s", self.log_id, mode)
            await self._arcam_state.set_decode_mode(mode)
            self._sound_mode = mode
            self._emit_update()
            return True
        except asyncio.TimeoutError:
            _LOG.error("%s Set decode mode timeout", self.log_id)
            return False
        except Exception as err:
            _LOG.error("%s Set decode mode failed: %s (%s)", self.log_id, err, type(err).__name__)
            return False
