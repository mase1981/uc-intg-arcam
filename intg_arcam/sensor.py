"""
Arcam FMJ Sensor Entities.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi.sensor import Attributes, DeviceClasses, Sensor, States

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
            device_class=DeviceClasses.CUSTOM,
        )

        _LOG.info("[%s] Audio format sensor initialized", entity_id)
        device.events.on("UPDATE", self._on_device_update)

    async def _on_device_update(self, entity_id: str, update_data: dict[str, Any]) -> None:
        if entity_id == self.id:
            if Attributes.VALUE in update_data:
                self.attributes[Attributes.STATE] = States.ON
                self.attributes[Attributes.VALUE] = update_data[Attributes.VALUE]
                _LOG.debug("[%s] Audio format updated to %s", self.id, update_data[Attributes.VALUE])


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
            device_class=DeviceClasses.CUSTOM,
        )

        _LOG.info("[%s] Sound mode sensor initialized", entity_id)
        device.events.on("UPDATE", self._on_device_update)

    async def _on_device_update(self, entity_id: str, update_data: dict[str, Any]) -> None:
        if entity_id == self.id:
            if Attributes.VALUE in update_data:
                self.attributes[Attributes.STATE] = States.ON
                self.attributes[Attributes.VALUE] = update_data[Attributes.VALUE]
                _LOG.debug("[%s] Sound mode updated to %s", self.id, update_data[Attributes.VALUE])
