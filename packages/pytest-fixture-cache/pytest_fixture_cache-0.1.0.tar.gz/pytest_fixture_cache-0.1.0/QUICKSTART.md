# Quick Start Guide

Get started with pytest-fixture-cache in 5 minutes!

## Installation

```bash
pip install pytest-fixture-cache
```

## Basic Example

Create a test file `test_example.py`:

```python
import pytest
import time
from pytest_fixture_cache import cached_fixture

@cached_fixture
@pytest.fixture
def slow_fixture():
    """This takes 5 seconds normally, but will be cached"""
    time.sleep(5)  # Simulate expensive operation
    return {"data": "cached value"}

def test_using_cached_fixture(slow_fixture):
    assert slow_fixture["data"] == "cached value"
```

## Run Tests

```bash
# First run - creates cache (slow)
pytest test_example.py -v
# Takes 5 seconds

# Second run - uses cache (fast!)
pytest test_example.py -v
# Takes <0.1 seconds
```

## View Cache Stats

```bash
pytest --cache-stats
```

Output:
```
================================================================================
FIXTURE CACHE STATISTICS
================================================================================

Found 1 cached fixture(s):

Fixture: slow_fixture
  Scope:   function
  Status:  clean
  Hits:    1
  Created: 2025-01-25 10:30:15
  Updated: 2025-01-25 10:30:15
================================================================================
```

## Clear Cache

```bash
# Clear all caches
pytest --clear-cache

# Or disable caching for one run
pytest --no-cache
```

## Next Steps

1. **Read the full README**: [README.md](README.md)
2. **Try examples**: Check `examples/` directory
3. **Learn advanced features**: Result monad support, cache invalidation
4. **Integrate into your project**: Add to your test suite

## Common Use Cases

### API Testing
```python
@cached_fixture
@pytest.fixture(scope="session")
def api_token():
    """Cache auth token for all tests"""
    return get_auth_token()  # Expensive API call
```

### Database Setup
```python
@cached_fixture
@pytest.fixture(scope="module")
def seeded_db():
    """Cache seeded database"""
    db = setup_database()
    db.seed_test_data()  # Expensive!
    return db
```

### File Generation
```python
@cached_fixture
@pytest.fixture
def test_file():
    """Cache generated file"""
    return generate_large_file()  # Expensive!
```

## Need Help?

- Check [examples/](examples/) directory
- Read [README.md](README.md) for full documentation
- Open an issue on GitHub

Happy testing! 🚀
