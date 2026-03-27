"""
Arcam FMJ Sensor Entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi.sensor import Attributes, States
from ucapi_framework import SensorEntity

from intg_arcam.config import ArcamConfig
from intg_arcam.device import ArcamDevice

_LOG = logging.getLogger(__name__)


class ArcamAudioFormatSensor(SensorEntity):
    """Sensor for displaying incoming audio format."""

    def __init__(self, device_config: ArcamConfig, device: ArcamDevice):
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}.audio_format"
        entity_name = f"{device_config.name} Audio Format"

        attributes = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.VALUE: "Unknown",
        }

        super().__init__(
            entity_id,
            entity_name,
            [],
            attributes,
            device_class=None,
        )
        self.subscribe_to_device(device)

        _LOG.info("[%s] Audio format sensor initialized", entity_id)

    async def sync_state(self):
        value = self._device.audio_format
        self.update({
            Attributes.STATE: States.ON if value else States.UNKNOWN,
            Attributes.VALUE: value or "",
        })


class ArcamSoundModeSensor(SensorEntity):
    """Sensor for displaying current sound/decode mode."""

    def __init__(self, device_config: ArcamConfig, device: ArcamDevice):
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}.sound_mode"
        entity_name = f"{device_config.name} Sound Mode"

        attributes = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.VALUE: "Unknown",
        }

        super().__init__(
            entity_id,
            entity_name,
            [],
            attributes,
            device_class=None,
        )
        self.subscribe_to_device(device)

        _LOG.info("[%s] Sound mode sensor initialized", entity_id)

    async def sync_state(self):
        value = self._device.sound_mode
        self.update({
            Attributes.STATE: States.ON if value else States.UNKNOWN,
            Attributes.VALUE: value or "",
        })


class ArcamRoomEqSensor(SensorEntity):
    """Sensor for displaying current room EQ / Dirac profile."""

    def __init__(self, device_config: ArcamConfig, device: ArcamDevice):
        self._device = device
        self._device_config = device_config

        entity_id = f"sensor.{device_config.identifier}.room_eq"
        entity_name = f"{device_config.name} Room EQ"

        attributes = {
            Attributes.STATE: States.UNKNOWN,
            Attributes.VALUE: "",
        }

        super().__init__(
            entity_id,
            entity_name,
            [],
            attributes,
            device_class=None,
        )
        self.subscribe_to_device(device)

        _LOG.info("[%s] Room EQ sensor initialized", entity_id)

    async def sync_state(self):
        value = self._device.room_eq
        self.update({
            Attributes.STATE: States.ON if value else States.UNKNOWN,
            Attributes.VALUE: value or "",
        })
