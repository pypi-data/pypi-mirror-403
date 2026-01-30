.PHONY: install install-dev lint format test test-cov build clean docs docs-serve help

PYTHON := python3
PIP := pip

help:
	@echo "pycewl - Python async CeWL implementation"
	@echo ""
	@echo "Commands:"
	@echo "  make install      Install package"
	@echo "  make install-dev  Install with dev dependencies"
	@echo "  make lint         Run ruff and mypy"
	@echo "  make format       Format code with ruff"
	@echo "  make test         Run tests"
	@echo "  make test-cov     Run tests with coverage"
	@echo "  make build        Build package"
	@echo "  make clean        Remove build artifacts"
	@echo "  make docs         Build documentation"
	@echo "  make docs-serve   Serve documentation locally"

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[all]"

lint:
	ruff check src tests
	ruff format --check src tests
	mypy src

format:
	ruff check --fix src tests
	ruff format src tests

test:
	pytest tests/

test-cov:
	pytest tests/ --cov=pycewl --cov-report=term-missing --cov-report=html

build:
	$(PYTHON) -m build

clean:
	rm -rf build/ dist/ *.egg-info src/*.egg-info
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	rm -rf htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

docs:
	mkdocs build

docs-serve:
	mkdocs serve
