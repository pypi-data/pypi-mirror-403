.PHONY: install dev test lint format clean build publish version tag sync

install:
	@uv sync --no-dev

dev: install
	@uv sync --extra dev

sync: install
	@uv sync --extra dev

pre-commit: dev
	@uv run ruff check --fix src/ tests/
	@uv run black src/ tests/
	@uv run mypy src/
	@uv run pytest
	@echo "Pre-commit checks passed."

test: dev
	@uv run pytest tests/ -v --cov=tyko --cov-report=html

clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .venv/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	@uv build

publish: build
	@uv publish

version:
	@python -c "from src.tyko.__version__ import __version__; print(__version__)"

docs-serve:
	@uv run --extra docs mkdocs serve

docs-build:
	@uv run --extra docs mkdocs build

docs-deploy:
	@uv run --extra docs mkdocs gh-deploy

# Helper to create a release tag
tag:
	@echo "Current version: $$(python -c 'from src.tyko.__version__ import __version__; print(__version__)')"
	@read -p "Create tag v$$(python -c 'from src.tyko.__version__ import __version__; print(__version__)')? [y/N] " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		git tag -a v$$(python -c 'from src.tyko.__version__ import __version__; print(__version__)') -m "Release version $$(python -c 'from src.tyko.__version__ import __version__; print(__version__)')"; \
		echo "Tag created. Push with: git push origin v$$(python -c 'from src.tyko.__version__ import __version__; print(__version__)')"; \
	fi
