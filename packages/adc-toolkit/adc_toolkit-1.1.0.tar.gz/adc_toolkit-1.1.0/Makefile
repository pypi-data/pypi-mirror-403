.PHONY: lint
lint:  # Use all linters on all files (not just staged for commit)
	uv run --extra dev pre-commit run --all --all-files

.PHONY: doc_browser
doc_browser:  # Generate and serve documentation in browser
	uv run pdoc src/adc_toolkit --docformat numpy

.PHONY: doc_html
doc_html:  # Generate HTML documentation in docs/html
	uv run pdoc src/adc_toolkit --docformat numpy -o docs/html

.PHONY: test
test:  # Run tests on all tests in the tests folder
	uv run pytest

.PHONY: coverage
coverage:  # Run all tests and check coverage of all tests on all tests in the tests folder
	uv run pytest --cov

.PHONY: cov_report
cov_report:  # Create a coverage report of all tests
	uv run coverage html

.PHONY: install
install:  # Install core + dev dependencies
	uv sync --extra dev

.PHONY: install_all
install_all:  # Install all dependencies including optional groups
	uv sync --all-extras

.PHONY: build
build:  # Build package for local testing
	uv build

.PHONY: clean
clean:  # Remove build artifacts and cache files
	rm -rf build/ dist/ *.egg-info .pytest_cache/ .mypy_cache/ .ruff_cache/ .coverage htmlcov/ docs/html/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

.PHONY: precommit_install
precommit_install:  # Set up pre-commit hooks for new contributors
	uv run pre-commit install

.PHONY: update
update:  # Update all dependencies to latest versions
	uv lock --upgrade && uv sync --extra dev

.PHONY: help
help:  # Show all available commands
	@grep -E '^[a-zA-Z_-]+:.*#' $(MAKEFILE_LIST) | awk -F ':.*# ' '{printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
