.PHONY: all sync test lint format typecheck qa \
		wheel sdist dist check publish-test publish clean

all: qa

sync:
	@uv sync

test:
	@uv run pytest tests/ -v

lint:
	@uv run ruff check --fix linkdb.py tests/

format:
	@uv run ruff format linkdb.py tests/

typecheck:
	@uv run mypy --strict linkdb.py

# Run a full quality assurance check
qa: sync test lint typecheck format

# Build wheel
wheel:
	@uv build --wheel

# Build source distribution
sdist:
	@uv build --sdist

# Build both wheel and sdist
dist: wheel sdist check

# Check distributions with twine
check:
	@uv run twine check dist/*

# Publish to TestPyPI
publish-test: check
	@uv run twine upload --repository testpypi dist/*

# Publish to PyPI
publish: check
	@uv run twine upload dist/*

clean:
	@rm -rf __pycache__ .pytest_cache *.db
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
