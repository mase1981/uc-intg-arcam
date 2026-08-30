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
from intg_arcam.sensor import (
    ArcamAudioFormatSensor,
    ArcamVideoModeSensor,
    ArcamSoundModeSensor,
    ArcamRoomEqSensor,
)
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
                    ArcamVideoModeSensor(cfg, dev),
                    ArcamSoundModeSensor(cfg, dev),
                    ArcamRoomEqSensor(cfg, dev),
                ],
                ArcamSoundModeSelect,
            ],
            driver_id="arcam",
            require_connection_before_registry=True,
        )
        self._subscribed_entity_ids: set[str] = set()

    async def on_subscribe_entities(self, entity_ids: list[str]) -> None:
        self._subscribed_entity_ids.update(entity_ids)
        await super().on_subscribe_entities(entity_ids)
        await self._configure_subscribed(entity_ids)

    async def on_unsubscribe_entities(self, entity_ids: list[str]) -> None:
        self._subscribed_entity_ids.difference_update(entity_ids)
        await super().on_unsubscribe_entities(entity_ids)

    async def async_register_available_entities(self, device_config, device) -> None:
        await super().async_register_available_entities(device_config, device)
        # Entities have just become available. In hub mode this happens after the
        # device connects, which can be after the Remote's SUBSCRIBE_ENTITIES has
        # already been processed (and dropped, since the entity wasn't available
        # yet) - the cause of "no configured entity found" 404s on Remote restart.
        # Reconcile now so any already-subscribed entity gets configured.
        await self._configure_subscribed(self._subscribed_entity_ids)

    async def _configure_subscribed(self, entity_ids) -> None:
        for entity_id in list(entity_ids):
            if self.api.configured_entities.contains(entity_id):
                continue
            entity = self.api.available_entities.get(entity_id)
            if entity is None:
                continue
            self.api.configured_entities.add(entity)
            await self.refresh_entity_state(entity_id)
            _LOG.info("Configured subscribed entity %s (restart recovery)", entity_id)
