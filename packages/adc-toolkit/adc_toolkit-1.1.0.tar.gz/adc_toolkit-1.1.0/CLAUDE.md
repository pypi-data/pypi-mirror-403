# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **adc-toolkit**, a Python framework for ADC data science and ML projects. It provides a structured approach to data handling with built-in validation, logging, EDA utilities, and processing tools. The toolkit emphasizes type safety, comprehensive testing, and reproducibility.

## Technology Stack & Key Dependencies

- **Python**: >=3.10, <3.14
- **Package Manager**: uv
- **Code Quality**: Ruff (linting + formatting + import sorting), mypy (type checking)
- **Testing**: pytest with 90% coverage requirement (CI/CD enforces this)
- **Documentation**: pdoc (NumPy-style docstrings required)
- **Configuration Management**: Hydra
- **Data Validation**: Great Expectations (GX) and Pandera
- **Data Catalog**: Kedro DataCatalog integration
- **Data Science**: pandas, numpy, scipy, statsmodels, matplotlib, seaborn
- **Optional Groups**: kedro, pandera, gx (Great Expectations), spark, gcp, logging (loguru), preprocessing (scikit-learn)

## Common Commands

### Development

```bash
# Install dependencies
uv sync                    # Install core + dev dependencies
uv sync --all-extras       # Install with all optional groups

# Virtual environment
uv shell  # Enter shell
exit      # Leave shell

# Code quality
make lint                                   # Run all linters and pre-commit hooks
uv run pre-commit run --all --all-files     # Same as above

# Testing
make test                                                    # Run all tests
make coverage                                                # Run tests with coverage report
uv run pytest --cov=src/adc_toolkit/ --cov-fail-under=90     # CI/CD command

# Run specific test
uv run pytest src/adc_toolkit/data/tests/test_catalog.py
uv run pytest src/adc_toolkit/data/tests/test_catalog.py::test_function_name

# Documentation
make doc_browser  # View documentation in browser
make doc_html     # Generate HTML docs in docs/html/
```

### Package Management

```bash
uv add <package>              # Add to main dependencies
uv add --group dev <package>  # Add to dev dependencies
uv remove <package>           # Remove package
uv update                     # Update all dependencies to latest versions
```

## Architecture

### Core Module Structure

The toolkit is organized under `src/adc_toolkit/` with these main components:

#### 1. **Data Module** (`src/adc_toolkit/data/`)

The centerpiece of the toolkit. Provides validated data catalog functionality:

- **`ValidatedDataCatalog`**: Main abstraction that combines a data catalog (for I/O) with a data validator
  - Uses Kedro's DataCatalog by default for loading/saving data
  - Supports GX (Great Expectations) or Pandera validators
  - Validates data after loading and before saving
  - Factory pattern: `ValidatedDataCatalog.in_directory("path/to/config")`

- **Catalog Implementations** (`catalogs/kedro/`): Kedro integration for data I/O with YAML configs
  - `KedroDataCatalog`: Wraps Kedro's DataCatalog
  - `KedroDataCatalog.init_catalog()`: Scaffolds the required folder structure

- **Validators** (`validators/`):
  - `gx/`: Great Expectations validator with batch managers, data context support (AWS, GCP, Azure), custom expectations
  - `pandera/`: Pandera-based validation with schema compilation and execution
  - `no_validator.py`: No-op validator when validation is not needed

#### 2. **CLI Module** (`src/adc_toolkit/cli/`)

Command-line interface for the toolkit:

- `adc-toolkit --version`: Show version
- `adc-toolkit init-catalog [PATH]`: Initialize Kedro catalog folder structure
  - Creates `base/globals.yml`, `base/catalog.yml`, `local/credentials.yml`
  - Flags: `--overwrite`, `--no-globals`, `--no-catalog`, `--no-credentials`

#### 3. **Processing Module** (`src/adc_toolkit/processing/`)

Data transformation pipeline with chainable steps:

- **`ProcessingPipeline`**: Orchestrates data transformations via `.add()` and `.run()`
- **`PipelineStep`**: Wraps individual transformation functions
- **Built-in steps** (`steps/pandas/`):
  - `remove_duplicates`, `fill_missing_values`, `make_columns_snake_case`
  - `filter_rows`, `select_columns`
  - `scale_data`, `encode_categorical`, `divide_one_column_by_another`
  - `group_and_aggregate`
- Accepts any callable with signature `(df: DataFrame, **kwargs) -> DataFrame`

#### 4. **EDA Module** (`src/adc_toolkit/eda/`)

Exploratory Data Analysis utilities (partially implemented):

- `time_series/`: Analysis, plotting, and statistics for time series data
- `cross_sectional/`: Cross-sectional analysis
- Uses Hydra for configuration-driven EDA

#### 5. **Logger Module** (`src/adc_toolkit/logger/`)

Flexible logging infrastructure with multiple backend support:

- **`Logger`**: Unified interface with `debug()`, `info()`, `warning()`, `error()` methods
- **`Logger.set_level()`**: Set global log level
- Auto-selects backend: Loguru (if installed) or Python standard logging

#### 6. **Configuration Module** (`src/adc_toolkit/configuration/`)

Hydra-based configuration management:

- `base/`: Base configuration templates
- `local/`: Local overrides (not committed to git)

