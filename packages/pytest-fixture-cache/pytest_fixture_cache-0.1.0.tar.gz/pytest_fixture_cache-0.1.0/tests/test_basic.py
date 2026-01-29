"""
Basic tests for pytest-fixture-cache library

These tests verify that the library works correctly.
"""

import pytest
from pytest_fixture_cache import (
    cached_fixture,
    save_fixture_cache,
    load_fixture_cache,
    clear_fixture_cache,
    mark_fixture_dirty,
    get_cache_stats
)


@cached_fixture
@pytest.fixture
def simple_fixture():
    """Simple cached fixture for testing"""
    return {"value": 42, "name": "test"}


def test_cached_fixture_works(simple_fixture):
    """Test that @cached_fixture decorator works"""
    assert simple_fixture["value"] == 42
    assert simple_fixture["name"] == "test"


def test_save_and_load_cache():
    """Test saving and loading cache"""
    test_data = {"key": "value", "number": 123}

    # Save to cache
    result = save_fixture_cache("test_fixture", test_data)
    assert result is True

    # Load from cache
    loaded_data = load_fixture_cache("test_fixture")
    assert loaded_data is not None
    assert loaded_data["key"] == "value"
    assert loaded_data["number"] == 123

    # Clean up
    clear_fixture_cache("test_fixture")


def test_dirty_cache_not_loaded():
    """Test that dirty cache is not loaded"""
    test_data = {"data": "test"}

    # Save to cache
    save_fixture_cache("test_dirty", test_data)

    # Mark dirty
    mark_fixture_dirty("test_dirty")

    # Try to load - should return None
    loaded = load_fixture_cache("test_dirty")
    assert loaded is None

    # Clean up
    clear_fixture_cache("test_dirty")


def test_cache_stats():
    """Test getting cache statistics"""
    # Create some cache entries
    save_fixture_cache("stat_test_1", {"a": 1})
    save_fixture_cache("stat_test_2", {"b": 2})

    # Get stats
    stats = get_cache_stats()
    assert isinstance(stats, list)
    assert len(stats) >= 2

    # Clean up
    clear_fixture_cache("stat_test_1")
    clear_fixture_cache("stat_test_2")


def test_clear_all_cache():
    """Test clearing all caches"""
    # Create some cache entries
    save_fixture_cache("clear_test_1", {"a": 1})
    save_fixture_cache("clear_test_2", {"b": 2})

    # Clear all
    clear_fixture_cache()

    # Verify cleared
    assert load_fixture_cache("clear_test_1") is None
    assert load_fixture_cache("clear_test_2") is None
