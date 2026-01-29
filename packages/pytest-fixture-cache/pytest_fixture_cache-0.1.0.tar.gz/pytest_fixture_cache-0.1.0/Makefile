.PHONY: help install test format lint clean build publish

help:
	@echo "pytest-fixture-cache - Development Commands"
	@echo ""
	@echo "install      Install package in development mode"
	@echo "test         Run tests"
	@echo "format       Format code with black"
	@echo "lint         Run linters (ruff)"
	@echo "clean        Remove build artifacts"
	@echo "build        Build distribution packages"
	@echo "publish      Publish to PyPI (requires twine)"
	@echo "examples     Run example tests"
	@echo "stats        Show cache statistics"

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=pytest_fixture_cache --cov-report=html --cov-report=term

format:
	black src/ tests/ examples/
	@echo "Code formatted with black"

lint:
	ruff check src/ tests/ examples/
	@echo "Linting complete"

type-check:
	mypy src/pytest_fixture_cache/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "Cleaned build artifacts"

build:
	python -m build
	@echo "Build complete - check dist/ directory"

publish: clean build
	twine upload dist/*
	@echo "Published to PyPI"

publish-test: clean build
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*
	@echo "Published to Test PyPI"

examples:
	pytest examples/ -v

examples-clean:
	pytest examples/ -v --clear-cache

stats:
	pytest --cache-stats

all: format lint test
	@echo "All checks passed!"
