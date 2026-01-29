.PHONY: test test-unit test-integration test-all lint format

# Run only unit tests (default)
test: test-unit

test-unit:
	uv run pytest tests/unit -v

# Run integration tests (requires Azure credentials)
test-integration:
	uv run pytest tests/integration -v -m integration

# Run all tests
test-all:
	uv run pytest tests -v

# Linting
lint:
	uv run ruff check src tests
	uv run mypy src

# Format code
format:
	uv run ruff format src tests
