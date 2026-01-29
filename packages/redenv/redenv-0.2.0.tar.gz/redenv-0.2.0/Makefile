.PHONY: install test lint build clean example example-sync

# Install the package in editable mode with dev dependencies
install:
	pip install -e ".[dev]"

# Run tests
test:
	PYTHONPATH=src python -m pytest

# Run linting and type checking
lint:
	python -m ruff check src tests
	python -m pyright src

# Build the package artifacts
build:
	rm -rf dist/ build/
	python -m build

# Clean up build artifacts and caches
clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
