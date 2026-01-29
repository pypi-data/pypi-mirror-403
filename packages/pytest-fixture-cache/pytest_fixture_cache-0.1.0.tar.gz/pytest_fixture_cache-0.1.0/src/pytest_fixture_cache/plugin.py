"""
Pytest plugin for fixture cache management.

Provides:
1. Command-line options:
   - --clear-cache: Clear all fixture caches before running tests
   - --no-cache: Disable fixture caching for this run
   - --cache-stats: Show fixture cache statistics and exit

2. Global fixtures:
   - mark_dirty: Function to mark fixtures as dirty from tests
   - clear_cache: Function to clear caches from tests

Usage:
    # Run tests with cache
    pytest tests/

    # Clear cache before run
    pytest tests/ --clear-cache

    # Disable caching
    pytest tests/ --no-cache

    # Show cache stats
    pytest --cache-stats

    # In tests - mark fixture dirty
    def test_something(my_fixture, mark_dirty):
        # Test modifies data
        modify_data(my_fixture)

        # Invalidate cache
        mark_dirty('my_fixture')
"""

import pytest

from .storage import (
    clear_fixture_cache,
    mark_fixture_dirty,
    get_cache_stats
)


def pytest_addoption(parser):
    """Add custom command-line options for fixture caching"""
    group = parser.getgroup("fixture-cache", "Fixture caching options")

    group.addoption(
        "--clear-cache",
        action="store_true",
        default=False,
        help="Clear all fixture caches before running tests"
    )

    group.addoption(
        "--no-cache",
        action="store_true",
        default=False,
        help="Disable fixture caching for this test run"
    )

    group.addoption(
        "--cache-stats",
        action="store_true",
        default=False,
        help="Show fixture cache statistics and exit (does not run tests)"
    )


def pytest_configure(config):
    """Configure plugin based on command-line options"""

    # Show cache stats if requested
    if config.option.cache_stats:
        print("\n" + "=" * 80)
        print("FIXTURE CACHE STATISTICS")
        print("=" * 80)

        stats = get_cache_stats()
        if not stats:
            print("\nNo cached fixtures found.")
            print("\nHint: Run tests first to create cached fixtures.")
        else:
            print(f"\nFound {len(stats)} cached fixture(s):\n")
            for entry in stats:
                print(f"Fixture: {entry['fixtureName']}")
                print(f"  Scope:   {entry['fixtureScope']}")
                print(f"  Status:  {entry['status']}")
                print(f"  Hits:    {entry['hitCount']}")
                print(f"  Created: {entry['createdAt']}")
                print(f"  Updated: {entry['updatedAt']}")
                print()

        print("=" * 80)
        print("\nUsage:")
        print("  pytest --clear-cache      # Clear all caches")
        print("  pytest --no-cache         # Disable caching")
        print("  pytest tests/ -v          # Run tests with caching enabled")
        print("=" * 80)

        # Exit without running tests
        pytest.exit("Cache stats displayed", returncode=0)

    # Clear cache if requested
    if config.option.clear_cache:
        print("\n[CACHE] Clearing all fixture caches...")
        clear_fixture_cache()
        print("[CACHE] All caches cleared successfully\n")


@pytest.fixture(scope="session")
def mark_dirty():
    """
    Global fixture to mark caches dirty from tests.

    This is a session-scoped fixture that provides a function to mark
    fixture caches as dirty. When a fixture is marked dirty, it will be
    recreated on the next test run instead of being loaded from cache.

    Returns:
        Function that takes a fixture name and marks it dirty

    Usage:
        def test_modify_data(my_fixture, mark_dirty):
            # Test that modifies fixture data
            delete_data(my_fixture['id'])

            # Mark cache dirty so next test gets fresh data
            mark_dirty('my_fixture')

        def test_with_fresh_data(my_fixture):
            # This will create a new fixture (cache is dirty)
            assert my_fixture['id']
    """
    return mark_fixture_dirty


@pytest.fixture(scope="session")
def clear_cache():
    """
    Global fixture to clear fixture caches from tests.

    This is a session-scoped fixture that provides a function to clear
    fixture caches. Clearing removes the cache entry entirely.

    Returns:
        Function that takes an optional fixture name and clears cache

    Usage:
        def test_something(clear_cache):
            # Clear specific fixture
            clear_cache('my_fixture')

            # Or clear all fixtures
            clear_cache()
    """
    return clear_fixture_cache
