.PHONY: help install install-dev test test-v lint format typecheck check clean license-headers

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install         Install package"
	@echo "  install-dev     Install package with dev dependencies"
	@echo "  test            Run tests"
	@echo "  test-v          Run tests (verbose)"
	@echo "  lint            Run ruff linter"
	@echo "  format          Format code with ruff"
	@echo "  typecheck       Run mypy type checker"
	@echo "  check           Run lint, typecheck, and test"
	@echo "  license-headers Add license headers to source files"
	@echo "  clean           Remove build artifacts"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest

test-v:
	pytest -v

lint:
	ruff check dotfiles tests

format:
	ruff format dotfiles tests

typecheck:
	mypy

check: lint typecheck test

license-headers:
	go run github.com/google/addlicense@latest -c "Riley Rice" -l apache -ignore "files/**" .

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
