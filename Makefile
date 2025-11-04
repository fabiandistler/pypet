# Makefile for pypet development

.PHONY: help install test lint format type-check clean hooks dev all

# Default target
help:
	@echo "pypet Development Commands:"
	@echo ""
	@echo "  make install     Install package in development mode"
	@echo "  make hooks       Install pre-push git hooks" 
	@echo "  make test        Run all tests"
	@echo "  make lint        Run linting checks (ruff + black)"
	@echo "  make format      Auto-format code with black and ruff"
	@echo "  make type-check  Run type checking with mypy"
	@echo "  make clean       Clean build artifacts and cache files"
	@echo "  make dev         Set up development environment"
	@echo "  make all         Run all checks (format + lint + test)"
	@echo ""
	@echo "Environment variables:"
	@echo "  SKIP_TESTS=1     Skip tests in hooks and all target"

# Install package in development mode
install:
	uv pip install -e ".[dev]"

# Install git hooks
hooks:
	@./scripts/install-hooks.sh

# Run tests
test:
	uv run python -m pytest tests/ -v

# Quick test for CI/hooks
test-quick:
	uv run python -m pytest tests/ -x --tb=short -q

# Run linting checks
lint:
	@echo "🔍 Running Black formatter check..."
	uv run python -m black --check pypet tests
	@echo "🔍 Running Ruff linting check..."  
	uv run python -m ruff check pypet tests

# Auto-format code
format:
	@echo "✨ Formatting code with Black..."
	uv run python -m black pypet tests
	@echo "🔧 Auto-fixing with Ruff..."
	uv run python -m ruff check pypet tests --fix

# Type checking
type-check:
	@echo "🎯 Running mypy type checking..."
	uv run python -m mypy pypet --ignore-missing-imports || true

# Clean build artifacts and cache files
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache

# Set up development environment
dev: install hooks
	@echo "🎉 Development environment ready!"
	@echo ""
	@echo "Next steps:"
	@echo "  - Run 'make test' to run tests"
	@echo "  - Run 'make format' to format code"
	@echo "  - Run 'make lint' to check linting"
	@echo "  - Git hooks are installed and will run on push"

# Run all checks
all: format lint
ifndef SKIP_TESTS
	@$(MAKE) test-quick
endif
	@echo "✅ All checks passed!"

# Test the CLI locally
cli-test:
	uv run python -m pypet.cli --help
	uv run python -m pypet.cli list

# Build package
build: clean
	uv build

# Install from local build
install-local: build
	pip install dist/*.whl --force-reinstall