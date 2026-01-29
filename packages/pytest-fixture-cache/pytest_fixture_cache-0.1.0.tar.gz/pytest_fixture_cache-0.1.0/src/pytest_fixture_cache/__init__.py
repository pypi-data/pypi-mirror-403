"""
pytest-fixture-cache: Smart fixture caching for pytest

A pytest plugin that provides automatic caching for expensive fixtures
using SQLite storage with dirty/clean status tracking.

Basic usage:
    from pytest_fixture_cache import cached_fixture

    @cached_fixture
    @pytest.fixture
    def expensive_fixture():
        # Expensive setup (API calls, DB seeding, etc.)
        return {"data": "value"}

CLI usage:
    pytest --clear-cache       # Clear all caches before run
    pytest --no-cache          # Disable caching for this run
    pytest --cache-stats       # Show cache statistics

For more details, see: https://github.com/yourusername/pytest-fixture-cache
"""

__version__ = "0.1.0"

from .decorator import cached_fixture
from .storage import (
    save_fixture_cache,
    load_fixture_cache,
    mark_fixture_dirty,
    mark_fixture_clean,
    clear_fixture_cache,
    get_cache_stats,
    get_cache_location,
)
from .utils import clear_fixtures, clear_all_fixtures

__all__ = [
    # Decorator
    "cached_fixture",
    # Storage API
    "save_fixture_cache",
    "load_fixture_cache",
    "mark_fixture_dirty",
    "mark_fixture_clean",
    "clear_fixture_cache",
    "get_cache_stats",
    "get_cache_location",
    # Utilities
    "clear_fixtures",
    "clear_all_fixtures",
]
