.PHONY: help check vermin check-deps ruff format build clean install test

# Default target
help:
	@echo "Available targets:"
	@echo "  make check      - Run all checks (vermin + deps + ruff)"
	@echo "  make vermin     - Check Python version compatibility (code only)"
	@echo "  make check-deps - Check dependencies' Python version requirements"
	@echo "  make ruff       - Run ruff linter"
	@echo "  make format     - Format code with ruff"
	@echo "  make build      - Build package"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make install    - Install package locally"
	@echo "  make test       - Run tests (if available)"

# Run all checks
check: vermin check-deps ruff
	@echo "✓ All checks passed!"

# Check Python version compatibility (code only)
vermin:
	@echo "Checking Python version compatibility (code only)..."
	@uvx vermin commit_with_ai.py
	@echo ""

# Check dependencies' Python version requirements
check-deps:
	@scripts/check-deps-versions.sh

# Run ruff linter
ruff:
	@echo "Running ruff linter..."
	@ruff check commit_with_ai.py || { \
		echo ""; \
		echo "⚠️  Ruff found fixable issues. Run 'make format' to auto-fix."; \
		exit 1; \
	}
	@echo "✓ Ruff check passed!"
	@echo ""

# Format code with ruff
format:
	@echo "Formatting code with ruff..."
	@ruff format commit_with_ai.py
	@ruff check --fix commit_with_ai.py
	@echo "✓ Code formatted!"

# Build package
build:
	@echo "Building package..."
	@rm -rf dist/
	@uv build
	@echo "✓ Build complete!"
	@ls -lh dist/

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf dist/ build/ *.egg-info __pycache__ .ruff_cache
	@echo "✓ Clean complete!"

# Install package locally (with dev dependencies)
install:
	@echo "Syncing dependencies and installing package..."
	@uv sync --extra dev
	@echo "✓ Installation complete!"

# Run tests (placeholder)
test:
	@echo "Running tests..."
	@echo "⚠️  No tests configured yet"
	@echo "Add pytest tests in tests/ directory"
