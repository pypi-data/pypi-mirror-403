"""
Tests for Project entity.
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from excel_to_sql.entities.project import Project


class TestProject:
    """Tests for Project entity."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp = Path(tempfile.mkdtemp())
        yield temp
        shutil.rmtree(temp)

    def test_init_project(self, temp_dir):
        """Test creating a new project."""
        project = Project(root=temp_dir)

        assert project.root == temp_dir
        assert project.imports_dir == temp_dir / "imports"
        assert project.exports_dir == temp_dir / "exports"
        assert project.data_dir == temp_dir / "data"

    def test_initialize_creates_directories(self, temp_dir):
        """Test that initialize() creates directories."""
        project = Project(root=temp_dir)
        project.initialize()

        assert project.imports_dir.exists()
        assert project.exports_dir.exists()
        assert project.data_dir.exists()
        assert project.logs_dir.exists()
        assert project.config_dir.exists()

    def test_initialize_creates_database(self, temp_dir):
        """Test that initialize() creates database."""
        project = Project(root=temp_dir)
        project.initialize()

        assert project.database.exists
        assert project.database.path == temp_dir / "data" / "excel-to-sql.db"

    def test_initialize_creates_mappings(self, temp_dir):
        """Test that initialize() creates default mappings."""
        project = Project(root=temp_dir)
        project.initialize()

        assert project.mappings_file.exists()
        assert "_example" in project.mappings

    def test_add_mapping(self, temp_dir):
        """Test adding a new type mapping."""
        project = Project(root=temp_dir)
        project.initialize()

        project.add_mapping(
            type_name="orders",
            table_name="orders_table",
            primary_key=["id"],
            column_mappings={"id": {"target": "id", "type": "integer"}},
        )

        assert "orders" in project.mappings
        assert project.mappings["orders"]["target_table"] == "orders_table"

    def test_get_mapping(self, temp_dir):
        """Test getting a specific mapping."""
        project = Project(root=temp_dir)
        project.initialize()

        project.add_mapping(
            type_name="orders",
            table_name="orders",
            primary_key=["id"],
            column_mappings={},
        )

        mapping = project.get_mapping("orders")
        assert mapping is not None
        assert mapping["target_table"] == "orders"

    def test_list_types(self, temp_dir):
        """Test listing all configured types."""
        project = Project(root=temp_dir)
        project.initialize()

        project.add_mapping("type1", "table1", ["id"], {})
        project.add_mapping("type2", "table2", ["id"], {})

        types = project.list_types()
        assert "type1" in types
        assert "type2" in types
        assert "_example" in types

    def test_mappings_property_cached(self, temp_dir):
        """Test that mappings property is cached."""
        project = Project(root=temp_dir)
        project.initialize()

        # Access mappings twice
        mappings1 = project.mappings
        mappings2 = project.mappings

        # Should be the same object (cached)
        assert mappings1 is mappings2

    def test_database_property_lazy(self, temp_dir):
        """Test that database property is lazily created."""
        project = Project(root=temp_dir)
        project.initialize()

        # Access database
        db = project.database

        # Should be created now
        assert db is not None
        assert db.exists

    def test_from_current_directory(self, temp_dir):
        """Test creating Project from current directory."""
        # Change to temp directory
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            # Create project from current directory
            project = Project.from_current_directory()

            # Should have detected the root
            assert project.root == temp_dir

        finally:
            os.chdir(original_cwd)
