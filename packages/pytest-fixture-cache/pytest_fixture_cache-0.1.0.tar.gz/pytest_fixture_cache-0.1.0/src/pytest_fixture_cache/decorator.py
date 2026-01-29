"""
Decorator for caching pytest fixtures.

Provides @cached_fixture decorator that automatically caches
fixture results to SQLite storage.
"""

import functools
from typing import Callable, Any

from .storage import save_fixture_cache, load_fixture_cache


def cached_fixture(func: Callable) -> Callable:
    """
    Decorator to cache pytest fixture results in SQLite.

    Only caches if:
    - Fixture returns a dict
    - Caching is not disabled (--no-cache flag)
    - Cache is clean (not marked dirty)

    Args:
        func: Pytest fixture function to wrap

    Returns:
        Wrapped fixture function with caching logic

    Example:
        @cached_fixture
        @pytest.fixture
        def expensive_fixture():
            # Expensive API calls, database setup, etc.
            return {"data": "value"}

    How it works:
        1. Check if cache exists and is clean
        2. If yes, return cached data (fast!)
        3. If no, execute fixture function (slow)
        4. Save result to cache
        5. Return result

    The decorator respects:
        - Pytest fixture scope (function, class, module, session)
        - --no-cache flag (disable caching)
        - Dirty status (recreate if marked dirty)
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get fixture name
        fixture_name = func.__name__

        # Check if caching is disabled via pytest config
        # The 'request' fixture is automatically passed to fixtures by pytest
        request = kwargs.get('request')
        if request and hasattr(request.config, 'option'):
            if getattr(request.config.option, 'no_cache', False):
                print(f"[CACHE] Caching disabled, executing '{fixture_name}'")
                return func(*args, **kwargs)

        # Try to load from cache
        cached_data = load_fixture_cache(fixture_name)
        if cached_data is not None:
            # Cache hit! Return cached data
            return cached_data

        # Cache miss - execute fixture function
        print(f"[CACHE MISS] Executing fixture '{fixture_name}'")
        result = func(*args, **kwargs)

        # Save to cache if result is a dict
        if isinstance(result, dict):
            # Determine fixture scope
            fixture_scope = "function"  # Default scope
            if hasattr(func, '_pytestfixturefunction'):
                scope_obj = getattr(func._pytestfixturefunction, 'scope', None)
                if scope_obj:
                    fixture_scope = scope_obj

            # Save to cache
            save_fixture_cache(fixture_name, result, scope=fixture_scope)
        else:
            print(f"[CACHE] Skipping cache for '{fixture_name}' (not a dict, type: {type(result).__name__})")

        return result

    return wrapper
