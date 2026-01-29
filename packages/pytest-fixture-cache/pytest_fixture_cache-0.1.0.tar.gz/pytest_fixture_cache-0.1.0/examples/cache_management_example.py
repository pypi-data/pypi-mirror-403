"""
Example demonstrating cache management features

Shows how to:
- Mark fixtures dirty
- Clear specific caches
- Use cache in tests

Run with:
    pytest examples/cache_management_example.py -v
"""

import pytest
import time
from pytest_fixture_cache import cached_fixture


# Simulated "database"
_database = {"records": []}


def add_record(data):
    """Simulate adding a record to database"""
    _database["records"].append(data)


def clear_database():
    """Simulate clearing database"""
    _database["records"] = []


def get_record_count():
    """Get number of records in database"""
    return len(_database["records"])


@cached_fixture
@pytest.fixture
def seeded_database():
    """
    Fixture that seeds database with test data.
    This is expensive, so we cache it.
    """
    print("\n[FIXTURE] Seeding database (slow operation)...")
    clear_database()

    # Simulate expensive seeding operation
    time.sleep(2)
    for i in range(100):
        add_record({"id": i, "name": f"Record {i}"})

    return {
        "record_count": get_record_count(),
        "seeded": True
    }


def test_database_seeded(seeded_database):
    """Test that database was seeded correctly"""
    assert seeded_database["seeded"] is True
    assert seeded_database["record_count"] == 100


def test_can_query_records(seeded_database):
    """Test that we can query seeded records"""
    # In real scenario, you'd query the database
    assert get_record_count() == 100


def test_modify_database_and_invalidate(seeded_database, mark_dirty):
    """
    Test that modifies database and marks cache dirty.

    After this test, the cache is invalid and will be recreated
    on next test run.
    """
    # Use the seeded database
    initial_count = get_record_count()
    assert initial_count == 100

    # Modify database (making cache invalid)
    clear_database()
    assert get_record_count() == 0

    # Mark cache dirty so next test gets fresh data
    mark_dirty('seeded_database')
    print("\n[TEST] Marked 'seeded_database' cache as dirty")


def test_clear_cache_programmatically(clear_cache):
    """
    Test demonstrating programmatic cache clearing.

    This clears the cache entirely, not just marking it dirty.
    """
    # Clear specific fixture cache
    clear_cache('seeded_database')
    print("\n[TEST] Cleared 'seeded_database' cache")

    # Or clear all caches
    # clear_cache()  # Clears ALL fixture caches


# Example: Fixture that should NOT be cached
@pytest.fixture
def current_timestamp():
    """
    This fixture returns current time - should NOT be cached
    because it needs to be different each time.

    Note: No @cached_fixture decorator!
    """
    import datetime
    return {
        "timestamp": datetime.datetime.now().isoformat(),
        "cached": False
    }


def test_timestamp_not_cached(current_timestamp):
    """Test that timestamp fixture is not cached"""
    assert current_timestamp["cached"] is False
    assert "timestamp" in current_timestamp


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