#### 7. **Utils Module** (`src/adc_toolkit/utils/`)

Shared utility functions for filesystem management, module loading, and custom exceptions.

### Design Patterns

- **Dependency Injection**: The toolkit uses dependency injection for catalogs and validators
- **Strategy Pattern**: Validators are swappable (GX, Pandera, or NoValidator)
- **Factory Pattern**: `ValidatedDataCatalog.in_directory()` for instantiation
- **Protocol Classes**: `Data`, `DataCatalog`, `DataValidator` provide contracts in `abs.py`

### Testing Strategy

- Tests are **embedded within module directories** (not in a top-level `tests/` folder)
- Each module has its own `tests/` subdirectory (e.g., `src/adc_toolkit/data/tests/`)
- This collocated approach keeps tests close to implementation
- CI/CD enforces 90% code coverage minimum
- Use pytest with mocking for external dependencies (databases, APIs)
- Set Java 17 environment variable for Spark tests

## Code Style & Standards

### Type Annotations & Documentation

- **All functions, methods, and class members must have type annotations** using the `typing` module
- **All functions, methods, and classes must have NumPy-style docstrings** with thorough explanations
- Mypy is enforced with strict settings (see pyproject.toml)

### Code Quality Requirements

- Follow PEP 8
- Use Ruff as primary linter/formatter (line length: 120)
- Aim for 90%+ test coverage (enforced in CI/CD)
- Use specific exception types with informative error messages
- Implement robust exception handling; avoid bare `except` clauses
- Use `logging` module judiciously

### Python Best Practices

- Write elegant, Pythonic code
- Single Responsibility Principle for modules
- Favor composition over inheritance
- Use async/await for I/O-bound operations
- Apply caching (`functools.lru_cache`, `@cache`) where appropriate
- Don't over-engineer; strive for simplicity while maintaining efficiency

### Pre-commit Hooks

The following checks run automatically on commit:

- **Ruff**: Linting with auto-fix + formatting (replaces Black, isort, Flake8)
- **mypy**: Type checking (excludes tests/notebooks)
- **gitleaks**: Secret detection
- **nbstripout**: Removes notebook outputs
- **codespell**: Spell checking
- **sqlfluff**: SQL linting
- **prettier**: YAML/JSON/Markdown formatting
- **General checks**: Trailing whitespace, YAML/TOML/JSON syntax, large files, merge conflicts, debug statements

## Project-Specific Notes

### Initializing the Data Catalog

Before using `ValidatedDataCatalog`, initialize the folder structure:

```bash
# Using CLI
adc-toolkit init-catalog ./config

# Using Python
from adc_toolkit.data.catalogs.kedro import KedroDataCatalog
KedroDataCatalog.init_catalog("./config")
```

This creates:

```
config/
├── base/
│   ├── globals.yml      # Global variables (bucket paths, dataset types)
│   └── catalog.yml      # Dataset definitions
└── local/
    └── credentials.yml  # Secrets (gitignored)
```

### Data Validation Workflow

When using `ValidatedDataCatalog`:

1. Initialize catalog structure: `adc-toolkit init-catalog ./config`
2. Configure `globals.yml` with bucket paths and dataset type mappings
3. Define datasets in `catalog.yml` (Kedro format)
4. Instantiate: `catalog = ValidatedDataCatalog.in_directory("./config")`
5. Load with validation: `df = catalog.load("dataset_name")` (auto-freezes schema on first load)
6. Save with validation: `catalog.save("dataset_name", df)`

### Optional Dependencies

Several feature groups are optional and must be explicitly installed:

| Group           | Purpose                                                            |
| --------------- | ------------------------------------------------------------------ |
| `kedro`         | Kedro DataCatalog for data I/O (required for ValidatedDataCatalog) |
| `gx`            | Great Expectations validation                                      |
| `pandera`       | Pandera validation                                                 |
| `spark`         | PySpark support                                                    |
| `gcp`           | Google Cloud Platform integration                                  |
| `logging`       | Loguru logging backend                                             |
| `preprocessing` | scikit-learn transformations                                       |

```bash
uv sync --extra kedro --extra gx  # Install specific groups
uv sync --all-extras              # Install all optional groups
```

### CI/CD Workflows

- **Unit Tests** (`.github/workflows/unittest.yml`): Runs on PR, requires 90% coverage
- **Linting** (`.github/workflows/lint_sqlfluff.yml`): SQL linting
- **Documentation** (`.github/workflows/pdoc-docs.yaml`): Auto-generates API docs
- **Releases** (`.github/workflows/release.yaml`): Automated release process

### Documentation Generation

- Uses pdoc for API documentation generation
- Docstrings must follow NumPy style
- Run `make doc_browser` during development to preview docs
- CI/CD auto-generates and publishes documentation

## Working with Notebooks

- Notebooks go in `notebooks/` directory
- Use naming convention: `{number}-{initials}-{description}.ipynb` (e.g., `01-mb-initial-data-exploration.ipynb`)
- nbstripout runs automatically to remove outputs before commit
- Notebook cells are formatted with Ruff (line length: 120)

## Important: Do Not Create These Files

- Do not create generic documentation, README files, or markdown files unless explicitly requested
- The project already has comprehensive documentation
- Focus on code implementation, not documentation generation
