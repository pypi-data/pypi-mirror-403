.PHONY: help install install-dev test lint format type-check clean build publish

help:
	@echo "Available commands:"
	@echo "  make install      - Install package"
	@echo "  make install-dev  - Install package with dev dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting checks"
	@echo "  make format       - Format code"
	@echo "  make type-check   - Run type checking"
	@echo "  make clean        - Clean build artifacts"
	@echo "  make build        - Build package"
	@echo "  make publish      - Build and upload to PyPI (requires TWINE_USERNAME/TWINE_PASSWORD)"

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

test:
	pytest

lint:
	flake8 owlab tests
	isort --check-only owlab tests
	black --check owlab tests

lint-fix:
	isort owlab tests
	black owlab tests

format:
	isort owlab tests
	black owlab tests

type-check:
	mypy owlab

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .coverage htmlcov

build:
	uv build

publish: clean build
	uv run --with twine twine upload dist/*
