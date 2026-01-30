"""Unit tests for the CLI main module."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from adc_toolkit.cli.main import create_parser, init_catalog_command, main


class TestCreateParser:
    """Tests for create_parser function."""

    def test_parser_has_version(self) -> None:
        """Test that parser has version argument."""
        parser = create_parser()
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args(["--version"])
        assert exc_info.value.code == 0

    def test_parser_has_init_catalog_command(self) -> None:
        """Test that parser has init-catalog command."""
        parser = create_parser()
        args = parser.parse_args(["init-catalog"])
        assert args.command == "init-catalog"
        assert args.path == "."
        assert args.overwrite is False

    def test_init_catalog_with_path(self) -> None:
        """Test init-catalog command with custom path."""
        parser = create_parser()
        args = parser.parse_args(["init-catalog", "/custom/path"])
        assert args.path == "/custom/path"

    def test_init_catalog_with_overwrite(self) -> None:
        """Test init-catalog command with overwrite flag."""
        parser = create_parser()
        args = parser.parse_args(["init-catalog", "--overwrite"])
        assert args.overwrite is True

    def test_init_catalog_with_no_globals(self) -> None:
        """Test init-catalog command with --no-globals flag."""
        parser = create_parser()
        args = parser.parse_args(["init-catalog", "--no-globals"])
        assert args.no_globals is True

    def test_init_catalog_with_no_catalog(self) -> None:
        """Test init-catalog command with --no-catalog flag."""
        parser = create_parser()
        args = parser.parse_args(["init-catalog", "--no-catalog"])
        assert args.no_catalog is True

    def test_init_catalog_with_no_credentials(self) -> None:
        """Test init-catalog command with --no-credentials flag."""
        parser = create_parser()
        args = parser.parse_args(["init-catalog", "--no-credentials"])
        assert args.no_credentials is True

    def test_init_catalog_with_all_exclude_flags(self) -> None:
        """Test init-catalog command with all exclude flags."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "init-catalog",
                "--no-globals",
                "--no-catalog",
                "--no-credentials",
            ]
        )
        assert args.no_globals is True
        assert args.no_catalog is True
        assert args.no_credentials is True


class TestInitCatalogCommand:
    """Tests for init_catalog_command function."""

    def test_creates_structure(self) -> None:
        """Test that init_catalog_command creates the structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parser = create_parser()
            args = parser.parse_args(["init-catalog", tmpdir])

            exit_code = init_catalog_command(args)

            config_path = Path(tmpdir)
            assert exit_code == 0
            assert (config_path / "base" / "globals.yml").exists()
            assert (config_path / "base" / "catalog.yml").exists()
            assert (config_path / "local" / "credentials.yml").exists()
            assert (config_path / "local" / ".gitignore").exists()

    def test_returns_zero_when_skipping(self) -> None:
        """Test that command returns 0 even when skipping files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parser = create_parser()
            args = parser.parse_args(["init-catalog", tmpdir])

            # Create first time
            init_catalog_command(args)

            # Create second time (should skip)
            exit_code = init_catalog_command(args)

            assert exit_code == 0

    def test_overwrite_flag_works(self) -> None:
        """Test that overwrite flag replaces files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parser = create_parser()

            # Create first time
            args = parser.parse_args(["init-catalog", tmpdir])
            init_catalog_command(args)

            # Modify a file
            config_path = Path(tmpdir)
            globals_path = config_path / "base" / "globals.yml"
            globals_path.write_text("modified")

            # Overwrite
            args = parser.parse_args(["init-catalog", tmpdir, "--overwrite"])
            exit_code = init_catalog_command(args)

            assert exit_code == 0
            assert "bucket_prefix" in globals_path.read_text()

    def test_no_globals_flag(self) -> None:
        """Test that --no-globals skips globals.yml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parser = create_parser()
            args = parser.parse_args(["init-catalog", tmpdir, "--no-globals"])

            exit_code = init_catalog_command(args)

            config_path = Path(tmpdir)
            assert exit_code == 0
            assert not (config_path / "base" / "globals.yml").exists()
            assert (config_path / "base" / "catalog.yml").exists()

    def test_resolves_path(self) -> None:
        """Test that path is resolved to absolute path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a relative path
            parser = create_parser()
            args = parser.parse_args(["init-catalog", tmpdir])

            exit_code = init_catalog_command(args)

            assert exit_code == 0

    def test_all_files_excluded_returns_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that excluding all files returns exit code 1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            parser = create_parser()
            args = parser.parse_args(["init-catalog", tmpdir, "--no-globals", "--no-catalog", "--no-credentials"])

            exit_code = init_catalog_command(args)

            assert exit_code == 1
            captured = capsys.readouterr()
            assert "All files excluded" in captured.out


class TestMain:
    """Tests for main function."""

    def test_no_command_prints_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that no command prints help and returns 0."""
        exit_code = main([])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower()

    def test_init_catalog_integration(self) -> None:
        """Test full init-catalog integration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code = main(["init-catalog", tmpdir])
            config_path = Path(tmpdir)
            assert exit_code == 0
            assert (config_path / "base" / "globals.yml").exists()
            assert (config_path / "local" / ".gitignore").exists()

    def test_version_flag(self) -> None:
        """Test that --version flag works."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0


class TestInitCatalogImportError:
    """Tests for import error handling."""

    def test_import_error_returns_one(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that ImportError returns exit code 1 when kedro is not installed."""
        import sys

        with patch.dict(sys.modules, {"adc_toolkit.data.catalogs.kedro.scaffold": None}):
            parser = create_parser()
            args = parser.parse_args(["init-catalog", "/tmp/test"])
            exit_code = init_catalog_command(args)

            assert exit_code == 1
            captured = capsys.readouterr()
            assert "kedro is required" in captured.out

    def test_kedro_import_error_shows_install_instructions(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that kedro import error shows uv sync install instructions."""
        import sys

        with patch.dict(sys.modules, {"adc_toolkit.data.catalogs.kedro.scaffold": None}):
            parser = create_parser()
            args = parser.parse_args(["init-catalog", "/tmp/test"])
            init_catalog_command(args)

            captured = capsys.readouterr()
            assert "uv sync --extra kedro" in captured.out
