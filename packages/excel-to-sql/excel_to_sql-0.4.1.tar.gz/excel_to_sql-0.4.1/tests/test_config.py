"""
Tests for config command.
"""

import pytest
from typer.testing import CliRunner
from pathlib import Path
import tempfile
import shutil
import gc
import pandas as pd

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


class TestConfigCommand:
    """Tests for config command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_project(self, monkeypatch):
        """Create a temporary project."""
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

        yield project

        # Cleanup
        project.database.dispose()
        gc.collect()
        rmtree_with_retry(temp)

    def test_config_list_empty(self, runner, temp_project):
        """Test config --list with no mappings."""
        result = runner.invoke(app, ["config", "--list"])

        assert result.exit_code == 0
        assert "No mappings configured" in result.stdout
        assert "--add-type" in result.stdout

    def test_config_list_with_mappings(self, runner, temp_project):
        """Test config --list with mappings configured."""
        # Add a mapping
        temp_project.add_mapping(
            type_name="products",
            table_name="products",
            primary_key=["id"],
            column_mappings={
                "ID": {"target": "id", "type": "integer"},
                "Name": {"target": "name", "type": "string"},
            },
        )

        result = runner.invoke(app, ["config", "--list"])

        assert result.exit_code == 0
        assert "products" in result.stdout
        assert "products" in result.stdout  # Table name
        assert "id" in result.stdout  # Primary key
        assert "2" in result.stdout  # Column count

    def test_config_show_existing_mapping(self, runner, temp_project):
        """Test config --show for existing mapping."""
        # Add a mapping
        temp_project.add_mapping(
            type_name="orders",
            table_name="orders_table",
            primary_key=["order_id"],
            column_mappings={
                "Order ID": {"target": "order_id", "type": "integer"},
                "Date": {"target": "date", "type": "date"},
            },
        )

        result = runner.invoke(app, ["config", "--show", "orders"])

        assert result.exit_code == 0
        assert "Mapping: orders" in result.stdout
        assert "orders_table" in result.stdout
        assert "order_id" in result.stdout
        assert "Order ID" in result.stdout
        assert "Date" in result.stdout

    def test_config_show_nonexistent_mapping(self, runner, temp_project):
        """Test config --show for non-existent mapping."""
        result = runner.invoke(app, ["config", "--show", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_config_add_type_basic(self, runner, temp_project):
        """Test config --add-type without auto-detection."""
        result = runner.invoke(
            app,
            [
                "config",
                "--add-type", "customers",
                "--table", "customers",
                "--pk", "id"
            ]
        )

        assert result.exit_code == 0
        assert "Created mapping for type 'customers'" in result.stdout
        assert "Table: customers" in result.stdout
        assert "Primary Key: id" in result.stdout
        assert "Columns: 0" in result.stdout

        # Verify mapping was created
        assert "customers" in temp_project.list_types()

    def test_config_add_type_with_auto_detect(self, runner, temp_project, tmp_path):
        """Test config --add-type with auto-detection from Excel file."""
        # Create an Excel file
        data = pd.DataFrame({
            "ID": [1, 2, 3],
            "Name": ["Alice", "Bob", "Charlie"],
            "Score": [95.5, 87.3, 92.1],
        })

        excel_file = tmp_path / "test.xlsx"
        data.to_excel(excel_file, index=False)

        result = runner.invoke(
            app,
            [
                "config",
                "--add-type", "students",
                "--table", "students",
                "--pk", "id",
                "--file", str(excel_file)
            ]
        )

        assert result.exit_code == 0
        assert "Auto-detecting columns" in result.stdout
        assert "Detected 3 columns" in result.stdout
        assert "Created mapping for type 'students'" in result.stdout

        # Verify mapping was created with columns
        mapping = temp_project.get_mapping("students")
        assert mapping is not None
        assert len(mapping["column_mappings"]) == 3

    def test_config_add_type_missing_table(self, runner, temp_project):
        """Test config --add-type without --table."""
        result = runner.invoke(
            app,
            ["config", "--add-type", "test", "--pk", "id"]
        )

        assert result.exit_code == 1
        assert "--table is required" in result.stdout

    def test_config_add_type_missing_pk(self, runner, temp_project):
        """Test config --add-type without --pk."""
        result = runner.invoke(
            app,
            ["config", "--add-type", "test", "--table", "test_table"]
        )

        assert result.exit_code == 1
        assert "--pk is required" in result.stdout

    def test_config_add_type_duplicate(self, runner, temp_project):
        """Test config --add-type with duplicate type name."""
        # Add initial mapping
        temp_project.add_mapping(
            type_name="products",
            table_name="products",
            primary_key=["id"],
            column_mappings={}
        )

        # Try to add again
        result = runner.invoke(
            app,
            [
                "config",
                "--add-type", "products",
                "--table", "products2",
                "--pk", "id"
            ]
        )

        assert result.exit_code == 1
        assert "already exists" in result.stdout

    def test_config_add_type_composite_pk(self, runner, temp_project):
        """Test config --add-type with composite primary key."""
        result = runner.invoke(
            app,
            [
                "config",
                "--add-type", "order_items",
                "--table", "order_items",
                "--pk", "order_id,product_id"
            ]
        )

        assert result.exit_code == 0
        assert "Created mapping for type 'order_items'" in result.stdout
        assert "Primary Key: order_id, product_id" in result.stdout

        # Verify composite PK was saved
        mapping = temp_project.get_mapping("order_items")
        assert mapping["primary_key"] == ["order_id", "product_id"]

    def test_config_remove_existing(self, runner, temp_project):
        """Test config --remove for existing mapping."""
        # Add a mapping
        temp_project.add_mapping(
            type_name="temp",
            table_name="temp_table",
            primary_key=["id"],
            column_mappings={}
        )

        # Remove it
        result = runner.invoke(app, ["config", "--remove", "temp"])

        assert result.exit_code == 0
        assert "Removed mapping 'temp'" in result.stdout

        # Verify it's gone
        assert "temp" not in temp_project.list_types()

    def test_config_remove_nonexistent(self, runner, temp_project):
        """Test config --remove for non-existent mapping."""
        result = runner.invoke(app, ["config", "--remove", "nonexistent"])

        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_config_validate_all_valid(self, runner, temp_project):
        """Test config --validate with all valid mappings."""
        # Add valid mappings
        temp_project.add_mapping(
            type_name="products",
            table_name="products",
            primary_key=["id"],
            column_mappings={
                "ID": {"target": "id", "type": "integer"},
            }
        )

        result = runner.invoke(app, ["config", "--validate"])

        assert result.exit_code == 0
        assert "Validating mappings" in result.stdout
        assert "are valid" in result.stdout

    def test_config_validate_with_errors(self, runner, temp_project):
        """Test config --validate with invalid mappings."""
        # Add invalid mapping (missing column_mappings)
        temp_project.add_mapping(
            type_name="invalid",
            table_name="invalid_table",
            primary_key=["nonexistent_col"],  # This column doesn't exist in column_mappings
            column_mappings={}
        )

        result = runner.invoke(app, ["config", "--validate"])

        assert result.exit_code == 0
        assert "Validating mappings" in result.stdout
        assert "error(s)" in result.stdout
        assert "invalid" in result.stdout

    def test_config_not_a_project(self, runner, tmp_path):
        """Test config command when not in an excel-to-sql project."""
        empty_dir = tmp_path / "empty_project"
        empty_dir.mkdir()

        # Mock from_current_directory to raise an exception
        def mock_error():
            raise ValueError("Not a project")

        import excel_to_sql.cli
        original_from_current = excel_to_sql.cli.Project.from_current_directory
        excel_to_sql.cli.Project.from_current_directory = mock_error

        try:
            result = runner.invoke(app, ["config", "--list"])
            assert result.exit_code == 1
            assert "Not an excel-to-sql project" in result.stdout
        finally:
            excel_to_sql.cli.Project.from_current_directory = original_from_current

    def test_config_default_shows_help(self, runner, temp_project):
        """Test config with no options shows help."""
        result = runner.invoke(app, ["config"])

        assert result.exit_code == 0
        assert "Usage:" in result.stdout
        assert "--add-type" in result.stdout
        assert "--list" in result.stdout
        assert "--show" in result.stdout
        assert "--remove" in result.stdout
        assert "--validate" in result.stdout


class TestProjectConfigMethods:
    """Tests for Project entity config methods."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project."""
        temp = tmp_path / "project"
        temp.mkdir()

        # Add .git marker
        (temp / ".git").mkdir()

        project = Project(root=temp)
        project.initialize()

        yield project

        # Cleanup
        project.database.dispose()
        gc.collect()
        rmtree_with_retry(temp)

    def test_remove_mapping_existing(self, temp_project):
        """Test remove_mapping() with existing mapping."""
        temp_project.add_mapping(
            type_name="test",
            table_name="test_table",
            primary_key=["id"],
            column_mappings={}
        )

        result = temp_project.remove_mapping("test")

        assert result is True
        assert "test" not in temp_project.list_types()

    def test_remove_mapping_nonexistent(self, temp_project):
        """Test remove_mapping() with non-existent mapping."""
        result = temp_project.remove_mapping("nonexistent")

        assert result is False

    def test_validate_mappings_all_valid(self, temp_project):
        """Test validate_mappings() with all valid mappings."""
        temp_project.add_mapping(
            type_name="valid",
            table_name="valid_table",
            primary_key=["id"],
            column_mappings={
                "ID": {"target": "id", "type": "integer"}
            }
        )

        errors = temp_project.validate_mappings()

        # Should be valid since target "id" matches primary key
        assert len(errors) == 0

    def test_validate_mappings_missing_required_field(self, temp_project):
        """Test validate_mappings() with missing required field."""
        temp_project.add_mapping(
            type_name="invalid",
            table_name="invalid_table",
            primary_key=["id"],
            column_mappings={}  # Missing in validation
        )
        # Remove required field manually
        mappings = temp_project.mappings
        del mappings["invalid"]["column_mappings"]
        temp_project._save_mappings(mappings)

        errors = temp_project.validate_mappings()

        assert len(errors) > 0
        assert any(e["type"] == "invalid" for e in errors)
        assert any("Missing required field" in e["error"] for e in errors)

    def test_validate_mappings_pk_not_in_columns(self, temp_project):
        """Test validate_mappings() with PK not in column_mappings."""
        temp_project.add_mapping(
            type_name="invalid",
            table_name="invalid_table",
            primary_key=["missing_column"],
            column_mappings={
                "ID": {"target": "id", "type": "integer"}
            }
        )

        errors = temp_project.validate_mappings()

        assert len(errors) > 0
        assert any("missing_column" in e["error"] for e in errors)

    def test_auto_detect_columns(self, temp_project, tmp_path):
        """Test auto_detect_columns()."""
        # Create test Excel file
        data = pd.DataFrame({
            "ID": [1, 2, 3],
            "Name": ["A", "B", "C"],
            "Price": [10.5, 20.0, 30.99],
            "Active": [True, False, True],
        })

        excel_file = tmp_path / "test.xlsx"
        data.to_excel(excel_file, index=False)

        columns = temp_project.auto_detect_columns(str(excel_file))

        assert "ID" in columns
        assert columns["ID"] == "integer"
        assert "Name" in columns
        assert columns["Name"] == "string"
        assert "Price" in columns
        assert columns["Price"] == "float"
        assert "Active" in columns
        assert columns["Active"] == "boolean"
