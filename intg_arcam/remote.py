"""
Arcam FMJ Remote Entity.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from arcam.fmj import ApiModel
from ucapi import StatusCodes
from ucapi.remote import Attributes, Commands, Features, States
from ucapi.ui import Buttons, EntityCommand, create_btn_mapping
from ucapi_framework import RemoteEntity

from intg_arcam.config import ArcamConfig
from intg_arcam.device import ArcamDevice, RC5_COMMANDS

_LOG = logging.getLogger(__name__)

# Audio mode buttons per model series.
# Each entry is (display_label, cmd_id). The cmd_id must exist in RC5_COMMANDS.
# "Direct" and "Mode" are common to all models and added automatically by the
# page builder.
_AUDIO_MODES_450 = [
    ("Stereo", "STEREO"),
    ("Dolby\nPLII Movie", "DOLBY_PLII_MOVIE"),
    ("Dolby\nPLII Music", "DOLBY_PLII_MUSIC"),
    ("Dolby\nPLII Game", "DOLBY_PLII_GAME"),
    ("Dolby PL", "DOLBY_PL"),
    ("DTS Neo:6\nCinema", "DTS_NEO6_CINEMA"),
    ("DTS Neo:6\nMusic", "DTS_NEO6_MUSIC"),
    ("MCH Stereo", "MCH_STEREO"),
]

_AUDIO_MODES_860 = [
    ("Stereo", "STEREO"),
    ("Dolby PL", "DOLBY_PL"),
    ("DTS\nNeural:X", "DTS_NEURAL_X"),
    ("DTS\nVirtual:X", "DTS_VIRTUAL_X"),
    ("DTS Neo:6\nCinema", "DTS_NEO6_CINEMA"),
    ("DTS Neo:6\nMusic", "DTS_NEO6_MUSIC"),
    ("MCH Stereo", "MCH_STEREO"),
]

_AUDIO_MODES_HDA = [
    ("Stereo", "STEREO"),
    ("Dolby\nSurround", "DOLBY_SURROUND"),
    ("DTS\nNeural:X", "DTS_NEURAL_X"),
    ("DTS Neo:6\nCinema", "DTS_NEO6_CINEMA"),
    ("DTS Neo:6\nMusic", "DTS_NEO6_MUSIC"),
    ("MCH Stereo", "MCH_STEREO"),
    ("Dolby\nVirt. Height", "DOLBY_VIRTUAL_HEIGHT"),
    ("Auro\nNative", "AURO_NATIVE"),
    ("Auro-Matic\n3D", "AURO_MATIC_3D"),
    ("Auro-2D", "AURO_2D"),
]

# SA/PA/ST series have no audio decode modes (stereo amps, power amps, streamers).
_AUDIO_MODES_SA: list[tuple[str, str]] = []
_AUDIO_MODES_PA: list[tuple[str, str]] = []
_AUDIO_MODES_ST: list[tuple[str, str]] = []

_AUDIO_MODES_BY_MODEL = {
    ApiModel.API450_SERIES: _AUDIO_MODES_450,
    ApiModel.API860_SERIES: _AUDIO_MODES_860,
    ApiModel.APIHDA_SERIES: _AUDIO_MODES_HDA,
    ApiModel.APISA_SERIES: _AUDIO_MODES_SA,
    ApiModel.APIPA_SERIES: _AUDIO_MODES_PA,
    ApiModel.APIST_SERIES: _AUDIO_MODES_ST,
}

# Input source buttons per model series.
# Each entry is (display_label, cmd_id). Ordered to match the physical remote's
# 4×3 grid layout, read left-to-right, top-to-bottom.
_INPUT_SOURCES_450 = [
    ("TUN", "INPUT_RADIO"), ("AUX", "INPUT_AUX"), ("NET", "INPUT_NET"), ("USB", "INPUT_USB"),
    ("BD", "INPUT_BD"),     ("AV", "INPUT_AV"),   ("VCR", "INPUT_VCR"), ("GAME", "INPUT_GAME"),
    ("STB", "INPUT_STB"),   ("SAT", "INPUT_SAT"), ("PVR", "INPUT_PVR"), ("CD", "INPUT_CD"),
]

_INPUT_SOURCES_860 = [
    ("Radio", "INPUT_RADIO"), ("AUX", "INPUT_AUX"), ("NET", "INPUT_NET"), ("USB", "INPUT_USB"),
    ("AV", "INPUT_AV"),      ("SAT", "INPUT_SAT"), ("PVR", "INPUT_PVR"), ("GAME", "INPUT_GAME"),
    ("BD", "INPUT_BD"),      ("CD", "INPUT_CD"),   ("STB", "INPUT_STB"), ("VCR", "INPUT_VCR"),
]

_INPUT_SOURCES_HDA = [
    ("Radio", "INPUT_RADIO"), ("AUX", "INPUT_AUX"), ("NET", "INPUT_NET"), ("BT", "INPUT_BT"),
    ("AV", "INPUT_AV"),      ("SAT", "INPUT_SAT"), ("PVR", "INPUT_PVR"), ("GAME", "INPUT_GAME"),
    ("BD", "INPUT_BD"),      ("CD", "INPUT_CD"),   ("STB", "INPUT_STB"), ("UHD", "INPUT_UHD"),
]

_INPUT_SOURCES_SA = [
    ("Phono", "INPUT_PHONO"), ("CD", "INPUT_CD"),  ("BD", "INPUT_BD"),     ("SAT", "INPUT_SAT"),
    ("PVR", "INPUT_PVR"),     ("AV", "INPUT_AV"),  ("AUX", "INPUT_AUX"),   ("STB", "INPUT_STB"),
    ("NET", "INPUT_NET"),     ("USB", "INPUT_USB"), ("GAME", "INPUT_GAME"), ("ARC", "INPUT_ARC_ERC"),
]

_INPUT_SOURCES_ST = [
    ("DIG 1", "INPUT_DIG1"), ("DIG 2", "INPUT_DIG2"),
    ("DIG 3", "INPUT_DIG3"), ("DIG 4", "INPUT_DIG4"),
    ("USB", "INPUT_USB_ST"), ("NET", "INPUT_NET_ST"),
]

# PA series: pure power amplifiers, no input selection.
_INPUT_SOURCES_PA: list[tuple[str, str]] = []

_INPUT_SOURCES_BY_MODEL = {
    ApiModel.API450_SERIES: _INPUT_SOURCES_450,
    ApiModel.API860_SERIES: _INPUT_SOURCES_860,
    ApiModel.APIHDA_SERIES: _INPUT_SOURCES_HDA,
    ApiModel.APISA_SERIES: _INPUT_SOURCES_SA,
    ApiModel.APIPA_SERIES: _INPUT_SOURCES_PA,
    ApiModel.APIST_SERIES: _INPUT_SOURCES_ST,
}

# Model capability sets — used to conditionally build remote pages.
_MODELS_WITH_TUNER = {ApiModel.API450_SERIES, ApiModel.API860_SERIES, ApiModel.APIHDA_SERIES}
_MODELS_WITH_OSD = {
    ApiModel.API450_SERIES, ApiModel.API860_SERIES, ApiModel.APIHDA_SERIES,
    ApiModel.APISA_SERIES, ApiModel.APIST_SERIES,
}

# Simple commands split by capability for conditional registration.
_NAVIGATION_COMMANDS = [
    "CURSOR_UP", "CURSOR_DOWN", "CURSOR_LEFT", "CURSOR_RIGHT",
    "OK", "MENU", "BACK", "INFO", "DISPLAY",
]

_TUNER_COMMANDS = [
    "TUNER_BAND", "PRESET_UP", "PRESET_DOWN", "INPUT_FM", "INPUT_DAB",
]

# Always registered — harmless for models that don't use them, and useful in automations.
_ALWAYS_COMMANDS = ["MODE", "DIRECT"]


def _build_audio_modes_page(modes: list[tuple[str, str]]) -> dict | None:
    """Build the Audio Modes page from a list of (label, cmd_id) tuples.

    Returns None if modes is empty (e.g. SA/PA/ST series with no decode modes).

    Lays out 2-wide buttons in a 4-column grid. The first row pairs the first
    mode (typically Stereo) with Direct. Remaining modes fill subsequent rows
    two at a time. When the remaining count is odd, Mode sits alongside the
    last mode; otherwise Mode gets a full-width row at the bottom.
    """
    if not modes:
        return None

    items = []
    row = 0

    # First row: first mode + Direct
    items.append({
        "type": "text",
        "text": modes[0][0],
        "command": {"cmd_id": modes[0][1]},
        "location": {"x": 0, "y": row},
        "size": {"width": 2, "height": 1},
    })
    items.append({
        "type": "text",
        "text": "Direct",
        "command": {"cmd_id": "DIRECT"},
        "location": {"x": 2, "y": row},
        "size": {"width": 2, "height": 1},
    })
    row += 1

    # Remaining modes: 2 per row
    remaining = modes[1:]
    odd_remaining = len(remaining) % 2 == 1
    paired = remaining if not odd_remaining else remaining[:-1]

    for i in range(0, len(paired), 2):
        items.append({
            "type": "text",
            "text": paired[i][0],
            "command": {"cmd_id": paired[i][1]},
            "location": {"x": 0, "y": row},
            "size": {"width": 2, "height": 1},
        })
        items.append({
            "type": "text",
            "text": paired[i + 1][0],
            "command": {"cmd_id": paired[i + 1][1]},
            "location": {"x": 2, "y": row},
            "size": {"width": 2, "height": 1},
        })
        row += 1

    if odd_remaining:
        # Last unpaired mode on the left, Mode button on the right
        items.append({
            "type": "text",
            "text": remaining[-1][0],
            "command": {"cmd_id": remaining[-1][1]},
            "location": {"x": 0, "y": row},
            "size": {"width": 2, "height": 1},
        })
        items.append({
            "type": "text",
            "text": "Mode",
            "command": {"cmd_id": "MODE"},
            "location": {"x": 2, "y": row},
            "size": {"width": 2, "height": 1},
        })
        row += 1
    else:
        # Mode button — full width on its own row
        items.append({
            "type": "text",
            "text": "Mode",
            "command": {"cmd_id": "MODE"},
            "location": {"x": 0, "y": row},
            "size": {"width": 4, "height": 1},
        })
        row += 1

    return {
        "page_id": "audio_modes",
        "name": "Audio Modes",
        # Height is fixed at 6 — the UC Remote stretches grid cells to fill the
        # display, so a tight height makes buttons uncomfortably tall.
        "grid": {"width": 4, "height": 6},
        "items": items,
    }


def _build_sources_page(sources: list[tuple[str, str]]) -> dict | None:
    """Build the Sources page from a list of (label, cmd_id) tuples.

    Returns None if sources is empty (e.g. PA series with no input selection).

    Lays out 1×1 buttons in a 4-column grid, filling left-to-right,
    top-to-bottom to match the physical remote's button arrangement.
    """
    if not sources:
        return None

    items = []
    for i, (label, cmd_id) in enumerate(sources):
        items.append({
            "type": "text",
            "text": label,
            "command": {"cmd_id": cmd_id},
            "location": {"x": i % 4, "y": i // 4},
        })

    return {
        "page_id": "sources",
        "name": "Sources",
        # Height is fixed at 6 — see audio_modes page comment.
        "grid": {"width": 4, "height": 6},
        "items": items,
    }


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

        model = device.api_model or ApiModel.API450_SERIES
        has_osd = model in _MODELS_WITH_OSD
        has_tuner = model in _MODELS_WITH_TUNER

        # Select audio modes and input sources for the detected model
        audio_modes = _AUDIO_MODES_BY_MODEL.get(model, _AUDIO_MODES_450)
        input_sources = _INPUT_SOURCES_BY_MODEL.get(model, _INPUT_SOURCES_450)

        # Build simple_commands from capability-appropriate command sets
        simple_commands = list(_ALWAYS_COMMANDS)
        if has_osd:
            simple_commands.extend(_NAVIGATION_COMMANDS)
        if has_tuner:
            simple_commands.extend(_TUNER_COMMANDS)
        for _, cmd_id in audio_modes:
            if cmd_id not in simple_commands:
                simple_commands.append(cmd_id)
        for _, cmd_id in input_sources:
            if cmd_id not in simple_commands:
                simple_commands.append(cmd_id)

        # Build pages conditionally based on model capabilities
        pages = []

        if has_osd:
            pages.append({
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
            })

        audio_modes_page = _build_audio_modes_page(audio_modes)
        if audio_modes_page is not None:
            pages.append(audio_modes_page)

        sources_page = _build_sources_page(input_sources)
        if sources_page is not None:
            pages.append(sources_page)

        if has_tuner:
            pages.append({
                "page_id": "tuner",
                "name": "Tuner",
                # Height is fixed at 6 — see audio_modes page comment.
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
            })

        button_mapping = [
            create_btn_mapping(Buttons.DPAD_MIDDLE, short=EntityCommand(cmd_id="OK")),
        ] if has_osd else []

        super().__init__(
            entity_id,
            entity_name,
            features,
            attributes,
            simple_commands=simple_commands,
            button_mapping=button_mapping,
            ui_pages=pages,
            cmd_handler=self.handle_command,
        )
        self.subscribe_to_device(device)

        _LOG.info("[%s] Remote entity initialized with %d commands, %d pages (model: %s)",
                  entity_id, len(simple_commands), len(pages), model)

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
