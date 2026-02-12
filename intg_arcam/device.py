"""
Arcam FMJ device implementation for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any
from arcam.fmj import CommandCodes, SourceCodes
from ucapi.media_player import Attributes as MediaAttributes, States as MediaStates
from ucapi.sensor import Attributes as SensorAttributes, States as SensorStates
from ucapi.select import Attributes as SelectAttributes, States as SelectStates
from ucapi_framework import ExternalClientDevice, DeviceEvents
from intg_arcam.config import ArcamConfig

_LOG = logging.getLogger(__name__)

RC5_COMMANDS = {
    "CURSOR_UP": (0x10, 0x50),
    "CURSOR_DOWN": (0x10, 0x51),
    "CURSOR_LEFT": (0x10, 0x55),
    "CURSOR_RIGHT": (0x10, 0x56),
    "OK": (0x10, 0x57),
    "MENU": (0x10, 0x52),
    "BACK": (0x10, 0x53),
    "INFO": (0x10, 0x0F),
    "DISPLAY": (0x10, 0x4D),
    "MODE": (0x10, 0x43),
    "DIRECT": (0x10, 0x63),
    "TUNER_BAND": (0x10, 0x44),
    "PRESET_UP": (0x10, 0x5E),
    "PRESET_DOWN": (0x10, 0x5F),
    "INPUT_CD": (0x10, 0x35),
    "INPUT_BD": (0x10, 0x36),
    "INPUT_AV": (0x10, 0x37),
    "INPUT_SAT": (0x10, 0x38),
    "INPUT_PVR": (0x10, 0x39),
    "INPUT_VCR": (0x10, 0x3A),
    "INPUT_AUX": (0x10, 0x3B),
    "INPUT_FM": (0x10, 0x3C),
    "INPUT_DAB": (0x10, 0x3D),
    "INPUT_NET": (0x10, 0x3E),
    "INPUT_USB": (0x10, 0x3F),
    "INPUT_STB": (0x10, 0x7C),
    "INPUT_GAME": (0x10, 0x7D),
    "STEREO": (0x10, 0x30),
    "DOLBY_PLII_MOVIE": (0x10, 0x45),
    "DOLBY_PLII_MUSIC": (0x10, 0x46),
    "DTS_NEO6_CINEMA": (0x10, 0x47),
    "DTS_NEO6_MUSIC": (0x10, 0x48),
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
        self._state = None
        self._process_task: asyncio.Task | None = None
        self._maintain_task: asyncio.Task | None = None

        self._power = False
        self._volume = 0
        self._muted = False
        self._source = None
        self._source_list = []
        self._sound_mode = None
        self._sound_mode_list = []
        self._audio_format = None

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

    async def create_client(self) -> Any:
        """Create the Arcam client (required by ExternalClientDevice)."""
        from arcam.fmj.client import Client
        from arcam.fmj.state import State

        self._client = Client(self._device_config.host, self._device_config.port)
        self._state = State(self._client, self._device_config.zone)
        return self._client

    async def connect_client(self) -> None:
        """Connect the Arcam client (required by ExternalClientDevice)."""
        _LOG.info("%s Starting Arcam client", self.log_id)
        await self._client.start()

        _LOG.info("%s Registering state listener", self.log_id)
        await self._state.start()

        _LOG.info("%s Starting response processor with data listener", self.log_id)
        self._process_task = asyncio.create_task(self._run_process_loop_with_listener())

        await asyncio.sleep(0.5)

        _LOG.info("%s Querying device state", self.log_id)
        try:
            await self._state.update()
            _LOG.info("%s Detected model: %s (API: %s)",
                     self.log_id, self._state.model, self._state._api_model)
        except Exception as err:
            _LOG.warning("%s State query failed: %s, using defaults", self.log_id, err)

        await self._initialize_state()
        self._maintain_task = asyncio.create_task(self._maintain_connection_loop())

    async def disconnect_client(self) -> None:
        """Disconnect the Arcam client (required by ExternalClientDevice)."""
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

        if self._client:
            _LOG.info("%s Closing client connection", self.log_id)
            try:
                await self._client.stop()
            except Exception as err:
                _LOG.debug("%s Error during client stop: %s", self.log_id, err)
            finally:
                self._client = None
                self._state = None

    def check_client_connected(self) -> bool:
        """Check if the Arcam client is connected (required by ExternalClientDevice)."""
        if not self._client or not self._state:
            return False
        return self._client.connected

    async def maintain_connection(self) -> None:
        """Required by ExternalClientDevice but we use our own background task."""
        pass

    def _on_data_received(self, packet) -> None:
        """Callback when data is received from device."""
        _LOG.debug("%s Data received from device", self.log_id)
        asyncio.create_task(self._handle_state_update())

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
        """Background task for periodic state refresh."""
        _LOG.info("%s Starting periodic state refresh loop", self.log_id)

        try:
            while True:
                await asyncio.sleep(30)  # Refresh every 30 seconds
                if self._state and self._client and self._client.connected:
                    try:
                        await self._state.update()
                        await self._handle_state_update()
                    except asyncio.TimeoutError:
                        _LOG.warning("%s State refresh timed out", self.log_id)
                    except Exception as err:
                        _LOG.debug("%s Error during state refresh: %s (%s)",
                                  self.log_id, err, type(err).__name__)

        except asyncio.CancelledError:
            _LOG.debug("%s State refresh loop cancelled", self.log_id)
            raise
        except Exception as err:
            _LOG.error("%s Error in state refresh loop: %s (%s)",
                      self.log_id, err, type(err).__name__)

    async def _initialize_state(self) -> None:
        """Initialize local state from device state."""
        if not self._state:
            return

        try:
            power = self._state.get_power()
            self._power = power if power is not None else False

            raw_volume = self._state.get_volume()
            if raw_volume is not None:
                self._volume = self._arcam_vol_to_percent(raw_volume)
            else:
                self._volume = 0

            muted = self._state.get_mute()
            self._muted = muted if muted is not None else False

            source = self._state.get_source()
            if source is not None:
                self._source = source.name if hasattr(source, "name") else str(source)
            else:
                self._source = None

            source_list = self._state.get_source_list()
            if source_list:
                self._source_list = [src.name if hasattr(src, "name") else str(src) for src in source_list]
            else:
                self._source_list = []

            if hasattr(self._state, "get_decode_mode"):
                decode_mode = self._state.get_decode_mode()
                if decode_mode is not None:
                    self._sound_mode = decode_mode.name if hasattr(decode_mode, "name") else str(decode_mode)

            if hasattr(self._state, "get_decode_modes"):
                decode_modes = self._state.get_decode_modes()
                if decode_modes:
                    self._sound_mode_list = [m.name if hasattr(m, "name") else str(m) for m in decode_modes]

            if hasattr(self._state, "get_incoming_audio_format"):
                audio_fmt = self._state.get_incoming_audio_format()
                if audio_fmt and isinstance(audio_fmt, tuple) and len(audio_fmt) >= 2:
                    fmt, config = audio_fmt
                    if fmt is not None:
                        fmt_name = fmt.name if hasattr(fmt, "name") else str(fmt)
                        self._audio_format = fmt_name

            _LOG.info("%s Initial state: Power=%s Volume=%d Muted=%s Source=%s Sources=%s",
                     self.log_id, self._power, self._volume, self._muted, self._source,
                     self._source_list[:5] if self._source_list else [])

            self._emit_update()

        except Exception as err:
            _LOG.warning("%s Failed to initialize state: %s (%s)",
                        self.log_id, err, type(err).__name__)

    async def _handle_state_update(self) -> None:
        """Handle state update from Arcam client."""
        if not self._state:
            return

        try:
            changed = False

            if hasattr(self._state, "get_power"):
                power = self._state.get_power()
                if power is not None and power != self._power:
                    self._power = power
                    changed = True

            if hasattr(self._state, "get_volume"):
                raw_volume = self._state.get_volume()
                if raw_volume is not None:
                    volume = self._arcam_vol_to_percent(raw_volume)
                    if volume != self._volume:
                        self._volume = volume
                        changed = True

            if hasattr(self._state, "get_mute"):
                muted = self._state.get_mute()
                if muted is not None and muted != self._muted:
                    self._muted = muted
                    changed = True

            if hasattr(self._state, "get_source"):
                source = self._state.get_source()
                source_name = source.name if hasattr(source, "name") else str(source) if source else None
                if source_name is not None and source_name != self._source:
                    self._source = source_name
                    changed = True

            if hasattr(self._state, "get_decode_mode"):
                decode_mode = self._state.get_decode_mode()
                if decode_mode is not None:
                    mode_name = decode_mode.name if hasattr(decode_mode, "name") else str(decode_mode)
                    if mode_name != self._sound_mode:
                        self._sound_mode = mode_name
                        changed = True

            if hasattr(self._state, "get_decode_modes"):
                decode_modes = self._state.get_decode_modes()
                if decode_modes:
                    modes = [m.name if hasattr(m, "name") else str(m) for m in decode_modes]
                    if modes != self._sound_mode_list:
                        self._sound_mode_list = modes

            if hasattr(self._state, "get_incoming_audio_format"):
                audio_fmt = self._state.get_incoming_audio_format()
                if audio_fmt and isinstance(audio_fmt, tuple) and len(audio_fmt) >= 2:
                    fmt, config = audio_fmt
                    if fmt is not None:
                        fmt_name = fmt.name if hasattr(fmt, "name") else str(fmt)
                        if fmt_name != self._audio_format:
                            self._audio_format = fmt_name
                            changed = True

            if changed:
                _LOG.debug("%s State updated: Power=%s Volume=%d Muted=%s Source=%s",
                          self.log_id, self._power, self._volume, self._muted, self._source)
                self._emit_update()

        except Exception as err:
            _LOG.debug("%s Error handling state update: %s", self.log_id, err)

    def _emit_update(self):
        """Emit device state update for all entities."""
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

        audio_format_id = f"sensor.{self.identifier}_audio_format"
        audio_format_data = {
            SensorAttributes.STATE: SensorStates.ON if self._power else SensorStates.UNAVAILABLE,
            SensorAttributes.VALUE: self._audio_format if self._audio_format else "Unknown",
        }
        self.events.emit(DeviceEvents.UPDATE, audio_format_id, audio_format_data)

        sound_mode_sensor_id = f"sensor.{self.identifier}_sound_mode"
        sound_mode_sensor_data = {
            SensorAttributes.STATE: SensorStates.ON if self._power else SensorStates.UNAVAILABLE,
            SensorAttributes.VALUE: self._sound_mode if self._sound_mode else "Unknown",
        }
        self.events.emit(DeviceEvents.UPDATE, sound_mode_sensor_id, sound_mode_sensor_data)

        sound_mode_select_id = f"select.{self.identifier}_sound_mode"
        sound_mode_select_data = {
            SelectAttributes.STATE: SelectStates.ON if self._power else SelectStates.UNAVAILABLE,
            SelectAttributes.CURRENT_OPTION: self._sound_mode if self._sound_mode else "",
            SelectAttributes.OPTIONS: self._sound_mode_list,
        }
        self.events.emit(DeviceEvents.UPDATE, sound_mode_select_id, sound_mode_select_data)

    async def turn_on(self) -> bool:
        """Turn device on."""
        if not self._state:
            _LOG.error("%s Turn on failed: state not initialized", self.log_id)
            return False
        try:
            power_state = self._state.get_power()
            _LOG.info("%s Turning on (API model: %s, current power state: %s)",
                     self.log_id, self._state._api_model, power_state)
            await self._state.set_power(True)
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

    async def turn_off(self) -> bool:
        """Turn device off."""
        if not self._state:
            _LOG.error("%s Turn off failed: state not initialized", self.log_id)
            return False
        try:
            _LOG.info("%s Turning off (API model: %s)", self.log_id, self._state._api_model)
            await self._state.set_power(False)
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

    async def set_volume(self, volume: int) -> bool:
        """Set volume level (0-100)."""
        if not self._state:
            _LOG.error("%s Set volume failed: state not initialized", self.log_id)
            return False
        try:
            arcam_vol = self._percent_to_arcam_vol(volume)
            _LOG.info("%s Setting volume to %d (%d raw)", self.log_id, volume, arcam_vol)
            await self._state.set_volume(int(arcam_vol))
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

    async def mute(self, mute: bool) -> bool:
        """Set mute state."""
        if not self._state:
            _LOG.error("%s Mute failed: state not initialized", self.log_id)
            return False
        try:
            _LOG.info("%s Setting mute to %s", self.log_id, mute)
            await self._state.set_mute(mute)
            self._muted = mute
            self._emit_update()
            return True
        except asyncio.TimeoutError:
            _LOG.error("%s Mute failed: timeout", self.log_id)
            return False
        except Exception as err:
            _LOG.error("%s Mute failed: %s (%s)", self.log_id, err, type(err).__name__)
            return False

    async def select_source(self, source: str) -> bool:
        """Select input source."""
        if not self._state:
            _LOG.error("%s Select source failed: state not initialized", self.log_id)
            return False
        try:
            _LOG.info("%s Selecting source: %s (API model: %s)",
                     self.log_id, source, self._state._api_model)
            try:
                source_enum = SourceCodes[source]
            except KeyError:
                _LOG.error("%s Unknown source: %s. Available: %s",
                          self.log_id, source, self._source_list)
                return False
            await self._state.set_source(source_enum)
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

    async def set_decode_mode(self, mode: str) -> bool:
        """Set decode/sound mode."""
        if not self._state:
            _LOG.error("%s Set decode mode failed: state not initialized", self.log_id)
            return False

        try:
            _LOG.info("%s Setting decode mode to: %s", self.log_id, mode)
            await self._state.set_decode_mode(mode)
            self._sound_mode = mode
            self._emit_update()
            return True
        except asyncio.TimeoutError:
            _LOG.error("%s Set decode mode timeout", self.log_id)
            return False
        except Exception as err:
            _LOG.error("%s Set decode mode failed: %s (%s)", self.log_id, err, type(err).__name__)
            return False
