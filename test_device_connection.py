"""Test device connection with simulator."""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from intg_arcam.config import ArcamConfig
from intg_arcam.device import ArcamDevice


async def test_device_connection():
    """Test device connection and basic operations."""
    print("Testing ArcamDevice connection...")

    # Create test configuration
    config = ArcamConfig(
        identifier="test_arcam",
        name="Test Arcam",
        host="127.0.0.1",
        port=50000,
        zone=1
    )

    # Create device
    print(f"\n[1] Creating device: {config.name} at {config.host}:{config.port}")
    device = ArcamDevice(config)

    try:
        print("\n[2] Testing connection (15 second timeout)...")
        print("    Note: Start the simulator first with: python tools/arcam_simulator.py")

        # Attempt connection with timeout
        connected = await asyncio.wait_for(
            device.connect(),
            timeout=15.0
        )

        if connected:
            print(f"[OK] Device connected successfully")
            print(f"    - Power: {device.power}")
            print(f"    - Volume: {device.volume}")
            print(f"    - Muted: {device.muted}")
            print(f"    - Source: {device.source}")
            print(f"    - Source List: {device.source_list}")

            print("\n[3] Testing disconnect...")
            await device.disconnect()
            print("[OK] Device disconnected successfully")

            return True
        else:
            print("[FAIL] Device failed to connect")
            return False

    except asyncio.TimeoutError:
        print("[FAIL] Connection timeout - is the simulator running?")
        return False
    except Exception as e:
        print(f"[FAIL] Connection error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            await device.disconnect()
        except:
            pass


if __name__ == "__main__":
    print("=" * 60)
    print("Arcam Device Connection Test")
    print("=" * 60)

    success = asyncio.run(test_device_connection())

    print("\n" + "=" * 60)
    if success:
        print("[SUCCESS] All tests passed!")
    else:
        print("[FAIL] Tests failed")
    print("=" * 60)

    sys.exit(0 if success else 1)
