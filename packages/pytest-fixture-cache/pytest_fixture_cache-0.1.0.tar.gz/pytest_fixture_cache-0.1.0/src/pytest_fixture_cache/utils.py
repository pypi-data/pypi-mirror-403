"""
Utility functions for programmatic cache operations.

Provides helper functions for batch cache operations and management.
"""

from typing import List
from .storage import _get_cache_db_path, clear_fixture_cache as _clear_single
import sqlite3


def clear_fixtures(fixture_names: List[str], verbose: bool = True) -> int:
    """
    Clear specific fixtures from the cache database.

    Args:
        fixture_names: List of fixture names to clear
        verbose: Whether to print status messages

    Returns:
        Number of cache entries deleted

    Example:
        >>> clear_fixtures(['fixture1', 'fixture2'])
        2
    """
    cache_db = _get_cache_db_path()

    if not cache_db.exists():
        if verbose:
            print("[CACHE] No cache database found, nothing to clear")
        return 0

    try:
        conn = sqlite3.connect(cache_db)
        cursor = conn.cursor()

        total_deleted = 0
        for fixture_name in fixture_names:
            cursor.execute("DELETE FROM fixture_cache WHERE fixtureName = ?", (fixture_name,))
            total_deleted += cursor.rowcount

        conn.commit()
        conn.close()

        if verbose and total_deleted > 0:
            print(f"\n[CACHE] Cleared {total_deleted} cache entries for {len(fixture_names)} fixtures")

        return total_deleted

    except Exception as e:
        if verbose:
            print(f"\n[CACHE WARNING] Failed to clear cache: {e}")
        return 0


def clear_all_fixtures(verbose: bool = True) -> int:
    """
    Clear all fixtures from the cache database.

    Args:
        verbose: Whether to print status messages

    Returns:
        Number of cache entries deleted

    Example:
        >>> clear_all_fixtures()
        5
    """
    cache_db = _get_cache_db_path()

    if not cache_db.exists():
        if verbose:
            print("[CACHE] No cache database found, nothing to clear")
        return 0

    try:
        conn = sqlite3.connect(cache_db)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM fixture_cache")
        total_deleted = cursor.rowcount

        conn.commit()
        conn.close()

        if verbose and total_deleted > 0:
            print(f"\n[CACHE] Cleared all {total_deleted} cache entries")

        return total_deleted

    except Exception as e:
        if verbose:
            print(f"\n[CACHE WARNING] Failed to clear cache: {e}")
        return 0
