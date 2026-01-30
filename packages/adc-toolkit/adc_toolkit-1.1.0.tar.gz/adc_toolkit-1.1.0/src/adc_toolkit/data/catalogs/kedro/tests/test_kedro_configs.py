"""Test Kedro configuration functions."""

import unittest
from unittest.mock import MagicMock, patch

from kedro.config import MissingConfigException, OmegaConfigLoader

from adc_toolkit.data.catalogs.kedro.kedro_configs import (
    _replace_sql_with_query,
    create_catalog,
    create_omega_config_loader,
    get_catalog_config,
    get_credentials_config,
)


class TestKedroConfigs(unittest.TestCase):
    """Unit tests for the kedro_configs module."""

    @patch("kedro.config.OmegaConfigLoader.__init__", return_value=None)
    def test_create_omega_config_loader(self, mock_omega_config_loader_init: MagicMock) -> None:
        """Test that create_omega_config_loader works correctly."""
        config_path = "/path/to/config"

        result = create_omega_config_loader(config_path)

        mock_omega_config_loader_init.assert_called_once_with(
            conf_source=config_path,
            base_env="base",
            default_run_env="local",
        )
        self.assertIsInstance(result, OmegaConfigLoader)

    def test_get_catalog_config(self) -> None:
        """Test that get_catalog_config works correctly."""
        mock_config_loader = MagicMock()
        mock_config_loader.__getitem__.return_value = {"key": "value"}

        # Test when catalog config exists
        result = get_catalog_config(mock_config_loader)
        self.assertEqual(result, {"key": "value"})
        mock_config_loader.__getitem__.assert_called_once_with("catalog")

        # Reset mock for the next test
        mock_config_loader.__getitem__.reset_mock()

        # Test when catalog config does not exist
        mock_config_loader.__getitem__.side_effect = MissingConfigException()
        with self.assertRaises(MissingConfigException):
            result = get_catalog_config(mock_config_loader)

    def test_replace_sql_with_query_sql_not_in_params(self) -> None:
        """Test that _replace_sql_with_query does nothing when `sql` is not in the params."""
        catalog_config = {"df_name": {"param": "value"}}

        result = _replace_sql_with_query(catalog_config)
        self.assertEqual(result, catalog_config)

    def test_replace_sql_with_query_sql_in_params_not_path(self) -> None:
        """Test that _replace_sql_with_query does nothing when `sql` is not a path."""
        catalog_config = {"df_name": {"sql": "SELECT * FROM table"}}

        result = _replace_sql_with_query(catalog_config)
        self.assertEqual(result, catalog_config)

    @patch("adc_toolkit.data.catalogs.kedro.kedro_configs.Path")
    def test_replace_sql_with_query_sql_in_params_path(self, mock_path: MagicMock) -> None:
        """Test that _replace_sql_with_query replaces `sql` with the query from the path."""
        catalog_config = {"df_name": {"sql": "/path/to/query.sql"}}
        mock_path.return_value.is_file.return_value = True
        mock_path.return_value.read_text.return_value = "SELECT * FROM table"

        result = _replace_sql_with_query(catalog_config)
        self.assertEqual(result, {"df_name": {"sql": "SELECT * FROM table"}})

    def test_get_credentials_config(self) -> None:
        """Test that get_credentials_config works correctly."""
        mock_config_loader = MagicMock()
        mock_config_loader.__getitem__.return_value = {"key": "value"}

        # Test when credentials config exists
        result = get_credentials_config(mock_config_loader)
        self.assertEqual(result, {"key": "value"})
        mock_config_loader.__getitem__.assert_called_once_with("credentials")

    def test_get_credentials_config_warns_missing_config(self) -> None:
        """Test that get_credentials_config warns when credentials config does not exist."""
        mock_config_loader = MagicMock()

        # Test when credentials config does not exist (MissingConfigException)
        mock_config_loader.__getitem__.side_effect = MissingConfigException()
        with self.assertWarns(UserWarning):
            result = get_credentials_config(mock_config_loader)
            self.assertEqual(result, {})
            mock_config_loader.__getitem__.assert_called_once_with("credentials")

    def test_get_credentials_config_warns_key_error(self) -> None:
        """Test that get_credentials_config warns when credentials key does not exist."""
        mock_config_loader = MagicMock()

        # Test when credentials key does not exist (KeyError)
        mock_config_loader.__getitem__.side_effect = KeyError("credentials")
        with self.assertWarns(UserWarning):
            result = get_credentials_config(mock_config_loader)
            self.assertEqual(result, {})
            mock_config_loader.__getitem__.assert_called_once_with("credentials")

    @patch("adc_toolkit.data.catalogs.kedro.kedro_configs.get_catalog_config")
    @patch("adc_toolkit.data.catalogs.kedro.kedro_configs.get_credentials_config")
    @patch("kedro.io.DataCatalog.from_config")
    def test_create_catalog(
        self,
        mock_data_catalog_from_config: MagicMock,
        mock_get_credentials_config: MagicMock,
        mock_get_catalog_config: MagicMock,
    ) -> None:
        """Test that create_catalog works correctly."""
        mock_config_loader = MagicMock()
        mock_catalog_config = {"key": "value"}
        mock_credentials_config = {"key": "value"}
        mock_data_catalog = MagicMock()

        mock_get_catalog_config.return_value = mock_catalog_config
        mock_get_credentials_config.return_value = mock_credentials_config
        mock_data_catalog_from_config.return_value = mock_data_catalog

        result = create_catalog(mock_config_loader)

        mock_get_catalog_config.assert_called_once_with(mock_config_loader)
        mock_get_credentials_config.assert_called_once_with(mock_config_loader)
        mock_data_catalog_from_config.assert_called_once_with(
            catalog=mock_catalog_config, credentials=mock_credentials_config
        )
        self.assertEqual(result, mock_data_catalog)
