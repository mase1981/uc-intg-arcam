"""
Arcam FMJ driver for Unfolded Circle Remote.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from ucapi import Entity
from ucapi_framework import BaseIntegrationDriver
from intg_arcam.config import ArcamConfig
from intg_arcam.device import ArcamDevice
from intg_arcam.media_player import ArcamMediaPlayer
from intg_arcam.remote import ArcamRemote
from intg_arcam.sensor import ArcamAudioFormatSensor, ArcamSoundModeSensor
from intg_arcam.select import ArcamSoundModeSelect

_LOG = logging.getLogger(__name__)


class ArcamDriver(BaseIntegrationDriver[ArcamDevice, ArcamConfig]):
    """Arcam FMJ integration driver."""

    def __init__(self):
        super().__init__(
            device_class=ArcamDevice,
            entity_classes=[
                ArcamMediaPlayer,
                ArcamRemote,
                ArcamAudioFormatSensor,
                ArcamSoundModeSensor,
                ArcamSoundModeSelect,
            ],
            driver_id="arcam",
        )

    def create_entities(
        self, device_config: ArcamConfig, device: ArcamDevice
    ) -> list[Entity]:
        """Create entity instances."""
        _LOG.info("Creating entities for %s", device_config.name)
        return [
            ArcamMediaPlayer(device_config, device),
            ArcamRemote(device_config, device),
            ArcamAudioFormatSensor(device_config, device),
            ArcamSoundModeSensor(device_config, device),
            ArcamSoundModeSelect(device_config, device),
        ]

    def register_available_entities(
        self, device_config: ArcamConfig, device: ArcamDevice
    ) -> None:
        """Register entities as both available and configured."""
        device_id = self.get_device_id(device_config)
        _LOG.info("Registering entities for %s", device_id)

        entities = self.create_entities(device_config, device)

        for entity in entities:
            if self.api.available_entities.contains(entity.id):
                self.api.available_entities.remove(entity.id)
            self.api.available_entities.add(entity)

            if self.api.configured_entities.contains(entity.id):
                self.api.configured_entities.remove(entity.id)
            self.api.configured_entities.add(entity)
            _LOG.info("Registered entity: %s", entity.id)
