"""
Basic example of using pytest-fixture-cache

Run with:
    pytest examples/basic_example.py -v

First run will be slow, subsequent runs will be fast!
"""

import pytest
import time
from pytest_fixture_cache import cached_fixture


@cached_fixture
@pytest.fixture
def expensive_api_call():
    """Simulates an expensive API call that takes 3 seconds"""
    print("\n[FIXTURE] Making expensive API call...")
    time.sleep(3)  # Simulate slow API
    return {
        "status": "success",
        "data": {"user_id": 123, "username": "testuser"},
        "timestamp": "2025-01-25T10:30:00Z"
    }


@cached_fixture
@pytest.fixture(scope="session")
def database_connection():
    """Simulates a database connection that takes 5 seconds to establish"""
    print("\n[FIXTURE] Establishing database connection...")
    time.sleep(5)  # Simulate slow DB connection
    return {
        "host": "localhost",
        "port": 5432,
        "database": "test_db",
        "connected": True
    }


def test_api_response_structure(expensive_api_call):
    """Test that API response has correct structure"""
    assert "status" in expensive_api_call
    assert expensive_api_call["status"] == "success"
    assert "data" in expensive_api_call


def test_api_response_data(expensive_api_call):
    """Test that API response data is valid"""
    data = expensive_api_call["data"]
    assert data["user_id"] == 123
    assert data["username"] == "testuser"


def test_database_connection(database_connection):
    """Test that database connection is established"""
    assert database_connection["connected"] is True
    assert database_connection["port"] == 5432


def test_database_details(database_connection):
    """Test database connection details"""
    assert database_connection["host"] == "localhost"
    assert database_connection["database"] == "test_db"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
