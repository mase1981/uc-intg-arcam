"""
Arcam FMJ Remote Entity.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.remote import Attributes, Commands, Features, States
from ucapi_framework import RemoteEntity

from intg_arcam.config import ArcamConfig
from intg_arcam.device import ArcamDevice, RC5_COMMANDS

_LOG = logging.getLogger(__name__)


class ArcamRemote(RemoteEntity):
    """Remote entity for Arcam FMJ advanced control."""

    def __init__(self, device_config: ArcamConfig, device: ArcamDevice):
        self._device = device
        self._device_config = device_config

        entity_id = f"remote.{device_config.identifier}"
        entity_name = f"{device_config.name} Remote"

        features = [Features.ON_OFF, Features.SEND_CMD]
        attributes = {
            Attributes.STATE: States.UNKNOWN,
        }

        simple_commands = [
            "CURSOR_UP",
            "CURSOR_DOWN",
            "CURSOR_LEFT",
            "CURSOR_RIGHT",
            "OK",
            "MENU",
            "BACK",
            "INFO",
            "DISPLAY",
            "MODE",
            "DIRECT",
            "TUNER_BAND",
            "PRESET_UP",
            "PRESET_DOWN",
            "INPUT_CD",
            "INPUT_BD",
            "INPUT_AV",
            "INPUT_SAT",
            "INPUT_PVR",
            "INPUT_VCR",
            "INPUT_AUX",
            "INPUT_FM",
            "INPUT_DAB",
            "INPUT_NET",
            "INPUT_USB",
            "INPUT_STB",
            "INPUT_UHD",
            "INPUT_BT",
            "INPUT_GAME",
            "STEREO",
            "DOLBY_PLII_MOVIE",
            "DOLBY_PLII_MUSIC",
            "DTS_NEO6_CINEMA",
            "DTS_NEO6_MUSIC",
        ]

        user_interface = {
            "pages": [
                {
                    "page_id": "navigation",
                    "name": "Navigation",
                    "grid": {"width": 4, "height": 6},
                    "items": [
                        {
                            "type": "text",
                            "text": "Menu",
                            "command": {"cmd_id": "MENU"},
                            "location": {"x": 0, "y": 0},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "Info",
                            "command": {"cmd_id": "INFO"},
                            "location": {"x": 2, "y": 0},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "icon",
                            "icon": "uc:up-arrow",
                            "command": {"cmd_id": "CURSOR_UP"},
                            "location": {"x": 1, "y": 1},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "icon",
                            "icon": "uc:left-arrow",
                            "command": {"cmd_id": "CURSOR_LEFT"},
                            "location": {"x": 0, "y": 2},
                        },
                        {
                            "type": "text",
                            "text": "OK",
                            "command": {"cmd_id": "OK"},
                            "location": {"x": 1, "y": 2},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "icon",
                            "icon": "uc:right-arrow",
                            "command": {"cmd_id": "CURSOR_RIGHT"},
                            "location": {"x": 3, "y": 2},
                        },
                        {
                            "type": "icon",
                            "icon": "uc:down-arrow",
                            "command": {"cmd_id": "CURSOR_DOWN"},
                            "location": {"x": 1, "y": 3},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "Back",
                            "command": {"cmd_id": "BACK"},
                            "location": {"x": 0, "y": 4},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "Display",
                            "command": {"cmd_id": "DISPLAY"},
                            "location": {"x": 2, "y": 4},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "Mode",
                            "command": {"cmd_id": "MODE"},
                            "location": {"x": 0, "y": 5},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "Direct",
                            "command": {"cmd_id": "DIRECT"},
                            "location": {"x": 2, "y": 5},
                            "size": {"width": 2, "height": 1},
                        },
                    ],
                },
                {
                    "page_id": "audio_modes",
                    "name": "Audio Modes",
                    "grid": {"width": 4, "height": 6},
                    "items": [
                        {
                            "type": "text",
                            "text": "Stereo",
                            "command": {"cmd_id": "STEREO"},
                            "location": {"x": 0, "y": 0},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "Direct",
                            "command": {"cmd_id": "DIRECT"},
                            "location": {"x": 2, "y": 0},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "Dolby\nPLII Movie",
                            "command": {"cmd_id": "DOLBY_PLII_MOVIE"},
                            "location": {"x": 0, "y": 1},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "Dolby\nPLII Music",
                            "command": {"cmd_id": "DOLBY_PLII_MUSIC"},
                            "location": {"x": 2, "y": 1},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "DTS Neo:6\nCinema",
                            "command": {"cmd_id": "DTS_NEO6_CINEMA"},
                            "location": {"x": 0, "y": 2},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "DTS Neo:6\nMusic",
                            "command": {"cmd_id": "DTS_NEO6_MUSIC"},
                            "location": {"x": 2, "y": 2},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "Mode",
                            "command": {"cmd_id": "MODE"},
                            "location": {"x": 0, "y": 3},
                            "size": {"width": 4, "height": 1},
                        },
                    ],
                },
                {
                    "page_id": "sources",
                    "name": "Sources",
                    "grid": {"width": 4, "height": 6},
                    "items": [
                        {
                            "type": "text",
                            "text": "BD",
                            "command": {"cmd_id": "INPUT_BD"},
                            "location": {"x": 0, "y": 0},
                        },
                        {
                            "type": "text",
                            "text": "SAT",
                            "command": {"cmd_id": "INPUT_SAT"},
                            "location": {"x": 1, "y": 0},
                        },
                        {
                            "type": "text",
                            "text": "AV",
                            "command": {"cmd_id": "INPUT_AV"},
                            "location": {"x": 2, "y": 0},
                        },
                        {
                            "type": "text",
                            "text": "GAME",
                            "command": {"cmd_id": "INPUT_GAME"},
                            "location": {"x": 3, "y": 0},
                        },
                        {
                            "type": "text",
                            "text": "STB",
                            "command": {"cmd_id": "INPUT_STB"},
                            "location": {"x": 0, "y": 1},
                        },
                        {
                            "type": "text",
                            "text": "PVR",
                            "command": {"cmd_id": "INPUT_PVR"},
                            "location": {"x": 1, "y": 1},
                        },
                        {
                            "type": "text",
                            "text": "VCR",
                            "command": {"cmd_id": "INPUT_VCR"},
                            "location": {"x": 2, "y": 1},
                        },
                        {
                            "type": "text",
                            "text": "AUX",
                            "command": {"cmd_id": "INPUT_AUX"},
                            "location": {"x": 3, "y": 1},
                        },
                        {
                            "type": "text",
                            "text": "CD",
                            "command": {"cmd_id": "INPUT_CD"},
                            "location": {"x": 0, "y": 2},
                        },
                        {
                            "type": "text",
                            "text": "NET",
                            "command": {"cmd_id": "INPUT_NET"},
                            "location": {"x": 1, "y": 2},
                        },
                        {
                            "type": "text",
                            "text": "USB",
                            "command": {"cmd_id": "INPUT_USB"},
                            "location": {"x": 2, "y": 2},
                        },
                        {
                            "type": "text",
                            "text": "UHD",
                            "command": {"cmd_id": "INPUT_UHD"},
                            "location": {"x": 3, "y": 2},
                        },
                        {
                            "type": "text",
                            "text": "FM",
                            "command": {"cmd_id": "INPUT_FM"},
                            "location": {"x": 0, "y": 3},
                        },
                        {
                            "type": "text",
                            "text": "DAB",
                            "command": {"cmd_id": "INPUT_DAB"},
                            "location": {"x": 1, "y": 3},
                        },
                        {
                            "type": "text",
                            "text": "BT",
                            "command": {"cmd_id": "INPUT_BT"},
                            "location": {"x": 2, "y": 3},
                        },
                    ],
                },
                {
                    "page_id": "tuner",
                    "name": "Tuner",
                    "grid": {"width": 4, "height": 6},
                    "items": [
                        {
                            "type": "text",
                            "text": "FM",
                            "command": {"cmd_id": "INPUT_FM"},
                            "location": {"x": 0, "y": 0},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "DAB",
                            "command": {"cmd_id": "INPUT_DAB"},
                            "location": {"x": 2, "y": 0},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "Band",
                            "command": {"cmd_id": "TUNER_BAND"},
                            "location": {"x": 0, "y": 1},
                            "size": {"width": 4, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "Preset",
                            "location": {"x": 0, "y": 2},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "icon",
                            "icon": "uc:up-arrow",
                            "command": {"cmd_id": "PRESET_UP"},
                            "location": {"x": 2, "y": 2},
                        },
                        {
                            "type": "icon",
                            "icon": "uc:down-arrow",
                            "command": {"cmd_id": "PRESET_DOWN"},
                            "location": {"x": 3, "y": 2},
                        },
                    ],
                },
            ]
        }

        super().__init__(
            entity_id,
            entity_name,
            features,
            attributes,
            simple_commands=simple_commands,
            ui_pages=user_interface["pages"],
            cmd_handler=self.handle_command,
        )
        self.subscribe_to_device(device)

        _LOG.info("[%s] Remote entity initialized with %d commands", entity_id, len(simple_commands))

    async def sync_state(self):
        self.update({
            Attributes.STATE: States.ON if self._device.power else States.OFF,
        })

    async def handle_command(
        self, entity: RemoteEntity, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            if cmd_id == Commands.ON:
                success = await self._device.turn_on()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id == Commands.OFF:
                success = await self._device.turn_off()
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR

            if cmd_id != Commands.SEND_CMD:
                _LOG.warning("[%s] Unsupported command type: %s", self.id, cmd_id)
                return StatusCodes.NOT_FOUND

            if not params or "command" not in params:
                _LOG.error("[%s] Missing command parameter", self.id)
                return StatusCodes.BAD_REQUEST

            command = params["command"]

            if command not in RC5_COMMANDS:
                _LOG.warning("[%s] Unknown command: %s", self.id, command)
                return StatusCodes.NOT_FOUND

            success = await self._device.send_rc5_command(command)

            if not success:
                _LOG.error("[%s] Command failed to send", self.id)
                return StatusCodes.SERVER_ERROR

            return StatusCodes.OK

        except Exception as err:
            _LOG.error("[%s] Error executing command %s: %s", self.id, cmd_id, err)
            return StatusCodes.SERVER_ERROR
