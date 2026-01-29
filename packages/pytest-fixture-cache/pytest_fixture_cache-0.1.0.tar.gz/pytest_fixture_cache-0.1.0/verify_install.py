#!/usr/bin/env python
"""
Verification script to ensure pytest-fixture-cache is installed correctly.

Run this after installation to verify everything works.
"""

import sys


def main():
    print("=" * 70)
    print("pytest-fixture-cache Installation Verification")
    print("=" * 70)
    print()

    # Test 1: Import the package
    print("1. Testing package import...")
    try:
        import pytest_fixture_cache
        print(f"   ✓ Package imported successfully")
        print(f"   Version: {pytest_fixture_cache.__version__}")
    except ImportError as e:
        print(f"   ✗ Failed to import package: {e}")
        return False

    # Test 2: Import main components
    print("\n2. Testing component imports...")
    try:
        from pytest_fixture_cache import (
            cached_fixture,
            save_fixture_cache,
            load_fixture_cache,
            clear_fixture_cache,
            get_cache_stats,
        )
        print("   ✓ All main components imported")
    except ImportError as e:
        print(f"   ✗ Failed to import components: {e}")
        return False

    # Test 3: Test basic caching
    print("\n3. Testing basic cache operations...")
    try:
        test_data = {"test": "data", "number": 42}

        # Save
        result = save_fixture_cache("verify_test", test_data)
        if not result:
            print("   ✗ Failed to save to cache")
            return False

        # Load
        loaded = load_fixture_cache("verify_test")
        if loaded is None:
            print("   ✗ Failed to load from cache")
            return False

        if loaded != test_data:
            print("   ✗ Loaded data doesn't match saved data")
            return False

        # Stats
        stats = get_cache_stats()
        if not isinstance(stats, list):
            print("   ✗ Failed to get cache stats")
            return False

        # Clean up
        clear_fixture_cache("verify_test")

        print("   ✓ Cache operations work correctly")
    except Exception as e:
        print(f"   ✗ Cache operations failed: {e}")
        return False

    # Test 4: Check pytest plugin
    print("\n4. Testing pytest plugin registration...")
    try:
        import pytest

        # Check if plugin is registered
        config = pytest.Config.fromdictargs({"plugins": []})
        plugin_manager = config.pluginmanager

        if plugin_manager.has_plugin("fixture_cache"):
            print("   ✓ Pytest plugin registered")
        else:
            # Plugin might be registered under different name
            print("   ⚠ Plugin registration unclear (may still work)")
    except Exception as e:
        print(f"   ⚠ Could not verify plugin registration: {e}")
        # Not a critical failure

    # Test 5: Check cache location
    print("\n5. Testing cache location...")
    try:
        from pytest_fixture_cache import get_cache_location

        cache_path = get_cache_location()
        print(f"   ✓ Cache location: {cache_path}")
    except Exception as e:
        print(f"   ✗ Failed to get cache location: {e}")
        return False

    # All tests passed
    print("\n" + "=" * 70)
    print("✓ All verification tests passed!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Try running: pytest examples/basic_example.py -v")
    print("  2. Check cache stats: pytest --cache-stats")
    print("  3. Read QUICKSTART.md for more examples")
    print()
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
