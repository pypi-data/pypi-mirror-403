.PHONY: install format lint typecheck test check all clean

install:
	uv sync

format:
	uv run ruff format src/ tests/

lint:
	uv run ruff check src/ tests/

typecheck:
	uv run ty check src/

test:
	uv run pytest tests/ -v

# Run all checks (what CI runs)
check: lint typecheck test
	uv run ruff format --check src/ tests/

# Format and run all checks
all: format check

clean:
	rm -rf dist/ .pytest_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
