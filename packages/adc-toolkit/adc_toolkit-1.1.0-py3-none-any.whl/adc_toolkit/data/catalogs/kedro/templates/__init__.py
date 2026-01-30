"""
Template files for Kedro catalog scaffolding.

This module contains template YAML configuration files used when scaffolding
new Kedro catalog directory structures via `KedroDataCatalog.init_catalog()`.
These templates provide starting points for configuring data catalogs with
helpful examples and documentation comments.

The templates establish best practices for organizing catalog configurations,
including separation of base definitions from local overrides, use of global
variables for parameterization, and secure credential management.

Files
-----
catalog.yml
    Template for base catalog dataset definitions. Includes commented examples
    for common dataset types (CSV, Parquet, SQL) and demonstrates use of global
    variables, versioning, and dataset factories.

globals.yml
    Template for global variables and parameters. Includes examples for common
    variables like base paths, bucket names, dataset type shortcuts, and folder
    organization patterns.

credentials_template.yml
    Template for credentials configuration. Includes commented examples for
    database connections (PostgreSQL, MySQL, BigQuery) and cloud storage
    credentials (AWS, GCS, Azure). Should be copied to local/credentials.yml
    and added to .gitignore.

.gitignore
    Template .gitignore file for the catalog directory. Ensures local overrides
    and credentials are not committed to version control.

See Also
--------
adc_toolkit.data.catalogs.kedro.KedroDataCatalog.init_catalog : Method that uses these templates.
adc_toolkit.data.catalogs.kedro.scaffold : Module with scaffolding utilities.

Notes
-----
These template files are embedded in the package and copied to new catalog
directories when `KedroDataCatalog.init_catalog()` is called. They are not
meant to be imported or used directly in application code.

Template files use YAML format with:
- Extensive documentation comments explaining configuration options
- Example dataset definitions demonstrating common patterns
- Placeholder values that should be replaced with project-specific values
- References to Kedro documentation for detailed information

Best Practices
--------------
When using these templates in a new project:

1. **Review and Customize**: Templates provide examples, not production-ready
   configurations. Review and adapt them to your project's needs.

2. **Global Variables**: Define common paths and parameters in globals.yml
   to avoid repetition and enable easy environment-specific overrides.

3. **Credentials Management**: Always store credentials in local/credentials.yml
   and add it to .gitignore. Never commit credentials to version control.

4. **Environment Structure**: Use base/ for shared definitions and local/ for
   environment-specific overrides. This enables consistent behavior across dev,
   staging, and production with minimal configuration duplication.

5. **Documentation**: Add comments to your catalog.yml explaining the purpose
   and structure of each dataset, especially for complex configurations.

Template Organization
---------------------
Templates are organized to support Kedro's layered configuration system:

- **base/catalog.yml**: Shared dataset definitions for all environments.
  Should contain dataset names, types, and default parameters.

- **base/globals.yml**: Shared global variables. Should contain variables
  that are the same across environments or have sensible defaults.

- **local/catalog.yml**: Environment-specific overrides. Empty in template
  but can override any base definitions.

- **local/credentials.yml**: Environment-specific credentials. Should contain
  all sensitive information (passwords, API keys, connection strings).

This separation enables:
- Version control for base configurations
- Environment-specific customization without duplicating base definitions
- Secure credential management outside of version control

Examples
--------
The templates are used automatically when scaffolding a new catalog:

>>> from adc_toolkit.data.catalogs.kedro import KedroDataCatalog
>>> result = KedroDataCatalog.init_catalog("./config/catalog")
>>> # Template files are copied to ./config/catalog/base/ and ./config/catalog/local/

After scaffolding, customize the templates for your project:

.. code-block:: yaml

    # Edit base/catalog.yml with your datasets
    my_dataset:
      type: pandas.CSVDataset
      filepath: ${globals:data_path}/my_dataset.csv
      load_args:
        sep: ","

    # Edit base/globals.yml with your paths
    data_path: data/raw
    processed_path: data/processed

    # Edit local/credentials.yml with your credentials (don't commit!)
    db_credentials:
      con: postgresql://user:password@localhost:5432/mydb

Typical workflow:

>>> # Step 1: Initialize catalog structure
>>> from adc_toolkit.data.catalogs.kedro import KedroDataCatalog
>>> KedroDataCatalog.init_catalog("./config/catalog")
>>>
>>> # Step 2: Edit the generated YAML files to define your datasets
>>> # (Edit files manually in your editor)
>>>
>>> # Step 3: Add local/credentials.yml to .gitignore
>>> # (Add "local/credentials.yml" to your .gitignore file)
>>>
>>> # Step 4: Use the configured catalog
>>> catalog = KedroDataCatalog.in_directory("./config/catalog")
>>> df = catalog.load("my_dataset")
"""
