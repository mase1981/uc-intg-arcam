"""
Arcam FMJ Sensor Entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi.sensor import Attributes, Sensor, States

from intg_arcam.config import ArcamConfig
from intg_arcam.device import ArcamDevice

_LOG = logging.getLogger(__name__)


class ArcamAudioFormatSensor(Sensor):
    """Sensor for displaying incoming audio format."""

    def __init__(self, device_config: ArcamConfig, device: ArcamDevice):
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}_audio_format"
        entity_name = f"{device_config.name} Audio Format"

        attributes = {
            Attributes.STATE: States.UNAVAILABLE,
            Attributes.VALUE: "Unknown",
        }

        super().__init__(
            entity_id,
            entity_name,
            [],
            attributes,
            device_class=None,
        )

        _LOG.info("[%s] Audio format sensor initialized", entity_id)


class ArcamSoundModeSensor(Sensor):
    """Sensor for displaying current sound/decode mode."""

    def __init__(self, device_config: ArcamConfig, device: ArcamDevice):
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}_sound_mode"
        entity_name = f"{device_config.name} Sound Mode"

        attributes = {
            Attributes.STATE: States.UNAVAILABLE,
            Attributes.VALUE: "Unknown",
        }

        super().__init__(
            entity_id,
            entity_name,
            [],
            attributes,
            device_class=None,
        )

        _LOG.info("[%s] Sound mode sensor initialized", entity_id)
