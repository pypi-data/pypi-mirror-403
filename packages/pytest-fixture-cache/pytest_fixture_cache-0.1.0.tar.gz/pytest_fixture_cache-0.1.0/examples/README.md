# Examples

This directory contains example usage of pytest-fixture-cache.

## Available Examples

### 1. basic_example.py
Basic usage demonstrating:
- `@cached_fixture` decorator
- Expensive fixture caching
- Session vs function scope
- Cache hit/miss behavior

**Run it:**
```bash
pytest examples/basic_example.py -v

# First run: slow (creates cache)
# Second run: fast (uses cache)
```

### 2. monad_example.py
Functional programming with Result monads:
- Result type integration
- `cached_result()` helper
- Chaining cached fixtures
- Error handling with Success/Failure

**Requires:** `pip install pytest-fixture-cache[monad]`

**Run it:**
```bash
pytest examples/monad_example.py -v
```

### 3. cache_management_example.py
Advanced cache management:
- Marking fixtures dirty
- Clearing cache programmatically
- Using `mark_dirty` and `clear_cache` fixtures
- When NOT to cache

**Run it:**
```bash
pytest examples/cache_management_example.py -v
```

## Running All Examples

```bash
# Run all examples
pytest examples/ -v

# Clear cache first
pytest examples/ -v --clear-cache

# Show cache stats after running
pytest examples/ -v && pytest --cache-stats
```

## Experiment with Cache

### See Cache in Action

```bash
# First run - slow
pytest examples/basic_example.py -v
# Note the timing

# Second run - fast
pytest examples/basic_example.py -v
# Much faster!

# Check cache stats
pytest --cache-stats
```

### Test Cache Invalidation

```bash
# Run test
pytest examples/cache_management_example.py::test_modify_database_and_invalidate -v

# Cache is now dirty, next run will recreate
pytest examples/cache_management_example.py::test_database_seeded -v
```

### Clear and Restart

```bash
# Clear all caches
pytest --clear-cache

# Run fresh
pytest examples/ -v
```

## Create Your Own

Use these examples as templates for your own tests:

```python
import pytest
from pytest_fixture_cache import cached_fixture

@cached_fixture
@pytest.fixture
def your_expensive_fixture():
    # Your expensive setup here
    return {"your": "data"}

def test_your_feature(your_expensive_fixture):
    # Your test here
    assert your_expensive_fixture["your"] == "data"
```

## Tips

1. **Check cache output**: Look for `[CACHE HIT]` and `[CACHE MISS]` messages
2. **Monitor timing**: Use `-v` to see how much time is saved
3. **Use cache stats**: Run `pytest --cache-stats` to see cache effectiveness
4. **Clear when needed**: Use `--clear-cache` to start fresh

## Questions?

- Read the main [README.md](../README.md)
- Check [QUICKSTART.md](../QUICKSTART.md)
- Open an issue on GitHub
