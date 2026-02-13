"""
Arcam FMJ Media Player entity.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any
from ucapi import StatusCodes
from ucapi.media_player import (
    Attributes, Commands, DeviceClasses, Features,
    MediaPlayer, States,
)
from intg_arcam.config import ArcamConfig
from intg_arcam.device import ArcamDevice

_LOG = logging.getLogger(__name__)


class ArcamMediaPlayer(MediaPlayer):
    """Media player entity for Arcam FMJ."""

    def __init__(self, device_config: ArcamConfig, device: ArcamDevice):
        """Initialize with device reference."""
        self._device = device
        self._device_config = device_config

        entity_id = f"media_player.{device_config.identifier}"

        features = [
            Features.ON_OFF,
            Features.VOLUME,
            Features.VOLUME_UP_DOWN,
            Features.MUTE_TOGGLE,
            Features.UNMUTE,
            Features.MUTE,
            Features.SELECT_SOURCE,
        ]

        attributes = {
            Attributes.STATE: States.UNAVAILABLE,
            Attributes.VOLUME: 0,
            Attributes.MUTED: False,
            Attributes.SOURCE: "",
            Attributes.SOURCE_LIST: [],
        }

        options = {
            "volume_steps": 100
        }

        super().__init__(
            entity_id,
            device_config.name,
            features,
            attributes,
            device_class=DeviceClasses.RECEIVER,
            options=options,
            cmd_handler=self.handle_command,
        )

    async def handle_command(
        self, entity: MediaPlayer, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle commands."""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == Commands.ON:
                success = await self._device.turn_on()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.OFF:
                success = await self._device.turn_off()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.VOLUME:
                if params and "volume" in params:
                    success = await self._device.set_volume(int(params["volume"]))
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.BAD_REQUEST

            elif cmd_id == Commands.VOLUME_UP:
                success = await self._device.volume_up()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.VOLUME_DOWN:
                success = await self._device.volume_down()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.MUTE_TOGGLE:
                success = await self._device.mute(not self._device.muted)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.MUTE:
                success = await self._device.mute(True)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.UNMUTE:
                success = await self._device.mute(False)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            elif cmd_id == Commands.SELECT_SOURCE:
                if params and "source" in params:
                    success = await self._device.select_source(params["source"])
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.BAD_REQUEST

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR
