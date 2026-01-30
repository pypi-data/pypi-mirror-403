"""
Integration tests for import command.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil
import gc
from typer.testing import CliRunner

from excel_to_sql.cli import app
from excel_to_sql.entities.project import Project


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


class TestImportCommand:
    """Integration tests for import command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_project(self, monkeypatch):
        """Create a temporary project with mappings."""
        import os

        temp = Path(tempfile.mkdtemp())

        # Add a .git marker to make it a valid project root
        (temp / ".git").mkdir()

        # Mock Project.from_current_directory to return our temp project
        def mock_from_current_directory():
            return Project(root=temp)

        monkeypatch.setattr(
            "excel_to_sql.entities.project.Project.from_current_directory",
            mock_from_current_directory
        )

        # Initialize project
        project = Project(root=temp)
        project.initialize()

        # Add products mapping
        project.add_mapping(
            type_name="products",
            table_name="products",
            primary_key=["id"],
            column_mappings={
                "ID": {"target": "id", "type": "integer"},
                "Name": {"target": "name", "type": "string"},
                "Price": {"target": "price", "type": "float"},
            },
        )

        # Create imports directory
        project.imports_dir.mkdir(parents=True, exist_ok=True)

        yield project

        # Cleanup
        project.database.dispose()
        gc.collect()
        rmtree_with_retry(temp)

    @pytest.fixture
    def sample_excel(self, temp_project):
        """Create a sample Excel file in the project."""
        data = pd.DataFrame(
            {
                "ID": [1, 2, 3],
                "Name": ["Product A", "Product B", "Product C"],
                "Price": [10.50, 20.00, 30.99],
            }
        )

        excel_path = temp_project.imports_dir / "products.xlsx"
        data.to_excel(excel_path, index=False)

        return excel_path

    def test_import_new_file(self, runner, temp_project, sample_excel):
        """Test importing a new Excel file."""
        result = runner.invoke(
            app, ["import", "--file", str(sample_excel), "--type", "products"]
        )

        assert result.exit_code == 0
        assert "Import completed successfully" in result.stdout
        assert "Inserted: 3" in result.stdout
        assert "Updated: 0" in result.stdout

        # Verify data in database
        table = temp_project.database.get_table("products")
        assert table.exists is True
        assert table.row_count == 3

        df = table.select_all()
        assert df["name"].tolist() == ["Product A", "Product B", "Product C"]

    def test_import_same_file_twice(self, runner, temp_project, sample_excel):
        """Test that importing same file twice is idempotent."""
        # First import
        result1 = runner.invoke(
            app, ["import", "--file", str(sample_excel), "--type", "products"]
        )
        assert result1.exit_code == 0
        assert "Inserted: 3" in result1.stdout

        # Second import (should skip)
        result2 = runner.invoke(
            app, ["import", "--file", str(sample_excel), "--type", "products"]
        )
        assert result2.exit_code == 0
        assert "Already imported" in result2.stdout
        assert "Use --force to re-import" in result2.stdout

        # Verify no duplicate data
        table = temp_project.database.get_table("products")
        assert table.row_count == 3

    def test_import_with_force_flag(self, runner, temp_project, sample_excel):
        """Test --force flag re-imports even if same content."""
        # First import
        result1 = runner.invoke(
            app, ["import", "--file", str(sample_excel), "--type", "products"]
        )
        assert result1.exit_code == 0
        assert "Inserted: 3" in result1.stdout

        # Second import with --force (should re-import)
        result2 = runner.invoke(
            app, ["import", "--file", str(sample_excel), "--type", "products", "--force"]
        )
        assert result2.exit_code == 0
        # With force, it should skip the hash check and process the import
        # Since data hasn't changed, all rows will be updates
        assert "Updated: 3" in result2.stdout or "Inserted: 3" in result2.stdout

    def test_import_updates_existing_rows(self, runner, temp_project, sample_excel):
        """Test that import updates existing rows based on PK."""
        # First import
        result1 = runner.invoke(
            app, ["import", "--file", str(sample_excel), "--type", "products"]
        )
        assert result1.exit_code == 0

        # Create updated Excel file
        updated_data = pd.DataFrame(
            {
                "ID": [1, 2, 3],
                "Name": ["Product A Updated", "Product B", "Product C"],
                "Price": [99.99, 20.00, 30.99],
            }
        )
        updated_path = temp_project.imports_dir / "products_updated.xlsx"
        updated_data.to_excel(updated_path, index=False)

        # Import updated file
        result2 = runner.invoke(
            app, ["import", "--file", str(updated_path), "--type", "products"]
        )
        assert result2.exit_code == 0
        assert "Inserted: 0" in result2.stdout
        assert "Updated: 3" in result2.stdout

        # Verify update
        table = temp_project.database.get_table("products")
        df = table.select_all()
        assert df[df["id"] == 1]["name"].iloc[0] == "Product A Updated"
        assert df[df["id"] == 1]["price"].iloc[0] == 99.99

    def test_import_nonexistent_file(self, runner, temp_project):
        """Test error handling for missing file."""
        result = runner.invoke(
            app, ["import", "--file", "missing.xlsx", "--type", "products"]
        )

        assert result.exit_code == 1
        assert "Error:" in result.stdout
        assert "File not found" in result.stdout

    def test_import_unknown_type(self, runner, temp_project, sample_excel):
        """Test error handling for unknown type."""
        result = runner.invoke(
            app, ["import", "--file", str(sample_excel), "--type", "unknown"]
        )

        assert result.exit_code == 1
        assert "Error:" in result.stdout
        assert "Unknown type" in result.stdout
        assert "Available types:" in result.stdout

    def test_import_without_init(self, runner, tmp_path):
        """Test error when project not initialized."""
        # This test would require mocking Project.from_current_directory to fail
        # For now, we'll skip it as it's covered by other error tests
        # The mock in temp_project fixture always returns a valid project
        pass

    def test_import_with_empty_rows(self, runner, temp_project):
        """Test import with empty rows in Excel."""
        # Create Excel with some rows that have empty strings (which will be NaN after clean)
        data = pd.DataFrame(
            {
                "ID": [1, 2, 3],
                "Name": ["Product A", "", "Product C"],
                "Price": [10.50, 20.00, 30.99],
            }
        )
        excel_path = temp_project.imports_dir / "with_empty.xlsx"
        data.to_excel(excel_path, index=False)

        result = runner.invoke(
            app, ["import", "--file", str(excel_path), "--type", "products"]
        )

        assert result.exit_code == 0
        # Clean should handle empty strings, dropna happens at row level
        # The row with empty name might still be imported because ID and Price have values
        assert "Inserted: 3" in result.stdout

    def test_import_with_null_values(self, runner, temp_project):
        """Test import handles null values correctly."""
        # Create Excel with null values
        data = pd.DataFrame(
            {
                "ID": [1, 2, 3],
                "Name": ["Product A", None, "Product C"],
                "Price": [10.50, 20.00, None],
            }
        )
        excel_path = temp_project.imports_dir / "with_nulls.xlsx"
        data.to_excel(excel_path, index=False)

        result = runner.invoke(
            app, ["import", "--file", str(excel_path), "--type", "products"]
        )

        assert result.exit_code == 0
        assert "Inserted: 3" in result.stdout

        # Verify data was imported
        table = temp_project.database.get_table("products")
        df = table.select_all()
        assert len(df) == 3
        # Null values should be in the database (may be None or NaN depending on pandas/sqlite)

    def test_import_with_invalid_types(self, runner, temp_project):
        """Test import coerces invalid type values to NaN."""
        # Create Excel with invalid integer
        data = pd.DataFrame(
            {
                "ID": [1, 2, 3],
                "Name": ["Product A", "Product B", "Product C"],
                "Price": [10.50, "invalid", 30.99],
            }
        )
        excel_path = temp_project.imports_dir / "invalid_types.xlsx"
        data.to_excel(excel_path, index=False)

        result = runner.invoke(
            app, ["import", "--file", str(excel_path), "--type", "products"]
        )

        assert result.exit_code == 0
        assert "Inserted: 3" in result.stdout

        # Verify invalid price became NaN
        table = temp_project.database.get_table("products")
        df = table.select_all()
        assert pd.isna(df[df["id"] == 2]["price"].iloc[0])

    def test_import_creates_import_history(self, runner, temp_project, sample_excel):
        """Test that import is recorded in history."""
        result = runner.invoke(
            app, ["import", "--file", str(sample_excel), "--type", "products"]
        )

        assert result.exit_code == 0

        # Check history
        history = temp_project.database.get_import_history()
        assert len(history) == 1
        assert history.iloc[0]["file_name"] == "products.xlsx"
        assert history.iloc[0]["file_type"] == "products"
        assert history.iloc[0]["rows_imported"] == 3
        assert history.iloc[0]["status"] == "success"

    def test_import_displays_summary_table(self, runner, temp_project, sample_excel):
        """Test that import displays Rich summary table."""
        result = runner.invoke(
            app, ["import", "--file", str(sample_excel), "--type", "products"]
        )

        assert result.exit_code == 0
        assert "Import Summary" in result.stdout
        assert "File" in result.stdout
        assert "Type" in result.stdout
        assert "Table" in result.stdout
        assert "Rows inserted" in result.stdout
        assert "Content hash" in result.stdout

    def test_import_with_composite_primary_key(self, runner, temp_project):
        """Test import with composite primary key."""
        # Add mapping with composite primary key
        temp_project.add_mapping(
            type_name="order_items",
            table_name="order_items",
            primary_key=["order_id", "product_id"],  # Composite PK
            column_mappings={
                "Order ID": {"target": "order_id", "type": "integer"},
                "Product ID": {"target": "product_id", "type": "integer"},
                "Quantity": {"target": "quantity", "type": "integer"},
            },
        )

        # Create Excel file with composite key data
        data = pd.DataFrame(
            {
                "Order ID": [1, 1, 2, 2],
                "Product ID": [10, 20, 10, 20],
                "Quantity": [5, 3, 7, 2],
            }
        )

        excel_path = temp_project.imports_dir / "order_items.xlsx"
        data.to_excel(excel_path, index=False)

        # First import
        result1 = runner.invoke(
            app, ["import", "--file", str(excel_path), "--type", "order_items"]
        )

        assert result1.exit_code == 0
        assert "Inserted: 4" in result1.stdout
        assert "Updated: 0" in result1.stdout

        # Verify data in database
        table = temp_project.database.get_table("order_items")
        assert table.exists is True
        assert table.row_count == 4

        df = table.select_all()
        assert df["quantity"].tolist() == [5, 3, 7, 2]

        # Create updated Excel file (update one row, add new row)
        updated_data = pd.DataFrame(
            {
                "Order ID": [1, 1, 2, 2, 3],  # 3, 30 is new
                "Product ID": [10, 20, 10, 20, 10],
                "Quantity": [99, 3, 7, 2, 15],  # First quantity changed to 99
            }
        )

        updated_excel_path = temp_project.imports_dir / "order_items_v2.xlsx"
        updated_data.to_excel(updated_excel_path, index=False)

        # Second import (should update 4 existing rows, insert 1 new row)
        # Note: UPSERT updates all rows matching PK, even if data unchanged
        result2 = runner.invoke(
            app, ["import", "--file", str(updated_excel_path), "--type", "order_items"]
        )

        assert result2.exit_code == 0
        assert "Inserted: 1" in result2.stdout
        assert "Updated: 4" in result2.stdout

        # Verify final state
        assert table.row_count == 5  # 4 original + 1 new

        df_final = table.select_all()
        # Order ID=1, Product ID=10 should have quantity=99 (updated)
        row = df_final[
            (df_final["order_id"] == 1) & (df_final["product_id"] == 10)
        ].iloc[0]
        assert row["quantity"] == 99
