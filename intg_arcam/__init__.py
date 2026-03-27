"""
Arcam FMJ for Unfolded Circle Remote.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from ucapi import DeviceStates
from ucapi_framework import get_config_path, BaseConfigManager
from intg_arcam.driver import ArcamDriver
from intg_arcam.setup_flow import ArcamSetupFlow
from intg_arcam.config import ArcamConfig

try:
    driver_path = Path(__file__).parent.parent.absolute() / "driver.json"
    with open(driver_path, "r", encoding="utf-8") as f:
        driver_info = json.load(f)
        __version__ = driver_info.get("version", "0.0.0")
except (FileNotFoundError, json.JSONDecodeError, KeyError):
    __version__ = "0.0.0"

__all__ = ["__version__"]

_LOG = logging.getLogger(__name__)


class JournaldFormatter(logging.Formatter):
    """Formatter for journald. Prefixes messages with syslog priority level.

    DEBUG app messages are logged with priority 6 (info) and INFO with priority
    5 (notice). This is a workaround until the log subsystem on the Remote is
    updated to support debug levels.
    """

    PRIORITY_MAP = {
        logging.DEBUG: "<6>",     # SD_INFO
        logging.INFO: "<5>",      # SD_NOTICE
        logging.WARNING: "<4>",   # SD_WARNING
        logging.ERROR: "<3>",     # SD_ERR
        logging.CRITICAL: "<2>",  # SD_CRIT
    }

    def format(self, record):
        """Format the log record with journald priority prefix."""
        priority = self.PRIORITY_MAP.get(record.levelno, "<6>")
        return f"{priority}{record.name}: {record.getMessage()}"


async def main():
    """Main entry point."""
    # Systemd/journald detection: INVOCATION_ID is set by systemd when running
    # as a service on the UC Remote.
    if os.getenv("INVOCATION_ID"):
        handler = logging.StreamHandler()
        handler.setFormatter(JournaldFormatter())
        logging.basicConfig(handlers=[handler])
    else:
        logging.basicConfig(
            format="%(asctime)s.%(msecs)03d %(levelname)-5s %(name)s.%(funcName)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    level = os.getenv("UC_LOG_LEVEL", "DEBUG").upper()
    logging.getLogger("intg_arcam").setLevel(level)
    # arcam.fmj pinned to INFO: only 4 statements (connect/disconnect lifecycle),
    # avoids per-packet DEBUG noise while retaining useful operational events.
    logging.getLogger("arcam.fmj").setLevel(logging.INFO)
    logging.getLogger("websockets").setLevel(logging.WARNING)

    _LOG.info("Starting Arcam FMJ Integration v%s", __version__)

    try:
        driver = ArcamDriver()

        config_path = get_config_path(driver.api.config_dir_path or "")
        _LOG.info("Using configuration path: %s", config_path)

        config_manager = BaseConfigManager(
            config_path,
            add_handler=driver.on_device_added,
            remove_handler=driver.on_device_removed,
            config_class=ArcamConfig,
        )
        driver.config_manager = config_manager

        setup_handler = ArcamSetupFlow.create_handler(driver)

        driver_json_path = os.path.join(os.path.dirname(__file__), "..", "driver.json")
        await driver.api.init(os.path.abspath(driver_json_path), setup_handler)

        await driver.register_all_device_instances(connect=False)

        device_count = len(list(config_manager.all()))
        if device_count > 0:
            await driver.api.set_device_state(DeviceStates.CONNECTED)
        else:
            await driver.api.set_device_state(DeviceStates.DISCONNECTED)

        _LOG.info("Arcam FMJ integration started")

        await asyncio.Future()

    except KeyboardInterrupt:
        _LOG.info("Integration stopped by user")
    except Exception as err:
        _LOG.critical("Fatal error: %s", err, exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
