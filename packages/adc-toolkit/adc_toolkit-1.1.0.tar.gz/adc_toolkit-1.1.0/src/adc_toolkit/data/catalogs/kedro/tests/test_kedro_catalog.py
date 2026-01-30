"""Unit tests for the KedroDataCatalog class."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from adc_toolkit.data.abs import Data
from adc_toolkit.data.catalogs.kedro.kedro_catalog import KedroDataCatalog


class TestKedroDataCatalog(unittest.TestCase):
    """Unit tests for the KedroDataCatalog class."""

    def setUp(self) -> None:
        """Set up."""
        self.config_loader = MagicMock()

    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.Path.exists", return_value=True)
    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.create_catalog")
    def test_init(
        self,
        mock_create_catalog: MagicMock,
        mock_exists: MagicMock,
    ) -> None:
        """Test that the data catalog is initialized correctly."""
        mock_catalog = MagicMock()
        mock_create_catalog.return_value = mock_catalog

        kedro_data_catalog = KedroDataCatalog("test/config/path", self.config_loader)

        mock_create_catalog.assert_called_once_with(self.config_loader)
        self.assertEqual(kedro_data_catalog._catalog, mock_catalog)

    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.Path.exists", return_value=True)
    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.create_catalog")
    def test_load(self, mock_create_catalog: MagicMock, mock_exists: MagicMock) -> None:
        """Test that the data catalog loads data correctly."""
        mock_catalog = MagicMock()
        mock_create_catalog.return_value = mock_catalog
        mock_data = MagicMock(spec=Data)
        mock_catalog.load.return_value = mock_data

        kedro_data_catalog = KedroDataCatalog("test/config/path", self.config_loader)
        result = kedro_data_catalog.load("test_data")

        mock_catalog.load.assert_called_once_with("test_data")
        self.assertEqual(result, mock_data)

    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.Path.exists", return_value=True)
    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.create_catalog")
    def test_load_with_query(self, mock_create_catalog: MagicMock, mock_exists: MagicMock) -> None:
        """Test that the data catalog loads data correctly with a query."""
        mock_catalog = MagicMock()
        mock_create_catalog.return_value = mock_catalog
        mock_data = MagicMock(spec=Data)
        mock_catalog.load.return_value = mock_data

        kedro_data_catalog = KedroDataCatalog("test/config/path", self.config_loader)
        kedro_data_catalog._catalog._datasets["test_data"]._load_args = {"query": "{query_arg}"}
        result = kedro_data_catalog.load("test_data", query_arg="test_query")

        mock_catalog.load.assert_called_once_with("test_data")
        assert kedro_data_catalog._catalog._datasets["test_data"]._load_args["query"] == "{query_arg}"
        self.assertEqual(result, mock_data)

    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.Path.exists", return_value=True)
    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.create_catalog")
    def test_load_with_query_not_supported(self, mock_create_catalog: MagicMock, mock_exists: MagicMock) -> None:
        """Test that the data catalog raises an error when loading data with a query that is not supported."""
        mock_catalog = MagicMock()
        mock_create_catalog.return_value = mock_catalog

        kedro_data_catalog = KedroDataCatalog("test/config/path", self.config_loader)
        kedro_data_catalog._catalog._datasets["test_data"]._load_args = {}
        with self.assertRaises(ValueError):
            kedro_data_catalog.load("test_data", query_arg="test_query")

    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.Path.exists", return_value=True)
    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.create_catalog")
    def test_save(self, mock_create_catalog: MagicMock, mock_exists: MagicMock) -> None:
        """Test that the data catalog saves data correctly."""
        mock_catalog = MagicMock()
        mock_create_catalog.return_value = mock_catalog
        mock_data = MagicMock(spec=Data)

        kedro_data_catalog = KedroDataCatalog("test/config/path", self.config_loader)
        kedro_data_catalog._catalog = mock_catalog
        kedro_data_catalog.save("test_data", mock_data)

        mock_catalog.save.assert_called_once_with("test_data", mock_data)

    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.Path.exists", return_value=True)
    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.create_catalog")
    def test_load_with_dynamic_query(self, mock_create_catalog: MagicMock, mock_exists: MagicMock) -> None:
        """Test that the data catalog loads data with a dynamic query correctly."""
        mock_catalog = MagicMock()
        mock_create_catalog.return_value = mock_catalog

        kedro_data_catalog = KedroDataCatalog("test/config/path", self.config_loader)
        kedro_data_catalog._catalog._datasets = {"test_data": MagicMock(_load_args={"query": "{query_arg}"})}
        kedro_data_catalog._load_with_dynamic_query("test_data", query_arg="test_query")

        assert kedro_data_catalog._catalog._datasets["test_data"]._load_args["query"] == "{query_arg}"

    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.Path.exists", return_value=True)
    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.create_catalog")
    def test_load_with_dynamic_query_not_supported(
        self, mock_create_catalog: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Test that the data catalog raises an error when loading data with a dynamic query that is not supported."""
        mock_catalog = MagicMock()
        mock_create_catalog.return_value = mock_catalog

        kedro_data_catalog = KedroDataCatalog("test/config/path", self.config_loader)
        kedro_data_catalog._catalog._datasets = {"test_data": MagicMock(_load_args={})}
        with self.assertRaises(ValueError):
            kedro_data_catalog._load_with_dynamic_query("test_data", query_arg="test_query")

    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.Path.exists", return_value=True)
    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.create_catalog")
    @patch("adc_toolkit.data.catalogs.kedro.kedro_catalog.create_omega_config_loader")
    def test_in_directory(
        self,
        mock_create_omega_config_loader: MagicMock,
        mock_create_catalog: MagicMock,
        mock_exists: MagicMock,
    ) -> None:
        """Test that the data catalog is initialized correctly with a directory path."""
        mock_catalog = MagicMock()
        mock_create_catalog.return_value = mock_catalog

        kedro_data_catalog = KedroDataCatalog.in_directory("test/config/path")

        mock_create_catalog.assert_called_once_with(mock_create_omega_config_loader.return_value)
        self.assertEqual(kedro_data_catalog._catalog, mock_catalog)

    def test_init_raises_file_not_found_error(self) -> None:
        """Test that FileNotFoundError is raised when config path does not exist."""
        with self.assertRaises(FileNotFoundError) as context:
            KedroDataCatalog("/nonexistent/path")

        self.assertIn("Configuration directory not found", str(context.exception))
        self.assertIn("adc-toolkit init-catalog", str(context.exception))
        self.assertIn("init_catalog", str(context.exception))

    def test_init_raises_error_for_incomplete_structure(self) -> None:
        """Test that FileNotFoundError is raised when catalog structure is incomplete."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create the directory but not the catalog structure
            path = Path(tmpdir)

            with self.assertRaises(FileNotFoundError) as context:
                KedroDataCatalog(path)

            self.assertIn("Catalog structure is incomplete", str(context.exception))
            self.assertIn("adc-toolkit init-catalog", str(context.exception))
            self.assertIn("init_catalog", str(context.exception))

    def test_init_raises_error_for_partial_structure(self) -> None:
        """Test that FileNotFoundError is raised when some files are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)

            # Create partial structure (only globals.yml)
            (path / "base").mkdir(parents=True)
            (path / "base" / "globals.yml").write_text("test")

            with self.assertRaises(FileNotFoundError) as context:
                KedroDataCatalog(path)

            self.assertIn("Catalog structure is incomplete", str(context.exception))

    def test_init_catalog_creates_structure(self) -> None:
        """Test that init_catalog creates the folder structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"
            result = KedroDataCatalog.init_catalog(path)

            self.assertTrue(result.success)
            self.assertEqual(len(result.created_files), 4)
            self.assertTrue((path / "base" / "globals.yml").exists())
            self.assertTrue((path / "base" / "catalog.yml").exists())
            self.assertTrue((path / "local" / "credentials.yml").exists())
            self.assertTrue((path / "local" / ".gitignore").exists())

    def test_init_catalog_with_overwrite(self) -> None:
        """Test that init_catalog can overwrite existing files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"

            # Create first time
            KedroDataCatalog.init_catalog(path)

            # Modify a file
            globals_path = path / "base" / "globals.yml"
            globals_path.write_text("modified")

            # Create again with overwrite
            result = KedroDataCatalog.init_catalog(path, overwrite=True)

            self.assertEqual(len(result.created_files), 4)
            self.assertIn("bucket_prefix", globals_path.read_text())

    def test_init_catalog_with_exclude_flags(self) -> None:
        """Test that init_catalog can exclude specific files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"
            result = KedroDataCatalog.init_catalog(
                path,
                include_globals=False,
                include_credentials=False,
            )

            self.assertEqual(len(result.created_files), 1)
            self.assertFalse((path / "base" / "globals.yml").exists())
            self.assertTrue((path / "base" / "catalog.yml").exists())
            self.assertFalse((path / "local" / "credentials.yml").exists())
            self.assertFalse((path / "local" / ".gitignore").exists())
