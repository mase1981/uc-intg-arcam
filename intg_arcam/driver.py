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
        _LOG.info("=== CREATE_ENTITIES CALLED for %s ===", device_config.name)
        try:
            entities = [
                ArcamMediaPlayer(device_config, device),
                ArcamRemote(device_config, device),
                ArcamAudioFormatSensor(device_config, device),
                ArcamSoundModeSensor(device_config, device),
                ArcamSoundModeSelect(device_config, device),
            ]
            _LOG.info("=== CREATED %d ENTITIES: %s ===",
                     len(entities), [e.id for e in entities])
            return entities
        except Exception as err:
            _LOG.error("=== CREATE_ENTITIES FAILED: %s ===", err, exc_info=True)
            raise

    def register_available_entities(
        self, device_config: ArcamConfig, device: ArcamDevice
    ) -> None:
        """Register available entities with debug logging."""
        _LOG.info("=== REGISTER_AVAILABLE_ENTITIES CALLED for %s ===",
                 device_config.identifier)

        entities = self.create_entities(device_config, device)
        _LOG.info("=== Got %d entities to register ===", len(entities))

        for entity in entities:
            _LOG.info("=== Registering entity: %s (type: %s) ===",
                     entity.id, type(entity).__name__)
            if self.api.available_entities.contains(entity.id):
                self.api.available_entities.remove(entity.id)
            self.api.available_entities.add(entity)

        all_available = list(self.api.available_entities.get_all())
        _LOG.info("=== TOTAL available_entities after registration: %d ===",
                 len(all_available))
        for e in all_available:
            _LOG.info("===   - %s ===", e.get("entity_id", "unknown"))
