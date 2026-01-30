"""
Tests for ExcelFile entity.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil
import gc

from excel_to_sql.entities.excel_file import ExcelFile


def rmtree_with_retry(path):
    """Remove directory tree with retry for Windows file locks."""
    for _ in range(5):
        try:
            shutil.rmtree(path, ignore_errors=True)
            return
        except PermissionError:
            gc.collect()
            import time

            time.sleep(0.1)
    try:
        shutil.rmtree(path, ignore_errors=True)
    except:
        pass


class TestExcelFile:
    """Tests for ExcelFile entity."""

    @pytest.fixture
    def temp_excel(self):
        """Create a temporary Excel file for testing."""
        temp = Path(tempfile.mkdtemp())

        # Create a simple Excel file
        data = pd.DataFrame(
            {"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"], "value": [10, 20, 30]}
        )
        excel_path = temp / "test.xlsx"
        data.to_excel(excel_path, index=False)

        yield excel_path

        # Clean up
        gc.collect()
        rmtree_with_retry(temp)

    @pytest.fixture
    def sample_fixture(self):
        """Get path to sample_data.xlsx fixture."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        return fixtures_dir / "sample_data.xlsx"

    def test_init_with_path(self, temp_excel):
        """Test creating ExcelFile with path."""
        file = ExcelFile(temp_excel)
        assert file.path == temp_excel

    def test_path_property(self, temp_excel):
        """Test path property."""
        file = ExcelFile(temp_excel)
        assert isinstance(file.path, Path)
        assert file.path.name == "test.xlsx"

    def test_name_property(self, temp_excel):
        """Test name property."""
        file = ExcelFile(temp_excel)
        assert file.name == "test.xlsx"

    def test_exists_property_true(self, temp_excel):
        """Test exists property when file exists."""
        file = ExcelFile(temp_excel)
        assert file.exists is True

    def test_exists_property_false(self):
        """Test exists property when file doesn't exist."""
        file = ExcelFile("nonexistent.xlsx")
        assert file.exists is False

    def test_read_excel_file(self, temp_excel):
        """Test reading Excel file."""
        file = ExcelFile(temp_excel)
        df = file.read()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "id" in df.columns
        assert "name" in df.columns
        assert "value" in df.columns

    def test_read_nonexistent_file(self):
        """Test reading nonexistent file raises error."""
        file = ExcelFile("nonexistent.xlsx")

        with pytest.raises(FileNotFoundError):
            file.read()

    def test_read_invalid_file(self, tmp_path):
        """Test reading non-Excel file raises error."""
        # Create a text file
        text_file = tmp_path / "test.txt"
        text_file.write_text("not an excel file")

        file = ExcelFile(text_file)

        with pytest.raises(ValueError, match="Not an Excel file"):
            file.read()

    def test_content_hash_consistency(self, temp_excel):
        """Test that content hash is consistent."""
        file = ExcelFile(temp_excel)
        hash1 = file.content_hash
        hash2 = file.content_hash

        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters

    def test_content_hash_cached(self, temp_excel):
        """Test that content hash is cached."""
        file = ExcelFile(temp_excel)

        # Access hash twice
        hash1 = file.content_hash
        hash2 = file.content_hash

        # Should be the same object (cached)
        assert hash1 == hash2

    def test_content_hash_different_content(self, temp_excel, tmp_path):
        """Test that different content produces different hashes."""
        # Create two different Excel files
        data1 = pd.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        file1_path = tmp_path / "file1.xlsx"
        data1.to_excel(file1_path, index=False)

        data2 = pd.DataFrame({"id": [1, 2, 3], "value": [99, 99, 99]})
        file2_path = tmp_path / "file2.xlsx"
        data2.to_excel(file2_path, index=False)

        file1 = ExcelFile(file1_path)
        file2 = ExcelFile(file2_path)

        assert file1.content_hash != file2.content_hash

    def test_content_hash_same_data_different_column_order(self, tmp_path):
        """Test that same data with different column order produces same hash."""
        data1 = pd.DataFrame({"id": [1, 2, 3], "name": ["A", "B", "C"]})
        file1_path = tmp_path / "file1.xlsx"
        data1.to_excel(file1_path, index=False)

        data2 = pd.DataFrame({"name": ["A", "B", "C"], "id": [1, 2, 3]})
        file2_path = tmp_path / "file2.xlsx"
        data2.to_excel(file2_path, index=False)

        file1 = ExcelFile(file1_path)
        file2 = ExcelFile(file2_path)

        # Hash should be the same since columns are sorted internally
        assert file1.content_hash == file2.content_hash

    def test_validate_valid_file(self, temp_excel):
        """Test validation of valid Excel file."""
        file = ExcelFile(temp_excel)
        assert file.validate() is True

    def test_validate_nonexistent_file(self):
        """Test validation of nonexistent file."""
        file = ExcelFile("nonexistent.xlsx")
        assert file.validate() is False

    def test_validate_non_excel_file(self, tmp_path):
        """Test validation of non-Excel file."""
        text_file = tmp_path / "test.txt"
        text_file.write_text("not excel")

        file = ExcelFile(text_file)
        assert file.validate() is False

    def test_read_sample_fixture(self, sample_fixture):
        """Test reading the sample fixture file."""
        file = ExcelFile(sample_fixture)

        assert file.exists is True
        assert file.validate() is True

        df = file.read()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 100  # Sample fixture has 100 rows
        assert "id" in df.columns
        assert "name" in df.columns
        assert "quantity" in df.columns
        assert "price" in df.columns

    def test_read_with_sheet_name(self, tmp_path):
        """Test reading specific sheet by name."""
        # Create Excel with multiple sheets
        data = pd.DataFrame({"a": [1, 2, 3]})
        excel_path = tmp_path / "test.xlsx"

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            data.to_excel(writer, sheet_name="Sheet1", index=False)
            data.to_excel(writer, sheet_name="Sheet2", index=False)

        file = ExcelFile(excel_path)
        df1 = file.read(sheet_name="Sheet1")
        df2 = file.read(sheet_name="Sheet2")

        assert len(df1) == 3
        assert len(df2) == 3

    def test_content_hash_triggers_read(self, temp_excel):
        """Test that accessing content_hash triggers file read."""
        file = ExcelFile(temp_excel)

        # Access hash (should read file internally)
        hash_value = file.content_hash

        assert hash_value is not None
        assert len(hash_value) == 64
