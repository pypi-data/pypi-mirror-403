"""
Integration helpers for functional programming patterns.

Provides caching utilities for Result/Either monad types from
libraries like returns, result, etc.
"""

from typing import Callable, TypeVar, Any
from .storage import load_fixture_cache, save_fixture_cache


T = TypeVar('T')
E = TypeVar('E')


def cached_result(fixture_name: str, create_func: Callable[[], Any]) -> Any:
    """
    Helper to load from cache or create fixture for Result monad types.

    Works with Result types from libraries like:
    - returns.result.Result
    - result.Result
    - Other Result/Either monad implementations

    Args:
        fixture_name: Name of the fixture (for cache key)
        create_func: Function to create the fixture (returns Result[T, E])

    Returns:
        Result[T, E] - Either cached (wrapped in Success) or newly created

    Example:
        from returns.result import Result, Success
        from pytest_fixture_cache.monad import cached_result

        def create_order():
            return create_order_api_call()  # Returns Result[OrderInfo, str]

        # In a fixture or test
        result = cached_result("order_fixture", create_order)
        assert isinstance(result, Success)
        order = result.unwrap()

    Note:
        This function assumes the Result type has:
        - A Success class that wraps successful values
        - An unwrap() method to extract the value
        - Checks if result is instance of Success for caching

    For custom monad types, you may need to adapt this helper.
    """
    # Try to load from cache
    cached_data = load_fixture_cache(fixture_name)
    if cached_data is not None:
        # Cache hit - need to wrap back into Success
        # Import Success dynamically to avoid hard dependency
        try:
            from returns.result import Success
            return Success(cached_data)
        except ImportError:
            # If returns is not installed, try result library
            try:
                from result import Ok
                return Ok(cached_data)
            except ImportError:
                # No monad library found, return raw dict
                print(f"[CACHE WARNING] No Result monad library found, returning raw dict")
                return cached_data

    # Cache miss - create new result
    print(f"[CACHE MISS] Creating fixture '{fixture_name}'")
    result = create_func()

    # Try to save to cache if it's a successful Result
    try:
        # Try returns library first
        from returns.result import Success
        if isinstance(result, Success):
            save_fixture_cache(fixture_name, result.unwrap())
    except ImportError:
        try:
            # Try result library
            from result import Ok
            if isinstance(result, Ok):
                save_fixture_cache(fixture_name, result.unwrap())
        except ImportError:
            pass

    return result


def is_success(result: Any) -> bool:
    """
    Check if a result is a successful Result type.

    Works with multiple Result monad libraries.

    Args:
        result: Result object to check

    Returns:
        True if result is successful, False otherwise

    Example:
        >>> from returns.result import Success, Failure
        >>> is_success(Success(42))
        True
        >>> is_success(Failure("error"))
        False
    """
    try:
        from returns.result import Success
        if isinstance(result, Success):
            return True
    except ImportError:
        pass

    try:
        from result import Ok
        if isinstance(result, Ok):
            return True
    except ImportError:
        pass

    return False


def unwrap_result(result: Any) -> Any:
    """
    Unwrap a Result type to get the inner value.

    Works with multiple Result monad libraries.

    Args:
        result: Result object to unwrap

    Returns:
        Unwrapped value

    Example:
        >>> from returns.result import Success
        >>> unwrap_result(Success(42))
        42
    """
    if hasattr(result, 'unwrap'):
        return result.unwrap()
    elif hasattr(result, 'value'):
        return result.value
    else:
        # Not a Result type, return as-is
        return result
