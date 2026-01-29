# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Support for custom serialization backends (pickle, msgpack)
- Redis backend for distributed testing
- Cache warming utilities
- Performance benchmarking tools

## [0.1.0] - 2025-01-25

### Added
- Initial release
- `@cached_fixture` decorator for automatic fixture caching
- SQLite-based persistent storage
- Dirty/clean status tracking for cache invalidation
- Hit count statistics for cache effectiveness monitoring
- CLI options: `--clear-cache`, `--no-cache`, `--cache-stats`
- Programmatic API for cache management
- Result monad integration (`cached_result` helper)
- Session-scoped fixtures: `mark_dirty`, `clear_cache`
- Scope-aware caching (function/class/module/session)
- Configurable cache directory via `PYTEST_FIXTURE_CACHE_DIR`
- Comprehensive documentation and examples

### Features
- Zero-config setup (works out of the box)
- Automatic cache invalidation support
- JSON serialization for dict fixtures
- Thread-safe SQLite operations
- Pytest plugin integration

### Documentation
- Complete README with usage examples
- API documentation
- Example files for common use cases
- Performance benchmarks

[Unreleased]: https://github.com/yourusername/pytest-fixture-cache/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/pytest-fixture-cache/releases/tag/v0.1.0
