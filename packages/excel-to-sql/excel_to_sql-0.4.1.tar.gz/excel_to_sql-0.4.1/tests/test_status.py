"""
Tests for status command.
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


class TestStatusCommand:
    """Tests for status command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_project(self, monkeypatch):
        """Create a temporary project with imports."""
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

    def test_status_no_imports(self, runner, temp_project):
        """Test status command when no imports have been performed."""
        result = runner.invoke(app, ["status"])

        assert result.exit_code == 0
        assert "No imports yet" in result.stdout
        assert "Run 'excel-to-sql import" in result.stdout

    def test_status_not_a_project(self, runner, tmp_path):
        """Test status command when not in an excel-to-sql project."""
        # Change to a temporary directory without project markers
        import os

        # Create temp dir without .git or pyproject.toml
        empty_dir = tmp_path / "empty_project"
        empty_dir.mkdir()

        # Mock from_current_directory to raise an exception
        def mock_error():
            raise ValueError("Not a project")

        import excel_to_sql.cli
        original_from_current = excel_to_sql.cli.Project.from_current_directory
        excel_to_sql.cli.Project.from_current_directory = mock_error

        try:
            result = runner.invoke(app, ["status"])
            assert result.exit_code == 1
            assert "Error:" in result.stdout
            assert "Not an excel-to-sql project" in result.stdout
        finally:
            excel_to_sql.cli.Project.from_current_directory = original_from_current

    def test_status_with_imports(self, runner, temp_project):
        """Test status command showing import history."""
        # Create an Excel file and import it
        data = pd.DataFrame(
            {
                "ID": [1, 2, 3],
                "Name": ["Product A", "Product B", "Product C"],
                "Price": [10.50, 20.00, 30.99],
            }
        )

        excel_path = temp_project.imports_dir / "products.xlsx"
        data.to_excel(excel_path, index=False)

        # Import the file
        import_result = runner.invoke(
            app, ["import", "--file", str(excel_path), "--type", "products"]
        )
        assert import_result.exit_code == 0

        # Check status
        status_result = runner.invoke(app, ["status"])

        assert status_result.exit_code == 0
        assert "Import History" in status_result.stdout
        assert "products.xlsx" in status_result.stdout
        assert "products" in status_result.stdout
        assert "Statistics:" in status_result.stdout
        assert "Total imports: 1" in status_result.stdout
        assert "Total rows: 3" in status_result.stdout
        assert "Success rate: 100.0%" in status_result.stdout
        assert "Last import:" in status_result.stdout

    def test_status_multiple_imports(self, runner, temp_project):
        """Test status command with multiple imports."""
        # Create and import first file
        data1 = pd.DataFrame(
            {
                "ID": [1, 2],
                "Name": ["Product A", "Product B"],
                "Price": [10.50, 20.00],
            }
        )

        excel1 = temp_project.imports_dir / "products1.xlsx"
        data1.to_excel(excel1, index=False)

        result1 = runner.invoke(
            app, ["import", "--file", str(excel1), "--type", "products"]
        )
        assert result1.exit_code == 0

        # Create and import second file
        data2 = pd.DataFrame(
            {
                "ID": [3, 4],
                "Name": ["Product C", "Product D"],
                "Price": [30.99, 40.50],
            }
        )

        excel2 = temp_project.imports_dir / "products2.xlsx"
        data2.to_excel(excel2, index=False)

        result2 = runner.invoke(
            app, ["import", "--file", str(excel2), "--type", "products"]
        )
        assert result2.exit_code == 0

        # Check status shows both imports
        status_result = runner.invoke(app, ["status"])

        assert status_result.exit_code == 0
        assert "Import History" in status_result.stdout
        assert "Total imports: 2" in status_result.stdout
        assert "Total rows: 4" in status_result.stdout
        assert "products1.xlsx" in status_result.stdout
        assert "products2.xlsx" in status_result.stdout

    def test_status_displays_table_format(self, runner, temp_project):
        """Test that status displays data in a table format."""
        # Import a file
        data = pd.DataFrame(
            {
                "ID": [1],
                "Name": ["Product A"],
                "Price": [10.50],
            }
        )

        excel_path = temp_project.imports_dir / "products.xlsx"
        data.to_excel(excel_path, index=False)

        import_result = runner.invoke(
            app, ["import", "--file", str(excel_path), "--type", "products"]
        )
        assert import_result.exit_code == 0

        # Check status has table columns
        status_result = runner.invoke(app, ["status"])

        assert status_result.exit_code == 0
        # Check for table headers/columns
        assert "Date" in status_result.stdout
        assert "File" in status_result.stdout
        assert "Type" in status_result.stdout
        assert "Rows" in status_result.stdout
        assert "Status" in status_result.stdout

    def test_status_shows_statistics(self, runner, temp_project):
        """Test that status command shows comprehensive statistics."""
        # Import a file with some skipped rows
        data = pd.DataFrame(
            {
                "ID": [1, 2, 3],
                "Name": ["Product A", "Product B", ""],  # Empty row
                "Price": [10.50, 20.00, 30.99],
            }
        )

        excel_path = temp_project.imports_dir / "products.xlsx"
        data.to_excel(excel_path, index=False)

        import_result = runner.invoke(
            app, ["import", "--file", str(excel_path), "--type", "products"]
        )
        assert import_result.exit_code == 0

        # Check statistics
        status_result = runner.invoke(app, ["status"])

        assert status_result.exit_code == 0
        assert "Statistics:" in status_result.stdout
        assert "Total imports:" in status_result.stdout
        assert "Total rows:" in status_result.stdout
        assert "Total skipped:" in status_result.stdout
        assert "Success rate:" in status_result.stdout
        assert "Last import:" in status_result.stdout
