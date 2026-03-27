"""
Arcam FMJ configuration for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from dataclasses import dataclass
from enum import StrEnum
from ucapi_framework import BaseConfigManager


class PollingMode(StrEnum):
    OFF = "off"
    ESSENTIAL = "essential"
    ALL = "all"


@dataclass
class ArcamConfig:
    """Arcam FMJ device configuration."""
    identifier: str
    name: str
    host: str
    port: int = 50000
    zone: int = 1
    polling_mode: str = "essential"
    poll_interval: int = 60


class ArcamConfigManager(BaseConfigManager[ArcamConfig]):
    """Configuration manager with automatic JSON persistence."""
    pass
