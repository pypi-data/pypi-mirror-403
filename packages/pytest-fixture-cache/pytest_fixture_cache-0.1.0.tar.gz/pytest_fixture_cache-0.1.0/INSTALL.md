# Installation Guide

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation Methods

### Method 1: From PyPI (Recommended)

```bash
pip install pytest-fixture-cache
```

### Method 2: From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/pytest-fixture-cache.git
cd pytest-fixture-cache

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

### Method 3: From Source with Development Dependencies

```bash
# Clone and install with dev tools
git clone https://github.com/yourusername/pytest-fixture-cache.git
cd pytest-fixture-cache
pip install -e ".[dev]"
```

## Optional Dependencies

### Result Monad Support

For functional programming with Result types:

```bash
pip install pytest-fixture-cache[monad]
```

This installs the `returns` library for Result monad support.

### Development Tools

For contributing:

```bash
pip install pytest-fixture-cache[dev]
```

This installs:
- pytest with coverage
- black (code formatter)
- ruff (linter)
- mypy (type checker)

## Verify Installation

After installation, verify everything works:

```bash
# Run verification script
python verify_install.py

# Or manually test
python -c "import pytest_fixture_cache; print(pytest_fixture_cache.__version__)"

# Check pytest recognizes the plugin
pytest --help | grep cache
```

You should see:
```
fixture-cache:
  --clear-cache         Clear all fixture caches before running tests
  --no-cache            Disable fixture caching for this test run
  --cache-stats         Show fixture cache statistics and exit
```

## Quick Test

Create a test file `test_quick.py`:

```python
import pytest
from pytest_fixture_cache import cached_fixture

@cached_fixture
@pytest.fixture
def my_fixture():
    return {"hello": "world"}

def test_it_works(my_fixture):
    assert my_fixture["hello"] == "world"
```

Run it:

```bash
pytest test_quick.py -v
```

You should see `[CACHE MISS]` on first run, and `[CACHE HIT]` on subsequent runs.

## Troubleshooting

### Issue: "No module named 'pytest_fixture_cache'"

**Solution:**
```bash
# Ensure pip installed correctly
pip list | grep pytest-fixture-cache

# Try reinstalling
pip uninstall pytest-fixture-cache
pip install pytest-fixture-cache
```

### Issue: Plugin not recognized by pytest

**Solution:**
```bash
# Check pytest version (needs 7.0+)
pytest --version

# Upgrade pytest if needed
pip install --upgrade pytest

# Verify plugin entry point
pip show pytest-fixture-cache
```

### Issue: Permission errors when creating cache

**Solution:**
```bash
# Check permissions
ls -la .pytest_cache/

# Or use custom cache directory
export PYTEST_FIXTURE_CACHE_DIR="/tmp/pytest_cache"
pytest
```

### Issue: Cache not being created

**Solution:**
1. Ensure fixture returns a dict:
   ```python
   @cached_fixture
   @pytest.fixture
   def my_fixture():
       return {"key": "value"}  # ✓ Works
       # return "string"         # ✗ Won't cache
   ```

2. Check for `--no-cache` flag
   ```bash
   # Remove --no-cache if present
   pytest  # Not: pytest --no-cache
   ```

## Upgrading

### From PyPI

```bash
pip install --upgrade pytest-fixture-cache
```

### From Source

```bash
cd pytest-fixture-cache
git pull
pip install --upgrade -e .
```

## Uninstalling

```bash
pip uninstall pytest-fixture-cache

# Also remove cache directory if desired
rm -rf .pytest_cache/fixtures/
```

## Next Steps

1. Read [QUICKSTART.md](QUICKSTART.md) for basic usage
2. Try examples in `examples/` directory
3. Read full documentation in [README.md](README.md)

## Getting Help

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Open an issue: https://github.com/yourusername/pytest-fixture-cache/issues
- Email: your.email@example.com
