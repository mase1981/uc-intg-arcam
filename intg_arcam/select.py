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
    """Select entity for sound/decode mode selection.

    Note: Sound mode selection is also available via the media player entity's
    SELECT_SOUND_MODE feature. This select entity may be deprecated in a future
    release if it proves redundant.
    """

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

    def _cycle_option(self, offset: int) -> str | None:
        """Return the option at +/- offset from the current, wrapping around.

        Returns None if the options list is empty. If the current mode is
        unknown or not in the list, starts from the first option.
        """
        modes = self._device.sound_mode_list
        if not modes:
            return None
        current = self._device.sound_mode
        if not current or current not in modes:
            return modes[0]
        idx = (modes.index(current) + offset) % len(modes)
        return modes[idx]

    async def handle_command(
        self, entity: SelectEntity, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == Commands.SELECT_OPTION and params and "option" in params:
                mode_name = params["option"]
                success = await self._device.set_decode_mode(mode_name)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id in (Commands.SELECT_NEXT, Commands.SELECT_PREVIOUS):
                offset = 1 if cmd_id == Commands.SELECT_NEXT else -1
                target = self._cycle_option(offset)
                if target is None:
                    _LOG.warning("[%s] Cannot cycle: current=%r, modes=%r",
                                self.id, self._device.sound_mode, self._device.sound_mode_list)
                    return StatusCodes.BAD_REQUEST
                success = await self._device.set_decode_mode(target)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            return StatusCodes.NOT_IMPLEMENTED

        except Exception as err:
            _LOG.error("[%s] Command error: %s", self.id, err)
            return StatusCodes.SERVER_ERROR
