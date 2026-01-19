"""Test arcam-fmj imports to ensure all dependencies are available."""

import sys


def test_arcam_imports():
    """Test that arcam.fmj can be imported and has required classes."""
    print("Testing arcam-fmj imports...")

    try:
        # Test basic module import
        import arcam.fmj
        print("[OK] arcam.fmj module imported successfully")

        # Test Client import
        from arcam.fmj.client import Client
        print("[OK] arcam.fmj.client.Client imported successfully")

        # Test State import
        from arcam.fmj.state import State
        print("[OK] arcam.fmj.state.State imported successfully")

        # Test that we can instantiate (without connecting)
        print("\nTesting class instantiation...")
        client = Client("127.0.0.1", 50000)
        print(f"[OK] Client instantiated: {client}")

        state = State(client, 1)
        print(f"[OK] State instantiated: {state}")

        print("\n[SUCCESS] All imports successful!")
        return True

    except ImportError as e:
        print(f"\n[FAIL] Import failed: {e}")
        print("\nMissing dependency. Please install:")
        print("  pip install defusedxml")
        return False
    except Exception as e:
        print(f"\n[FAIL] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_arcam_imports()
    sys.exit(0 if success else 1)
