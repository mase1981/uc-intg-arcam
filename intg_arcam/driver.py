"""
Arcam FMJ driver for Unfolded Circle Remote.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from ucapi_framework import BaseIntegrationDriver
from intg_arcam.config import ArcamConfig
from intg_arcam.device import ArcamDevice
from intg_arcam.media_player import ArcamMediaPlayer
from intg_arcam.remote import ArcamRemote
from intg_arcam.sensor import ArcamAudioFormatSensor, ArcamSoundModeSensor, ArcamRoomEqSensor
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
                lambda cfg, dev: [
                    ArcamAudioFormatSensor(cfg, dev),
                    ArcamSoundModeSensor(cfg, dev),
                    ArcamRoomEqSensor(cfg, dev),
                ],
                ArcamSoundModeSelect,
            ],
            driver_id="arcam",
            require_connection_before_registry=True,
        )

    async def on_subscribe_entities(self, entity_ids: list[str]) -> None:
        await super().on_subscribe_entities(entity_ids)

        # On Remote restart the generic CONNECT handler connects the device
        # before SUBSCRIBE_ENTITIES arrives, so the framework's transition-gated
        # registration is skipped and the entity never reaches available/configured,
        # causing "no configured entity found" 404s. Reconcile any subscribed entity
        # whose device is connected but which is missing from configured_entities.
        for entity_id in entity_ids:
            if self.api.configured_entities.contains(entity_id):
                continue

            device_id = self.device_from_entity_id(entity_id)
            if device_id is None:
                continue

            device = self._device_instances.get(device_id)
            if device is None or not device.is_connected:
                continue

            if self.api.available_entities.get(entity_id) is None:
                await self.async_register_available_entities(
                    self.get_device_config(device_id), device
                )

            entity = self.api.available_entities.get(entity_id)
            if entity is not None:
                self.api.configured_entities.add(entity)
                await self.refresh_entity_state(entity_id)
                _LOG.info("Recovered subscription for entity %s after restart", entity_id)
