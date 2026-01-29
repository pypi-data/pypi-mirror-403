"""
Example using Result monad with pytest-fixture-cache

Requires: pip install pytest-fixture-cache[monad]

Run with:
    pytest examples/monad_example.py -v
"""

import pytest
from returns.result import Result, Success, Failure
from pytest_fixture_cache.monad import cached_result


def create_user() -> Result[dict, str]:
    """
    Simulates creating a user via API.
    Returns Result[UserInfo, ErrorMessage]
    """
    import time
    print("\n[API] Creating user...")
    time.sleep(2)  # Simulate API call

    # Simulate successful user creation
    user_info = {
        "user_id": "usr_12345",
        "username": "testuser",
        "email": "test@example.com",
        "created": True
    }
    return Success(user_info)


def create_order(user_id: str) -> Result[dict, str]:
    """
    Simulates creating an order via API.
    Returns Result[OrderInfo, ErrorMessage]
    """
    import time
    print(f"\n[API] Creating order for user {user_id}...")
    time.sleep(2)  # Simulate API call

    order_info = {
        "order_id": "ord_67890",
        "user_id": user_id,
        "status": "pending",
        "total": 99.99
    }
    return Success(order_info)


@pytest.fixture
def user():
    """Cached user fixture using Result monad"""
    result = cached_result("user_fixture", create_user)

    # Verify it's a Success
    assert isinstance(result, Success), f"User creation failed: {result}"

    # Unwrap and return
    return result.unwrap()


@pytest.fixture
def order(user):
    """Cached order fixture that depends on user"""
    def create():
        return create_order(user["user_id"])

    result = cached_result("order_fixture", create)

    # Verify it's a Success
    assert isinstance(result, Success), f"Order creation failed: {result}"

    return result.unwrap()


def test_user_created(user):
    """Test that user was created successfully"""
    assert user["created"] is True
    assert user["user_id"].startswith("usr_")
    assert user["username"] == "testuser"


def test_user_email(user):
    """Test user email is valid"""
    assert "@" in user["email"]
    assert user["email"] == "test@example.com"


def test_order_created(order):
    """Test that order was created successfully"""
    assert order["status"] == "pending"
    assert order["order_id"].startswith("ord_")


def test_order_belongs_to_user(user, order):
    """Test that order is associated with user"""
    assert order["user_id"] == user["user_id"]


def test_order_total(order):
    """Test order has valid total"""
    assert order["total"] > 0
    assert isinstance(order["total"], (int, float))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
