# Contributing to pytest-fixture-cache

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/pytest-fixture-cache.git
   cd pytest-fixture-cache
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install in development mode**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify installation**
   ```bash
   pytest tests/ -v
   pytest examples/ -v
   ```

## Project Structure

```
pytest-fixture-cache/
├── src/pytest_fixture_cache/
│   ├── __init__.py       # Public API exports
│   ├── storage.py        # SQLite backend
│   ├── decorator.py      # @cached_fixture
│   ├── plugin.py         # Pytest plugin
│   ├── utils.py          # Utilities
│   └── monad.py          # Result monad support
├── tests/                # Test suite
├── examples/             # Usage examples
├── pyproject.toml        # Package configuration
└── README.md             # Documentation
```

## Making Changes

### Code Style

We use:
- **Black** for code formatting (line length: 100)
- **Ruff** for linting
- **MyPy** for type checking (optional)

Run formatters:
```bash
black src/ tests/ examples/
ruff check src/ tests/ examples/
```

### Writing Tests

1. Add tests to `tests/` directory
2. Use descriptive test names: `test_<what>_<condition>`
3. Include docstrings explaining what the test verifies

Example:
```python
def test_cache_invalidation_marks_dirty():
    """Test that marking cache dirty prevents loading"""
    save_fixture_cache("test", {"data": "value"})
    mark_fixture_dirty("test")
    assert load_fixture_cache("test") is None
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_basic.py -v

# With coverage
pytest tests/ --cov=pytest_fixture_cache --cov-report=html
```

## Contribution Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write code
   - Add tests
   - Update documentation

4. **Ensure tests pass**
   ```bash
   pytest tests/ -v
   black src/ tests/
   ruff check src/ tests/
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request**
   - Go to GitHub
   - Click "New Pull Request"
   - Describe your changes

## Pull Request Guidelines

- **Title**: Clear, descriptive title (e.g., "Add Redis backend support")
- **Description**: Explain what changes you made and why
- **Tests**: Include tests for new features
- **Documentation**: Update README.md if adding user-facing features
- **Changelog**: Add entry to CHANGELOG.md under [Unreleased]

Example PR description:
```markdown
## Summary
Adds support for Redis as a cache backend.

## Changes
- Added `RedisStorage` class in `storage.py`
- Added `--cache-backend` CLI option
- Updated documentation with Redis examples

## Testing
- Added `tests/test_redis_backend.py`
- All existing tests pass
- Tested with Redis 7.0

## Documentation
- Updated README.md with Redis setup instructions
- Added example in `examples/redis_example.py`
```

## Feature Requests

Have an idea? Open an issue with:
- **Title**: "Feature: <description>"
- **Use case**: Why is this feature needed?
- **Proposal**: How should it work?
- **Examples**: Code examples if possible

## Bug Reports

Found a bug? Open an issue with:
- **Title**: "Bug: <description>"
- **Steps to reproduce**: How to trigger the bug
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Environment**: Python version, pytest version, OS

Example:
```markdown
## Bug: Cache not cleared with --clear-cache

**Steps to reproduce:**
1. Run `pytest --clear-cache`
2. Check cache stats with `pytest --cache-stats`
3. Cache entries still present

**Expected:** All cache entries should be deleted

**Actual:** Cache entries remain

**Environment:**
- Python 3.11
- pytest 7.4.0
- Ubuntu 22.04
```

## Development Tips

### Running Examples

```bash
# Run all examples
pytest examples/ -v

# Run specific example
pytest examples/basic_example.py -v

# Clear cache between runs
pytest examples/ -v --clear-cache
```

### Debugging

Enable verbose cache logging:
```python
# In your test
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing with Different Python Versions

```bash
# Using tox (if configured)
tox

# Or manually
python3.8 -m pytest tests/
python3.9 -m pytest tests/
python3.11 -m pytest tests/
```

## Code Review Process

1. Maintainer reviews PR
2. Feedback provided (if needed)
3. You make updates
4. Once approved, PR is merged

We aim to review PRs within 48 hours.

## Release Process

(For maintainers)

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. Build package: `python -m build`
6. Upload to PyPI: `twine upload dist/*`

## Questions?

- Open an issue with label "question"
- Email: your.email@example.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🎉
