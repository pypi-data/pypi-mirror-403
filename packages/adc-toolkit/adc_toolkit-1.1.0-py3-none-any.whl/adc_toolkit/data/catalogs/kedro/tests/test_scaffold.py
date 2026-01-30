"""Unit tests for the scaffold module."""

import tempfile
from pathlib import Path

import pytest

from adc_toolkit.data.catalogs.kedro.scaffold import (
    ScaffoldResult,
    catalog_structure_exists,
    create_catalog_folder_structure,
    get_template_content,
)


class TestScaffoldResult:
    """Tests for ScaffoldResult dataclass."""

    def test_success_with_created_files(self) -> None:
        """Test that success is True when files were created."""
        result = ScaffoldResult(
            created_files=[Path("/test/file.yml")],
            skipped_files=[],
            created_directories=[],
        )
        assert result.success is True

    def test_success_with_created_directories(self) -> None:
        """Test that success is True when directories were created."""
        result = ScaffoldResult(
            created_files=[],
            skipped_files=[],
            created_directories=[Path("/test/dir")],
        )
        assert result.success is True

    def test_success_false_when_nothing_created(self) -> None:
        """Test that success is False when nothing was created."""
        result = ScaffoldResult(
            created_files=[],
            skipped_files=[Path("/test/file.yml")],
            created_directories=[],
        )
        assert result.success is False

    def test_default_values(self) -> None:
        """Test that default values are empty lists."""
        result = ScaffoldResult()
        assert result.created_files == []
        assert result.skipped_files == []
        assert result.created_directories == []


class TestGetTemplateContent:
    """Tests for get_template_content function."""

    def test_get_globals_template(self) -> None:
        """Test that globals template can be loaded."""
        content = get_template_content("globals")
        assert "bucket_prefix" in content
        assert "bucket_name" in content
        assert "datasets" in content
        assert "folders" in content

    def test_get_catalog_template(self) -> None:
        """Test that catalog template can be loaded."""
        content = get_template_content("catalog")
        assert "Kedro Data Catalog" in content
        assert "type:" in content

    def test_get_credentials_template(self) -> None:
        """Test that credentials template can be loaded."""
        content = get_template_content("credentials")
        assert "Credentials" in content
        assert "gitignore" in content.lower()

    def test_get_gitignore_template(self) -> None:
        """Test that gitignore template can be loaded."""
        content = get_template_content("gitignore")
        assert "credentials.yml" in content


class TestCreateCatalogFolderStructure:
    """Tests for create_catalog_folder_structure function."""

    def test_creates_full_structure(self) -> None:
        """Test that full folder structure is created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"
            result = create_catalog_folder_structure(path)

            assert isinstance(result, ScaffoldResult)
            assert result.success
            assert len(result.created_files) == 4
            assert len(result.created_directories) == 2
            assert len(result.skipped_files) == 0

            # Verify files exist
            assert (path / "base" / "globals.yml").exists()
            assert (path / "base" / "catalog.yml").exists()
            assert (path / "local" / "credentials.yml").exists()
            assert (path / "local" / ".gitignore").exists()

    def test_creates_directories_in_existing_path(self) -> None:
        """Test that directories are created in existing path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir)
            result = create_catalog_folder_structure(path)

            assert result.success
            assert (path / "base").exists()
            assert (path / "local").exists()

    def test_skips_existing_files(self) -> None:
        """Test that existing files are skipped by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"

            # Create structure first time
            create_catalog_folder_structure(path)

            # Modify a file
            globals_path = path / "base" / "globals.yml"
            globals_path.write_text("modified content")

            # Create again without overwrite
            result = create_catalog_folder_structure(path)

            assert len(result.created_files) == 0
            assert len(result.skipped_files) == 4

            # Verify file was not overwritten
            assert globals_path.read_text() == "modified content"

    def test_overwrites_existing_files(self) -> None:
        """Test that existing files are overwritten with flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"

            # Create structure first time
            create_catalog_folder_structure(path)

            # Modify a file
            globals_path = path / "base" / "globals.yml"
            globals_path.write_text("modified content")

            # Create again with overwrite
            result = create_catalog_folder_structure(path, overwrite=True)

            assert len(result.created_files) == 4
            assert len(result.skipped_files) == 0

            # Verify file was overwritten
            assert "bucket_prefix" in globals_path.read_text()

    def test_exclude_globals(self) -> None:
        """Test that globals can be excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"
            result = create_catalog_folder_structure(path, include_globals=False)

            assert len(result.created_files) == 3
            assert not (path / "base" / "globals.yml").exists()
            assert (path / "base" / "catalog.yml").exists()
            assert (path / "local" / "credentials.yml").exists()
            assert (path / "local" / ".gitignore").exists()

    def test_exclude_catalog(self) -> None:
        """Test that catalog can be excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"
            result = create_catalog_folder_structure(path, include_catalog=False)

            assert len(result.created_files) == 3
            assert (path / "base" / "globals.yml").exists()
            assert not (path / "base" / "catalog.yml").exists()
            assert (path / "local" / "credentials.yml").exists()
            assert (path / "local" / ".gitignore").exists()

    def test_exclude_credentials(self) -> None:
        """Test that credentials and gitignore can be excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"
            result = create_catalog_folder_structure(path, include_credentials=False)

            assert len(result.created_files) == 2
            assert (path / "base" / "globals.yml").exists()
            assert (path / "base" / "catalog.yml").exists()
            assert not (path / "local" / "credentials.yml").exists()
            assert not (path / "local" / ".gitignore").exists()

    def test_exclude_all_files(self) -> None:
        """Test excluding all files creates nothing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"
            result = create_catalog_folder_structure(
                path,
                include_globals=False,
                include_catalog=False,
                include_credentials=False,
            )

            assert len(result.created_files) == 0
            assert len(result.created_directories) == 0
            assert not result.success  # nothing was created

    def test_accepts_string_path(self) -> None:
        """Test that string paths are accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = str(Path(tmpdir) / "config")
            result = create_catalog_folder_structure(path)

            assert result.success


class TestCatalogStructureExists:
    """Tests for catalog_structure_exists function."""

    def test_returns_true_when_complete(self) -> None:
        """Test that returns True when all files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"
            create_catalog_folder_structure(path)

            assert catalog_structure_exists(path)

    def test_returns_false_when_missing_globals(self) -> None:
        """Test that returns False when globals.yml is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"
            create_catalog_folder_structure(path)

            (path / "base" / "globals.yml").unlink()

            assert not catalog_structure_exists(path)

    def test_returns_false_when_missing_catalog(self) -> None:
        """Test that returns False when catalog.yml is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"
            create_catalog_folder_structure(path)

            (path / "base" / "catalog.yml").unlink()

            assert not catalog_structure_exists(path)

    def test_returns_false_when_missing_credentials(self) -> None:
        """Test that returns False when credentials.yml is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"
            create_catalog_folder_structure(path)
            (path / "local" / "credentials.yml").unlink()

            assert not catalog_structure_exists(path)

    def test_returns_false_when_missing_gitignore(self) -> None:
        """Test that returns False when .gitignore is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"
            create_catalog_folder_structure(path)
            (path / "local" / ".gitignore").unlink()

            assert not catalog_structure_exists(path)

    def test_returns_false_when_path_not_exists(self) -> None:
        """Test that returns False when path does not exist."""
        assert not catalog_structure_exists("/nonexistent/path")

    def test_accepts_string_path(self) -> None:
        """Test that string paths are accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "config"
            create_catalog_folder_structure(path)

            assert catalog_structure_exists(str(path))
