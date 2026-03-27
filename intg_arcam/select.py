"""
Arcam FMJ Select Entity for Sound Mode selection.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.select import Attributes, Commands, States
from ucapi_framework import SelectEntity

from intg_arcam.config import ArcamConfig
from intg_arcam.device import ArcamDevice

_LOG = logging.getLogger(__name__)


class ArcamSoundModeSelect(SelectEntity):
    """Select entity for sound/decode mode selection."""

    def __init__(self, device_config: ArcamConfig, device: ArcamDevice):
        self._device = device
        self._device_config = device_config

        entity_id = f"select.{device_config.identifier}.sound_mode"
        entity_name = f"{device_config.name} Sound Mode"

        attributes = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.CURRENT_OPTION: "",
            Attributes.OPTIONS: [],
        }

        super().__init__(
            entity_id,
            entity_name,
            attributes,
            cmd_handler=self.handle_command,
        )
        self.subscribe_to_device(device)

        _LOG.info("[%s] Sound mode select entity initialized", self.id)

    async def sync_state(self):
        self.update({
            Attributes.STATE: States.ON if self._device.power else States.UNAVAILABLE,
            Attributes.CURRENT_OPTION: self._device.sound_mode or "",
            Attributes.OPTIONS: self._device.sound_mode_list,
        })

    async def handle_command(
        self, entity: SelectEntity, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == Commands.SELECT_OPTION and params and "option" in params:
                mode_name = params["option"]
                success = await self._device.set_decode_mode(mode_name)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR
