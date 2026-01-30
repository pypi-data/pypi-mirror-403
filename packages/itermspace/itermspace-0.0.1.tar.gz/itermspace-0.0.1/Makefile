.PHONY: install lint test clean pre-commit typecheck deadcode

install:
	uv sync --all-groups
	uv run pre-commit install

lint:
	uv run ruff check src tests --fix
	uv run ruff format src tests

typecheck:
	uv run ty check src

deadcode:
	uv run vulture

test:
	uv run pytest tests -v

pre-commit:
	uv run pre-commit run --all-files

clean:
	rm -rf dist build *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
