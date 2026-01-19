"""
Arcam FMJ setup flow for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any
from ucapi import RequestUserInput
from ucapi_framework import BaseSetupFlow
from intg_arcam.config import ArcamConfig
from intg_arcam.device import ArcamDevice

_LOG = logging.getLogger(__name__)


class ArcamSetupFlow(BaseSetupFlow[ArcamConfig]):
    """Setup flow for Arcam FMJ integration."""

    def get_manual_entry_form(self) -> RequestUserInput:
        """Define manual entry fields."""
        return RequestUserInput(
            {"en": "Arcam FMJ Setup"},
            [
                {
                    "id": "name",
                    "label": {"en": "Device Name"},
                    "field": {"text": {"value": ""}},
                },
                {
                    "id": "host",
                    "label": {"en": "IP Address"},
                    "field": {"text": {"value": ""}},
                },
                {
                    "id": "port",
                    "label": {"en": "Port"},
                    "field": {"number": {"value": 50000, "min": 1, "max": 65535}},
                },
                {
                    "id": "zone",
                    "label": {"en": "Zone"},
                    "field": {"number": {"value": 1, "min": 1, "max": 2}},
                },
            ]
        )

    async def query_device(
        self, input_values: dict[str, Any]
    ) -> ArcamConfig | RequestUserInput:
        """
        Validate connection and create config.
        Called after user provides info.
        """
        host = input_values.get("host", "").strip()
        if not host:
            raise ValueError("IP address is required")

        port = int(input_values.get("port", 50000))
        zone = int(input_values.get("zone", 1))
        name = input_values.get("name", f"Arcam ({host})").strip()

        _LOG.info("Testing connection to Arcam at %s:%d zone %d", host, port, zone)

        try:
            test_config = ArcamConfig(
                identifier=f"arcam_{host.replace('.', '_')}_{port}_z{zone}",
                name=name,
                host=host,
                port=port,
                zone=zone
            )

            test_device = ArcamDevice(test_config)
            connected = await asyncio.wait_for(
                test_device.connect(),
                timeout=15.0
            )
            await test_device.disconnect()

            if not connected:
                raise ValueError(f"Failed to connect to Arcam at {host}:{port}")

            _LOG.info("Successfully connected to Arcam at %s:%d", host, port)
            return test_config

        except asyncio.TimeoutError:
            raise ValueError(
                f"Connection timeout to {host}:{port}\n"
                "Please verify:\n"
                "- Device is powered on\n"
                "- Network connection is available\n"
                "- IP address and port are correct"
            ) from None
        except Exception as err:
            _LOG.error("Setup failed: %s", err)
            raise ValueError(f"Setup failed: {err}") from err
