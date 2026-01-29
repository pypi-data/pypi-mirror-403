.PHONY: install sync test clean run help

# Default target
help:
	@echo "Available commands:"
	@echo "  make install    - Install package in editable mode"
	@echo "  make sync       - Sync dependencies with uv (recommended)"
	@echo "  make sync-dev   - Sync with dev dependencies"
	@echo "  make test       - Run translation on test input"
	@echo "  make run        - Run with custom input/output (INPUT=file.srt OUTPUT=out.srt)"
	@echo "  make clean      - Remove generated files"
	@echo "  make lint       - Run ruff linter"
	@echo "  make format     - Format code with ruff"

# Install package in editable mode
install:
	uv pip install -e .

# Sync dependencies (recommended)
sync:
	uv sync

# Sync with dev dependencies
sync-dev:
	uv sync --group dev

# Test translation with sample input
test: sync
	uv run srt-translate input.srt output.srt

# Run with custom files
run: sync
	@if [ -z "$(INPUT)" ] || [ -z "$(OUTPUT)" ]; then \
		echo "Usage: make run INPUT=input.srt OUTPUT=output.srt"; \
		exit 1; \
	fi
	uv run srt-translate $(INPUT) $(OUTPUT)

# Lint code
lint:
	uv run ruff check .

# Format code
format:
	uv run ruff format .

# Clean generated files
clean:
	rm -f output.srt
	rm -rf .venv
	rm -rf *.egg-info
	rm -rf __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
