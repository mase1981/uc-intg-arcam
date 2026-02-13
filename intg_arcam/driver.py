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
                lambda cfg, dev: [
                    ArcamAudioFormatSensor(cfg, dev),
                    ArcamSoundModeSensor(cfg, dev),
                ],
                ArcamSoundModeSelect,
            ],
            driver_id="arcam",
        )
