"""
Tests for Table entity.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil
import gc

from excel_to_sql.entities.database import Database
from excel_to_sql.entities.table import Table


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


class TestTable:
    """Tests for Table entity."""

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

    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame(
            {
                "id": [1, 2, 3],
                "name": ["Alice", "Bob", "Charlie"],
                "value": [10.5, 20.0, 30.5],
                "active": [True, False, True],
            }
        )

    def test_init_table(self, temp_db):
        """Test creating a Table entity."""
        table = Table(temp_db, "test_table")
        assert table.name == "test_table"

    def test_name_property(self, temp_db):
        """Test name property."""
        table = Table(temp_db, "products")
        assert table.name == "products"

    def test_exists_property_false(self, temp_db):
        """Test exists property when table doesn't exist."""
        table = Table(temp_db, "nonexistent")
        assert table.exists is False

    def test_exists_property_true(self, temp_db, sample_df):
        """Test exists property when table exists."""
        table = Table(temp_db, "test")
        table.create(sample_df, primary_key=["id"])
        assert table.exists is True

    def test_row_count_property(self, temp_db, sample_df):
        """Test row_count property."""
        table = Table(temp_db, "test")
        assert table.row_count == 0

        table.upsert(sample_df, primary_key=["id"])
        assert table.row_count == 3

    def test_columns_property(self, temp_db, sample_df):
        """Test columns property."""
        table = Table(temp_db, "test")
        assert table.columns == []

        table.create(sample_df, primary_key=["id"])
        assert set(table.columns) == {"id", "name", "value", "active"}

    def test_create_table_from_dataframe(self, temp_db, sample_df):
        """Test creating table from DataFrame schema."""
        table = Table(temp_db, "products")
        table.create(sample_df, primary_key=["id"])

        assert table.exists is True
        assert table.row_count == 0  # No data inserted yet

        # Check schema
        columns = table.columns
        assert "id" in columns
        assert "name" in columns
        assert "value" in columns
        assert "active" in columns

    def test_create_infer_types(self, temp_db):
        """Test type inference from DataFrame."""
        df = pd.DataFrame(
            {
                "int_col": [1, 2, 3],
                "float_col": [1.1, 2.2, 3.3],
                "str_col": ["a", "b", "c"],
                "bool_col": [True, False, True],
            }
        )

        table = Table(temp_db, "types_test")
        table.create(df, primary_key=["int_col"])

        # Query schema
        schema = temp_db.query("PRAGMA table_info(types_test)")

        # Check type mappings
        type_dict = {row["name"]: row["type"] for _, row in schema.iterrows()}

        assert type_dict["int_col"] == "INTEGER"
        assert type_dict["float_col"] == "REAL"
        assert type_dict["str_col"] == "TEXT"
        assert type_dict["bool_col"] == "BOOLEAN"

    def test_upsert_insert_new_rows(self, temp_db, sample_df):
        """Test upsert inserts new rows."""
        table = Table(temp_db, "products")
        stats = table.upsert(sample_df, primary_key=["id"])

        assert stats["inserted"] == 3
        assert stats["updated"] == 0
        assert stats["failed"] == 0
        assert table.row_count == 3

    def test_upsert_update_existing_rows(self, temp_db, sample_df):
        """Test upsert updates existing rows."""
        table = Table(temp_db, "products")

        # Insert initial data
        table.upsert(sample_df, primary_key=["id"])

        # Update with new values
        updated_df = pd.DataFrame(
            {
                "id": [1, 2],
                "name": ["Alice Updated", "Bob Updated"],
                "value": [99.9, 88.8],
                "active": [False, True],
            }
        )

        stats = table.upsert(updated_df, primary_key=["id"])

        assert stats["inserted"] == 0
        assert stats["updated"] == 2
        assert table.row_count == 3  # Still 3 rows total

        # Verify updates
        result = table.select_all()
        alice_row = result[result["id"] == 1].iloc[0]
        assert alice_row["name"] == "Alice Updated"
        assert alice_row["value"] == 99.9

    def test_upsert_mixed_insert_and_update(self, temp_db, sample_df):
        """Test upsert with both inserts and updates."""
        table = Table(temp_db, "products")

        # Insert initial data
        table.upsert(sample_df, primary_key=["id"])

        # Mix of updates (id=1,2) and inserts (id=4,5)
        mixed_df = pd.DataFrame(
            {
                "id": [1, 2, 4, 5],
                "name": ["Alice Updated", "Bob Updated", "David", "Eve"],
                "value": [99.9, 88.8, 40.0, 50.0],
                "active": [False, True, True, False],
            }
        )

        stats = table.upsert(mixed_df, primary_key=["id"])

        assert stats["inserted"] == 2  # id=4,5
        assert stats["updated"] == 2  # id=1,2
        assert table.row_count == 5

    def test_upsert_creates_table_if_not_exists(self, temp_db, sample_df):
        """Test upsert creates table if it doesn't exist."""
        table = Table(temp_db, "new_table")
        assert table.exists is False

        stats = table.upsert(sample_df, primary_key=["id"])

        assert table.exists is True
        assert stats["inserted"] == 3

    def test_upsert_with_null_values(self, temp_db):
        """Test upsert handles null values correctly."""
        df = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "name": ["Alice", None, "Charlie"],
                "value": [10.5, None, 30.5],
            }
        )

        table = Table(temp_db, "test")
        stats = table.upsert(df, primary_key=["id"])

        assert stats["inserted"] == 3
        assert table.row_count == 3

        # Verify nulls were preserved
        result = table.select_all()
        row2 = result[result["id"] == 2].iloc[0]
        assert pd.isna(row2["name"])
        assert pd.isna(row2["value"])

    def test_select_all(self, temp_db, sample_df):
        """Test selecting all rows from table."""
        table = Table(temp_db, "products")
        table.upsert(sample_df, primary_key=["id"])

        result = table.select_all()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert "id" in result.columns
        assert "name" in result.columns

    def test_truncate(self, temp_db, sample_df):
        """Test truncating table."""
        table = Table(temp_db, "products")
        table.upsert(sample_df, primary_key=["id"])

        assert table.row_count == 3

        table.truncate()

        assert table.row_count == 0
        assert table.exists is True  # Table still exists

    def test_drop(self, temp_db, sample_df):
        """Test dropping table."""
        table = Table(temp_db, "products")
        table.upsert(sample_df, primary_key=["id"])

        assert table.exists is True

        table.drop()

        assert table.exists is False

    def test_upsert_with_composite_primary_key(self, temp_db):
        """Test upsert with composite primary key."""
        df = pd.DataFrame(
            {
                "user_id": [1, 1, 2, 2],
                "product_id": [10, 20, 10, 20],
                "quantity": [5, 3, 7, 2],
            }
        )

        table = Table(temp_db, "orders")
        stats = table.upsert(df, primary_key=["user_id", "product_id"])

        assert stats["inserted"] == 4
        assert table.row_count == 4

        # Update one row
        update_df = pd.DataFrame(
            {
                "user_id": [1],
                "product_id": [10],
                "quantity": [99],
            }
        )

        stats = table.upsert(update_df, primary_key=["user_id", "product_id"])
        assert stats["updated"] == 1
        assert table.row_count == 4  # Still 4 rows

    def test_infer_sql_type_integer(self):
        """Test type inference for integers."""
        # This is tested indirectly through create_table_infer_types
        # but we can add specific type tests if needed
        pass

    def test_multiple_operations(self, temp_db, sample_df):
        """Test multiple table operations in sequence."""
        table = Table(temp_db, "products")

        # Insert
        stats1 = table.upsert(sample_df, primary_key=["id"])
        assert stats1["inserted"] == 3

        # Update
        update_df = pd.DataFrame(
            {"id": [1], "name": ["Updated"], "value": [99.9], "active": [True]}
        )
        stats2 = table.upsert(update_df, primary_key=["id"])
        assert stats2["updated"] == 1

        # Select
        result = table.select_all()
        assert len(result) == 3

        # Truncate
        table.truncate()
        assert table.row_count == 0

        # Insert again
        stats3 = table.upsert(sample_df, primary_key=["id"])
        assert stats3["inserted"] == 3
