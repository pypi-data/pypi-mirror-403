"""
Tests for Database entity.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil
import gc
import os

from excel_to_sql.entities.database import Database


def handle_remove_readonly(func, path, exc):
    """Handle Windows readonly files on cleanup."""
    import stat
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    return


def rmtree_with_retry(path):
    """Remove directory tree with retry for Windows file locks."""
    for _ in range(5):
        try:
            shutil.rmtree(path, onerror=handle_remove_readonly)
            return
        except PermissionError:
            gc.collect()
            import time
            time.sleep(0.1)
    # Final attempt, ignore errors
    try:
        shutil.rmtree(path, ignore_errors=True)
    except:
        pass


class TestDatabase:
    """Tests for Database entity."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        temp = Path(tempfile.mkdtemp())
        db_path = temp / "test.db"
        db = Database(db_path)
        db.initialize()
        yield db
        # Dispose engine to release file locks
        db.dispose()
        # Force garbage collection
        gc.collect()
        # Clean up temp directory with retry logic
        rmtree_with_retry(temp)

    def test_database_path(self, temp_db):
        """Test database path property."""
        assert isinstance(temp_db.path, Path)
        assert temp_db.path.name == "test.db"

    def test_database_exists(self, temp_db):
        """Test database exists property."""
        assert temp_db.exists

    def test_initialize_creates_file(self):
        """Test that initialize() creates database file."""
        temp = Path(tempfile.mkdtemp())
        db_path = temp / "new.db"

        db = Database(db_path)
        assert not db.exists

        db.initialize()
        assert db.exists

        # Dispose before cleanup
        db.dispose()
        gc.collect()
        rmtree_with_retry(temp)

    def test_initialize_creates_import_history_table(self, temp_db):
        """Test that _import_history table is created."""
        assert temp_db.table_exists("_import_history")

    def test_execute_insert(self, temp_db):
        """Test executing INSERT statement."""
        temp_db.execute("CREATE TABLE test_table (id INTEGER, name TEXT)")

        rows_affected = temp_db.execute(
            "INSERT INTO test_table (id, name) VALUES (1, 'test')"
        )

        assert rows_affected == 1

    def test_query_select(self, temp_db):
        """Test executing SELECT query."""
        temp_db.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        temp_db.execute("INSERT INTO test VALUES (1, 'Alice')")
        temp_db.execute("INSERT INTO test VALUES (2, 'Bob')")

        df = temp_db.query("SELECT * FROM test ORDER BY id")

        assert len(df) == 2
        assert df.iloc[0]["name"] == "Alice"
        assert df.iloc[1]["name"] == "Bob"

    def test_table_exists(self, temp_db):
        """Test checking if table exists."""
        temp_db.execute("CREATE TABLE test_table (id INTEGER)")

        assert temp_db.table_exists("test_table")
        assert not temp_db.table_exists("non_existent")

    def test_is_imported(self, temp_db):
        """Test checking if file hash is imported."""
        # Not imported initially
        assert not temp_db.is_imported("abc123")

        # Record import
        temp_db.record_import(
            file_name="test.xlsx",
            file_path="/path/to/test.xlsx",
            content_hash="abc123",
            file_type="test_type",
            rows_imported=100,
        )

        # Now imported
        assert temp_db.is_imported("abc123")

    def test_get_import_history(self, temp_db):
        """Test getting import history."""
        temp_db.record_import(
            file_name="file1.xlsx",
            file_path="/path1",
            content_hash="hash1",
            file_type="type1",
            rows_imported=10,
        )

        temp_db.record_import(
            file_name="file2.xlsx",
            file_path="/path2",
            content_hash="hash2",
            file_type="type2",
            rows_imported=20,
        )

        history = temp_db.get_import_history()
        assert len(history) == 2
        # Check both files are present (order may vary due to same timestamp)
        file_names = set(history["file_name"])
        assert "file1.xlsx" in file_names
        assert "file2.xlsx" in file_names

    def test_get_table_placeholder(self, temp_db):
        """Test getting a Table entity."""
        table = temp_db.get_table("test_table")
        # Now returns a Table entity (implemented in Phase 2)
        assert table is not None
        assert table.name == "test_table"
        assert table.exists is False  # Table doesn't exist yet

    def test_engine_property_cached(self, temp_db):
        """Test that engine property is cached."""
        engine1 = temp_db.engine
        engine2 = temp_db.engine

        # Should be the same object
        assert engine1 is engine2

    def test_record_import_with_optional_fields(self, temp_db):
        """Test recording import with all optional fields."""
        row_id = temp_db.record_import(
            file_name="test.xlsx",
            file_path="/path/to/test.xlsx",
            content_hash="hash123",
            file_type="test",
            rows_imported=50,
            rows_skipped=5,
            status="partial",
            import_duration_ms=1500,
            report_path="/path/to/report.json",
        )

        assert row_id > 0

        # Verify the record
        history = temp_db.query(
            "SELECT * FROM _import_history WHERE content_hash = :hash",
            {"hash": "hash123"},
        )
        assert len(history) == 1
        assert history.iloc[0]["status"] == "partial"
        assert history.iloc[0]["rows_skipped"] == 5
