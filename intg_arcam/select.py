"""
Arcam FMJ Select Entity for Sound Mode selection.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.select import Attributes, Select, States

from intg_arcam.config import ArcamConfig
from intg_arcam.device import ArcamDevice

_LOG = logging.getLogger(__name__)


class ArcamSoundModeSelect(Select):
    """Select entity for sound/decode mode selection."""

    def __init__(self, device_config: ArcamConfig, device: ArcamDevice):
        self._device = device
        self._device_config = device_config

        entity_id = f"select.{device_config.identifier}_sound_mode"
        entity_name = f"{device_config.name} Sound Mode"

        attributes = {
            Attributes.STATE: States.UNAVAILABLE,
            Attributes.CURRENT_OPTION: "",
            Attributes.OPTIONS: [],
        }

        super().__init__(
            entity_id,
            entity_name,
            attributes,
            cmd_handler=self.handle_command,
        )

        _LOG.info("[%s] Sound mode select entity initialized", self.id)
        device.events.on("UPDATE", self._on_device_update)

    async def _on_device_update(self, entity_id: str, update_data: dict[str, Any]) -> None:
        if entity_id == self.id:
            if Attributes.STATE in update_data:
                self.attributes[Attributes.STATE] = update_data[Attributes.STATE]
            if Attributes.CURRENT_OPTION in update_data:
                self.attributes[Attributes.CURRENT_OPTION] = update_data[Attributes.CURRENT_OPTION]
            if Attributes.OPTIONS in update_data:
                self.attributes[Attributes.OPTIONS] = update_data[Attributes.OPTIONS]
            _LOG.debug("[%s] Sound mode select updated: %s", self.id, update_data)

    async def handle_command(
        self, entity: Select, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == "select_option" and params and "option" in params:
                mode_name = params["option"]
                success = await self._device.set_decode_mode(mode_name)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR
