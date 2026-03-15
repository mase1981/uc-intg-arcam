"""
Arcam FMJ setup flow for Unfolded Circle integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any
from ucapi import RequestUserInput, SetupAction, UserDataResponse
from ucapi_framework import BaseSetupFlow
from intg_arcam.config import ArcamConfig, PollingMode
from intg_arcam.device import ArcamDevice

_LOG = logging.getLogger(__name__)


class ArcamSetupFlow(BaseSetupFlow[ArcamConfig]):
    """Setup flow for Arcam FMJ integration."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._existing_config: ArcamConfig | None = None

    async def _handle_configuration_mode(self, msg: UserDataResponse) -> SetupAction:
        """Capture existing config before the framework removes it during update.

        TODO: ucapi-framework should support non-destructive reconfiguration natively.
        See: https://github.com/JackJPowell/ucapi-framework/issues/18
        """
        action = msg.input_values.get("action")
        device_id = msg.input_values.get("choice", "")
        if action == "update" and device_id:
            self._existing_config = self.config.get(device_id)
        else:
            self._existing_config = None
        return await super()._handle_configuration_mode(msg)

    def get_manual_entry_form(self) -> RequestUserInput:
        """Define manual entry fields, pre-populated on reconfiguration."""
        cfg = self._existing_config
        return RequestUserInput(
            {"en": "Arcam FMJ Setup"},
            [
                {
                    "id": "name",
                    "label": {"en": "Device Name"},
                    "field": {"text": {"value": cfg.name if cfg else ""}},
                },
                {
                    "id": "host",
                    "label": {"en": "IP Address"},
                    "field": {"text": {"value": cfg.host if cfg else ""}},
                },
                {
                    "id": "port",
                    "label": {"en": "Port"},
                    "field": {"number": {
                        "value": cfg.port if cfg else 50000,
                        "min": 1, "max": 65535,
                    }},
                },
                {
                    "id": "zone",
                    "label": {"en": "Zone"},
                    "field": {"number": {
                        "value": cfg.zone if cfg else 1,
                        "min": 1, "max": 2,
                    }},
                },
                {
                    "id": "info",
                    "label": {"en": "Sync Settings"},
                    "field": {"label": {"value": (
                        "Your Arcam receiver pushes all state changes automatically "
                        "per the Arcam IP protocol. Essential polling adds a lightweight "
                        "safety net (4 queries every 60 seconds). 'None' is safe per "
                        "protocol spec but disables all fail-safe polling. These settings "
                        "can be changed later."
                    )}},
                },
                {
                    "id": "polling_mode",
                    "label": {"en": "Polling Mode"},
                    "field": {"dropdown": {
                        "value": cfg.polling_mode if cfg else "essential",
                        "items": [
                            {
                                "id": "essential",
                                "label": {"en": "Essential - poll key states as fail-safe (recommended)"},
                            },
                            {
                                "id": "off",
                                "label": {"en": "None - rely on push events only"},
                            },
                            {
                                "id": "all",
                                "label": {"en": "All - poll all states (heavy, includes tuner/presets)"},
                            },
                        ],
                    }},
                },
                {
                    "id": "poll_interval",
                    "label": {"en": "Polling Interval (seconds)"},
                    "field": {"number": {
                        "value": cfg.poll_interval if cfg else 60,
                        "min": 30, "max": 600,
                    }},
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

        # Validate polling settings
        polling_mode = input_values.get("polling_mode", "essential")
        if polling_mode not in (m.value for m in PollingMode):
            _LOG.warning("Unrecognized polling_mode '%s', falling back to 'essential'", polling_mode)
            polling_mode = "essential"
        poll_interval = int(input_values.get("poll_interval", 60))
        poll_interval = max(30, min(600, poll_interval))

        _LOG.info("Testing connection to Arcam at %s:%d zone %d", host, port, zone)

        try:
            test_config = ArcamConfig(
                identifier=f"arcam_{host.replace('.', '_')}_{port}_z{zone}",
                name=name,
                host=host,
                port=port,
                zone=zone,
                polling_mode=polling_mode,
                poll_interval=poll_interval,
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
