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
        )

    def register_available_entities(
        self, device_config: ArcamConfig, device: ArcamDevice
    ) -> None:
        """
        Register entities to both available and configured lists.

        The Remote's subscription flow doesn't trigger for this integration,
        so we bypass it by adding entities directly to configured_entities.
        This ensures entities appear and work immediately after setup.

        Skips re-registration on reconnect to avoid resetting entity states
        to their initial values (e.g., UNKNOWN) which the framework would
        emit as entity_change events before our state sync completes.
        """
        device_id = self.get_device_id(device_config)

        # Check if entities are already registered (reconnect scenario)
        if self.api.configured_entities.contains(f"media_player.{device_id}"):
            _LOG.debug("Entities already registered for %s, skipping", device_id)
            return

        _LOG.info("Registering available entities for %s", device_id)

        entities = self.create_entities(device_config, device)

        for entity in entities:
            if self.api.available_entities.contains(entity.id):
                self.api.available_entities.remove(entity.id)
            self.api.available_entities.add(entity)

            if self.api.configured_entities.contains(entity.id):
                self.api.configured_entities.remove(entity.id)
            self.api.configured_entities.add(entity)
