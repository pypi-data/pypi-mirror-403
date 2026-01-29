"""
Fixture cache storage backend using SQLite.

Provides persistent caching for pytest fixtures with status tracking,
hit counts, and scope management.
"""

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional
from contextlib import contextmanager


def _get_cache_dir() -> Path:
    """
    Get the cache directory path.

    Checks in order:
    1. PYTEST_FIXTURE_CACHE_DIR environment variable
    2. .pytest_cache/fixtures (default)

    Returns:
        Path to cache directory
    """
    env_dir = os.getenv("PYTEST_FIXTURE_CACHE_DIR")
    if env_dir:
        return Path(env_dir)

    # Default: use pytest's cache directory
    return Path(".pytest_cache/fixtures")


def _get_cache_db_path() -> Path:
    """Get the cache database file path"""
    return _get_cache_dir() / "cache.db"


def _ensure_cache_dir():
    """Ensure cache directory exists"""
    _get_cache_dir().mkdir(parents=True, exist_ok=True)


def _init_db():
    """Initialize cache database and create table if not exists"""
    _ensure_cache_dir()

    cache_db = _get_cache_db_path()
    conn = sqlite3.connect(str(cache_db))
    conn.row_factory = sqlite3.Row  # Return rows as dict-like objects

    # Create table if not exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fixture_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fixtureName TEXT NOT NULL UNIQUE,
            fixtureScope TEXT NOT NULL DEFAULT 'function',
            fixtureData TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'clean' CHECK(status IN ('clean', 'dirty')),
            createdAt TEXT NOT NULL DEFAULT (datetime('now')),
            updatedAt TEXT NOT NULL DEFAULT (datetime('now')),
            hitCount INTEGER NOT NULL DEFAULT 0
        )
    """)

    # Create indexes
    conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON fixture_cache(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON fixture_cache(createdAt)")

    conn.commit()
    return conn


@contextmanager
def _get_connection():
    """Get SQLite connection as context manager"""
    conn = _init_db()
    try:
        yield conn
    finally:
        conn.close()


def save_fixture_cache(name: str, data: dict[str, Any], scope: str = "function") -> bool:
    """
    Save or update fixture cache in SQLite.

    Args:
        name: Fixture name (e.g., 'my_expensive_fixture')
        data: Fixture result dict to cache (must be JSON-serializable)
        scope: Pytest scope (function, class, module, session)

    Returns:
        True if successful, False otherwise

    Example:
        >>> save_fixture_cache("my_fixture", {"data": "value"})
        True
    """
    try:
        # Serialize data to JSON
        json_data = json.dumps(data, ensure_ascii=False)

        with _get_connection() as conn:
            # Insert or replace
            conn.execute("""
                INSERT INTO fixture_cache (fixtureName, fixtureScope, fixtureData, status, hitCount)
                VALUES (?, ?, ?, 'clean', 0)
                ON CONFLICT(fixtureName) DO UPDATE SET
                    fixtureData = excluded.fixtureData,
                    fixtureScope = excluded.fixtureScope,
                    status = 'clean',
                    updatedAt = datetime('now')
            """, (name, scope, json_data))

            conn.commit()
            print(f"[CACHE SAVED] Fixture '{name}' cached successfully")
            return True

    except Exception as e:
        print(f"[CACHE ERROR] Failed to save fixture cache '{name}': {e}")
        return False


def load_fixture_cache(name: str) -> Optional[dict[str, Any]]:
    """
    Load fixture cache from SQLite if clean.

    Args:
        name: Fixture name

    Returns:
        Cached fixture data dict, or None if not found or dirty

    Example:
        >>> data = load_fixture_cache("my_fixture")
        >>> if data:
        ...     print(f"Loaded: {data}")
    """
    try:
        with _get_connection() as conn:
            cursor = conn.execute("""
                SELECT fixtureData, status
                FROM fixture_cache
                WHERE fixtureName = ?
            """, (name,))

            result = cursor.fetchone()

            if not result:
                return None

            # Check if cache is clean
            if result['status'] != 'clean':
                print(f"[CACHE] Fixture '{name}' is dirty, skipping cache")
                return None

            # Increment hit count
            conn.execute("""
                UPDATE fixture_cache
                SET hitCount = hitCount + 1
                WHERE fixtureName = ?
            """, (name,))
            conn.commit()

            # Deserialize JSON data
            data = json.loads(result['fixtureData'])
            print(f"[CACHE HIT] Loaded fixture '{name}' from cache")
            return data

    except Exception as e:
        print(f"[CACHE ERROR] Failed to load fixture cache '{name}': {e}")
        return None


def mark_fixture_dirty(name: Optional[str] = None) -> bool:
    """
    Mark fixture cache as dirty (invalid).

    When a fixture is marked dirty, it will be recreated on next test run
    instead of being loaded from cache.

    Args:
        name: Fixture name, or None to mark ALL fixtures dirty

    Returns:
        True if successful, False otherwise

    Example:
        >>> # Mark specific fixture dirty
        >>> mark_fixture_dirty("my_fixture")
        True

        >>> # Mark all fixtures dirty
        >>> mark_fixture_dirty()
        True
    """
    try:
        with _get_connection() as conn:
            if name is None:
                # Mark ALL fixtures dirty
                cursor = conn.execute("""
                    UPDATE fixture_cache
                    SET status = 'dirty'
                    WHERE status = 'clean'
                """)
            else:
                # Mark specific fixture dirty
                cursor = conn.execute("""
                    UPDATE fixture_cache
                    SET status = 'dirty'
                    WHERE fixtureName = ?
                """, (name,))

            affected = cursor.rowcount
            conn.commit()

            target = f"'{name}'" if name else "all fixtures"
            print(f"[CACHE] Marked {target} dirty ({affected} rows affected)")
            return True

    except Exception as e:
        print(f"[CACHE ERROR] Failed to mark fixture dirty: {e}")
        return False


def mark_fixture_clean(name: str) -> bool:
    """
    Mark fixture cache as clean (valid).

    This is useful if you manually recreated data and want to mark it clean
    without going through save_fixture_cache.

    Args:
        name: Fixture name

    Returns:
        True if successful, False otherwise

    Example:
        >>> mark_fixture_clean("my_fixture")
        True
    """
    try:
        with _get_connection() as conn:
            cursor = conn.execute("""
                UPDATE fixture_cache
                SET status = 'clean'
                WHERE fixtureName = ?
            """, (name,))

            affected = cursor.rowcount
            conn.commit()

            if affected > 0:
                print(f"[CACHE] Marked '{name}' clean")
                return True
            else:
                print(f"[CACHE] Fixture '{name}' not found in cache")
                return False

    except Exception as e:
        print(f"[CACHE ERROR] Failed to mark fixture clean: {e}")
        return False


def clear_fixture_cache(name: Optional[str] = None) -> bool:
    """
    Delete fixture cache from SQLite.

    Args:
        name: Fixture name, or None to clear ALL caches

    Returns:
        True if successful, False otherwise

    Example:
        >>> # Clear specific fixture
        >>> clear_fixture_cache("my_fixture")
        True

        >>> # Clear all fixtures
        >>> clear_fixture_cache()
        True
    """
    try:
        with _get_connection() as conn:
            if name is None:
                # Clear ALL caches
                cursor = conn.execute("DELETE FROM fixture_cache")
            else:
                # Clear specific cache
                cursor = conn.execute("""
                    DELETE FROM fixture_cache
                    WHERE fixtureName = ?
                """, (name,))

            affected = cursor.rowcount
            conn.commit()

            target = f"'{name}'" if name else "all fixtures"
            print(f"[CACHE] Cleared {target} ({affected} rows affected)")
            return True

    except Exception as e:
        print(f"[CACHE ERROR] Failed to clear fixture cache: {e}")
        return False


def get_cache_stats() -> list[dict[str, Any]]:
    """
    Get cache statistics for all fixtures.

    Returns:
        List of cache entries with stats (fixture name, status, hit count, timestamps)

    Example:
        >>> stats = get_cache_stats()
        >>> for entry in stats:
        ...     print(f"{entry['fixtureName']}: {entry['status']} (hits: {entry['hitCount']})")
    """
    try:
        with _get_connection() as conn:
            cursor = conn.execute("""
                SELECT
                    fixtureName,
                    fixtureScope,
                    status,
                    hitCount,
                    createdAt,
                    updatedAt
                FROM fixture_cache
                ORDER BY fixtureName
            """)

            # Convert Row objects to dicts
            return [dict(row) for row in cursor.fetchall()]

    except Exception as e:
        print(f"[CACHE ERROR] Failed to get cache stats: {e}")
        return []


def get_cache_location() -> Path:
    """
    Get the cache database file path.

    Returns:
        Path to cache.db file

    Example:
        >>> cache_path = get_cache_location()
        >>> print(f"Cache stored at: {cache_path}")
    """
    return _get_cache_db_path()
