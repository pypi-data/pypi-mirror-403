__version__ = "1.1.0"

__doc__ = f"""# ADC Toolkit: A Python Framework for Validated Data Pipelines

The adc-toolkit provides a structured approach to data handling in data science
and machine learning projects. It combines configuration-driven data catalogs
with automatic schema validation, ensuring data quality throughout your pipeline.

The toolkit's core value proposition is seamless validated data I/O: load data
with automatic validation, save data with automatic validation, and detect
schema drift without writing manual validation code.

---

## Key Features

- **ValidatedDataCatalog**: Main abstraction combining Kedro DataCatalog (I/O)
  with automatic data validation.
  Factory method: `ValidatedDataCatalog.in_directory(path)`.
- **Dual Validator Support**: Choose between Great Expectations (GX) for
  powerful expectation suites or Pandera for lightweight Python-based schema
  validation.
- **Auto Schema Detection**: Automatically generates and enforces schemas on
  first data load. Schema is "frozen" to prevent silent data drift in
  subsequent operations.
- **Processing Pipeline**: Chainable, reusable data transformation steps with
  a fluent API.
- **Flexible Logging**: Unified logging interface with support for Python
  logging and Loguru backends.
- **Hydra Configuration**: YAML-based hierarchical configuration management
  for reproducible pipelines.
- **Cloud Support**: AWS, GCP, and Azure data context support for Great
  Expectations.
- **CLI Tools**: Scaffold catalog structure with a single command:
  `adc-toolkit init-catalog`.

---

## Quick Start

### Installation

```bash
# Basic installation
pip install adc-toolkit

# With Kedro and Great Expectations (recommended)
pip install adc-toolkit[kedro,gx]

# With Kedro and Pandera
pip install adc-toolkit[kedro,pandera]
```

### Initialize Catalog Structure

```bash
adc-toolkit init-catalog ./config
```

### Load and Save Data with Validation

```python
from adc_toolkit.data.catalog import ValidatedDataCatalog

catalog = ValidatedDataCatalog.in_directory("./config")
df = catalog.load("my_dataset")  # Validated after loading
catalog.save("processed_data", df)  # Validated before saving
```

---

## Modules

- **data**: Core data module providing the ValidatedDataCatalog for validated
  data pipelines. Includes Kedro catalog integration and validators (Great
  Expectations, Pandera, NoValidator).
- **logger**: Flexible logging infrastructure with a unified interface.
  Supports both standard Python logging and Loguru backends.
  Main export: `Logger`.
- **processing**: Data processing utilities with chainable transformation
  pipelines. Main classes: `ProcessingPipeline`, `PipelineStep`.
- **eda**: Exploratory data analysis utilities for time series and
  cross-sectional data. Uses Hydra for configuration-driven EDA.
  Note: This module is partially implemented and shows a FutureWarning on
  import.
- **cli**: Command-line interface for toolkit operations. Provides
  `init-catalog` command for scaffolding configuration directories.
- **configuration**: Hydra-based configuration management with base templates
  and local overrides. Configuration files are in YAML format.
- **utils**: Shared utility functions including custom exceptions,
  configuration loaders, module management, and filesystem operations.

---

## Examples

### Basic Usage

```python
from adc_toolkit.data.catalog import ValidatedDataCatalog

catalog = ValidatedDataCatalog.in_directory("./config")
df = catalog.load("customer_data")  # Automatically validated
processed = df.dropna()
catalog.save("clean_customers", processed)  # Validated before saving
```

### Custom Validators

**Using Pandera validator:**

```python
from adc_toolkit.data.catalog import ValidatedDataCatalog
from adc_toolkit.data.validators.pandera import PanderaValidator

catalog = ValidatedDataCatalog.in_directory("./config", validator_class=PanderaValidator)
```

**Using Great Expectations validator:**

```python
from adc_toolkit.data.catalog import ValidatedDataCatalog
from adc_toolkit.data.validators.gx import GXValidator

catalog = ValidatedDataCatalog.in_directory("./config", validator_class=GXValidator)
```

### Processing Pipeline

```python
from adc_toolkit.processing.pipeline import ProcessingPipeline
from adc_toolkit.processing.steps.pandas import (
    remove_duplicates,
    fill_missing_values,
    make_columns_snake_case,
)

pipeline = ProcessingPipeline()
pipeline = (
    pipeline.add(remove_duplicates, subset=["id"])
    .add(fill_missing_values, method="median")
    .add(make_columns_snake_case)
)
processed_df = pipeline.run(df)
```

### Logging

```python
from adc_toolkit.logger import Logger

logger = Logger()
logger.info("Processing started")
Logger.set_level("debug")  # Set global log level
```

### CLI Usage

```bash
# Initialize catalog structure
adc-toolkit init-catalog ./config

# Overwrite existing files
adc-toolkit init-catalog ./config --overwrite

# Skip credentials file
adc-toolkit init-catalog ./config --no-credentials
```

### Complete Pipeline

```python
from adc_toolkit.data.catalog import ValidatedDataCatalog
from adc_toolkit.processing.pipeline import ProcessingPipeline
from adc_toolkit.processing.steps.pandas import remove_duplicates
from adc_toolkit.logger import Logger

logger = Logger()
logger.info("Starting data pipeline")

# Load with validation
catalog = ValidatedDataCatalog.in_directory("./config")
raw_data = catalog.load("sales_raw")

# Process
pipeline = ProcessingPipeline().add(remove_duplicates)
clean_data = pipeline.run(raw_data)

# Save with validation
catalog.save("sales_clean", clean_data)
logger.info("Pipeline complete")
```

---

## See Also

- `adc_toolkit.data.catalog.ValidatedDataCatalog`: Main data catalog API.
- `adc_toolkit.data.catalogs.kedro.KedroDataCatalog`: Kedro catalog implementation.
- `adc_toolkit.data.validators.gx.GXValidator`: Great Expectations validator.
- `adc_toolkit.data.validators.pandera.PanderaValidator`: Pandera validator.
- `adc_toolkit.logger.Logger`: Logging interface.
- `adc_toolkit.processing.pipeline.ProcessingPipeline`: Data transformation pipelines.
- `adc_toolkit.cli.main`: CLI entry point.

---

## Notes

### Optional Dependencies

The toolkit uses optional dependency groups to keep the base installation
lightweight. Install only what you need:

| Group           | Description                                              |
|-----------------|----------------------------------------------------------|
| `kedro`         | Kedro DataCatalog for data I/O (required for ValidatedDataCatalog) |
| `gx`            | Great Expectations validation                            |
| `pandera`       | Pandera validation                                       |
| `eda`           | Exploratory data analysis tools                          |
| `spark`         | PySpark support                                          |
| `gcp`           | Google Cloud Platform integration                        |
| `logging`       | Loguru logging backend                                   |
| `preprocessing` | scikit-learn transformations                             |

Install with: `pip install adc-toolkit[kedro,gx]` or similar.

### Design Patterns

- **Factory Pattern**: Use `in_directory(path)` class methods to instantiate
  catalogs and validators from configuration directories.
- **Strategy Pattern**: Swap catalog and validator implementations without
  changing downstream code.
- **Protocol-based Design**: Type safety through structural subtyping (PEP 544).
- **Dependency Injection**: Pass catalog and validator as constructor arguments.

### Configuration Structure

The toolkit expects this configuration directory structure:

```
config/
├── base/
│   ├── globals.yml      # Global variables (bucket paths, dataset types)
│   └── catalog.yml      # Kedro dataset definitions
└── local/
    └── credentials.yml  # Secrets and credentials (gitignored)
```

### Limitations

- The EDA module is partially implemented and shows a FutureWarning on import.
- Great Expectations is constrained to version <1.0.0 due to API changes in GX 1.0.
- The `kedro` optional dependency is required for ValidatedDataCatalog to function.

### Version Information

- **Current version**: {__version__}
- **Python support**: 3.10, 3.11, 3.12, 3.13
"""
