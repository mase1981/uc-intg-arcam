"""
Arcam FMJ device implementation for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any
from ucapi_framework import ExternalClientDevice, DeviceEvents
from intg_arcam.config import ArcamConfig

_LOG = logging.getLogger(__name__)


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

        self._power = False
        self._volume = 0
        self._muted = False
        self._source = None
        self._source_list = []

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

        _LOG.info("%s Client started, initializing state", self.log_id)
        await self._initialize_state()

    async def disconnect_client(self) -> None:
        """Disconnect the Arcam client (required by ExternalClientDevice)."""
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
        return True

    async def maintain_connection(self) -> None:
        """Monitor connection and update state."""
        if not self._state:
            return

        update_task = None
        try:
            _LOG.info("%s Starting state monitoring loop", self.log_id)

            def state_update_callback():
                """Callback when state updates."""
                asyncio.create_task(self._handle_state_update())

            self._state.register_callback(state_update_callback)

            update_task = asyncio.create_task(self._state.update())

            await asyncio.Future()

        except asyncio.CancelledError:
            _LOG.debug("%s Connection monitoring cancelled", self.log_id)
            if update_task and not update_task.done():
                update_task.cancel()
                try:
                    await update_task
                except asyncio.CancelledError:
                    pass
            raise
        except Exception as err:
            _LOG.error("%s Error in connection monitoring: %s", self.log_id, err)
            raise
        finally:
            _LOG.debug("%s Exiting connection monitoring", self.log_id)

    async def _initialize_state(self) -> None:
        """Initialize device state after connection."""
        if not self._state:
            return

        try:
            await asyncio.sleep(0.5)

            if hasattr(self._state, "get_power"):
                self._power = await self._state.get_power() or False

            if hasattr(self._state, "get_volume"):
                raw_volume = await self._state.get_volume()
                if raw_volume is not None:
                    self._volume = self._arcam_vol_to_percent(raw_volume)

            if hasattr(self._state, "get_mute"):
                self._muted = await self._state.get_mute() or False

            if hasattr(self._state, "get_source"):
                self._source = await self._state.get_source()

            if hasattr(self._state, "get_source_list"):
                source_list = await self._state.get_source_list()
                if source_list:
                    self._source_list = [src.decode() if isinstance(src, bytes) else str(src) for src in source_list]

            _LOG.info("%s Initial state: Power=%s Volume=%d Muted=%s Source=%s",
                     self.log_id, self._power, self._volume, self._muted, self._source)

            self._emit_update()

        except Exception as err:
            _LOG.warning("%s Failed to initialize state: %s", self.log_id, err)

    async def _handle_state_update(self) -> None:
        """Handle state update from Arcam client."""
        if not self._state:
            return

        try:
            changed = False

            if hasattr(self._state, "get_power"):
                power = await self._state.get_power()
                if power is not None and power != self._power:
                    self._power = power
                    changed = True

            if hasattr(self._state, "get_volume"):
                raw_volume = await self._state.get_volume()
                if raw_volume is not None:
                    volume = self._arcam_vol_to_percent(raw_volume)
                    if volume != self._volume:
                        self._volume = volume
                        changed = True

            if hasattr(self._state, "get_mute"):
                muted = await self._state.get_mute()
                if muted is not None and muted != self._muted:
                    self._muted = muted
                    changed = True

            if hasattr(self._state, "get_source"):
                source = await self._state.get_source()
                if source is not None and source != self._source:
                    self._source = source
                    changed = True

            if changed:
                _LOG.debug("%s State updated: Power=%s Volume=%d Muted=%s Source=%s",
                          self.log_id, self._power, self._volume, self._muted, self._source)
                self._emit_update()

        except Exception as err:
            _LOG.debug("%s Error handling state update: %s", self.log_id, err)

    def _emit_update(self):
        """Emit device state update."""
        update_data = {
            "state": "ON" if self._power else "OFF",
            "volume": self._volume,
            "muted": self._muted,
            "source": self._source,
        }
        _LOG.debug("%s Emitting update: %s", self.log_id, update_data)
        self.events.emit(
            DeviceEvents.UPDATE,
            self.identifier,
            update_data
        )

    async def turn_on(self) -> bool:
        """Turn device on."""
        if not self._state:
            return False
        try:
            _LOG.info("%s Turning on", self.log_id)
            if hasattr(self._state, "set_power"):
                await self._state.set_power(True)
                self._power = True
                self._emit_update()
                return True
            return False
        except Exception as err:
            _LOG.error("%s Turn on failed: %s", self.log_id, err)
            return False

    async def turn_off(self) -> bool:
        """Turn device off."""
        if not self._state:
            return False
        try:
            _LOG.info("%s Turning off", self.log_id)
            if hasattr(self._state, "set_power"):
                await self._state.set_power(False)
                self._power = False
                self._emit_update()
                return True
            return False
        except Exception as err:
            _LOG.error("%s Turn off failed: %s", self.log_id, err)
            return False

    async def set_volume(self, volume: int) -> bool:
        """Set volume level (0-100)."""
        if not self._state:
            return False
        try:
            arcam_vol = self._percent_to_arcam_vol(volume)
            _LOG.info("%s Setting volume to %d (%d raw)", self.log_id, volume, arcam_vol)
            if hasattr(self._state, "set_volume"):
                await self._state.set_volume(arcam_vol)
                self._volume = volume
                self._emit_update()
                return True
            return False
        except Exception as err:
            _LOG.error("%s Set volume failed: %s", self.log_id, err)
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
            return False
        try:
            _LOG.info("%s Setting mute to %s", self.log_id, mute)
            if hasattr(self._state, "set_mute"):
                await self._state.set_mute(mute)
                self._muted = mute
                self._emit_update()
                return True
            return False
        except Exception as err:
            _LOG.error("%s Mute failed: %s", self.log_id, err)
            return False

    async def select_source(self, source: str) -> bool:
        """Select input source."""
        if not self._state:
            return False
        try:
            _LOG.info("%s Selecting source: %s", self.log_id, source)
            if hasattr(self._state, "set_source"):
                await self._state.set_source(source)
                self._source = source
                self._emit_update()
                return True
            return False
        except Exception as err:
            _LOG.error("%s Select source failed: %s", self.log_id, err)
            return False

    def _arcam_vol_to_percent(self, arcam_vol: float) -> int:
        """Convert Arcam volume (-90.0 to 10.0 dB) to percentage (0-100)."""
        min_db = -90.0
        max_db = 10.0
        clamped = max(min_db, min(max_db, arcam_vol))
        return int(((clamped - min_db) / (max_db - min_db)) * 100)

    def _percent_to_arcam_vol(self, percent: int) -> float:
        """Convert percentage (0-100) to Arcam volume (-90.0 to 10.0 dB)."""
        min_db = -90.0
        max_db = 10.0
        return (percent / 100.0) * (max_db - min_db) + min_db
