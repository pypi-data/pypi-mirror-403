"""
Tests for metadata storage.
"""

import pytest
from pathlib import Path
from datetime import datetime
from excel_to_sql.metadata.store import MetadataStore
from excel_to_sql.metadata.models import ImportMetadata


class TestImportMetadata:
    """Tests for ImportMetadata model."""

    def test_create_metadata(self):
        """Test creating import metadata."""
        metadata = ImportMetadata(
            file_name="test.xlsx",
            file_type="products",
            table_name="products",
            row_count=100,
            column_count=5,
            content_hash="abc123",
            tags=["import", "test"],
            custom_metadata={"source": "manual"}
        )

        assert metadata.file_name == "test.xlsx"
        assert metadata.file_type == "products"
        assert metadata.table_name == "products"
        assert metadata.row_count == 100
        assert metadata.column_count == 5
        assert metadata.content_hash == "abc123"
        assert "import" in metadata.tags
        assert metadata.custom_metadata["source"] == "manual"

    def test_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = ImportMetadata(
            file_name="test.xlsx",
            file_type="products",
            table_name="products",
            row_count=100,
            column_count=5,
            content_hash="abc123",
            tags=["test"]
        )

        d = metadata.to_dict()

        assert d["file_name"] == "test.xlsx"
        assert d["row_count"] == 100
        assert isinstance(d["timestamp"], str)

    def test_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            "file_name": "test.xlsx",
            "file_type": "products",
            "table_name": "products",
            "row_count": 100,
            "column_count": 5,
            "content_hash": "abc123",
            "tags": ["test"],
            "custom_metadata": {},
            "timestamp": "2024-01-01T00:00:00"
        }

        metadata = ImportMetadata.from_dict(data)

        assert metadata.file_name == "test.xlsx"
        assert metadata.row_count == 100


class TestMetadataStore:
    """Tests for MetadataStore."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create temporary directory for metadata store."""
        return tmp_path

    @pytest.fixture
    def store(self, temp_dir):
        """Create metadata store."""
        return MetadataStore(temp_dir)

    @pytest.fixture
    def sample_metadata(self):
        """Create sample metadata."""
        return ImportMetadata(
            file_name="test.xlsx",
            file_type="products",
            table_name="products",
            row_count=100,
            column_count=5,
            content_hash="abc123",
            tags=["import", "test"]
        )

    def test_save_metadata(self, store, sample_metadata):
        """Test saving metadata."""
        store.save(sample_metadata)

        # Verify it was saved
        retrieved = store.get_by_hash("abc123")
        assert retrieved is not None
        assert retrieved.file_name == "test.xlsx"
        assert retrieved.row_count == 100

    def test_get_by_hash(self, store, sample_metadata):
        """Test getting metadata by hash."""
        store.save(sample_metadata)

        retrieved = store.get_by_hash("abc123")
        assert retrieved is not None

        # Test non-existent hash
        not_found = store.get_by_hash("nonexistent")
        assert not_found is None

    def test_get_by_tag(self, store, temp_dir):
        """Test getting metadata by tag."""
        metadata1 = ImportMetadata(
            file_name="test1.xlsx",
            file_type="products",
            table_name="products",
            row_count=100,
            column_count=5,
            content_hash="hash1",
            tags=["import", "products"]
        )

        metadata2 = ImportMetadata(
            file_name="test2.xlsx",
            file_type="categories",
            table_name="categories",
            row_count=50,
            column_count=3,
            content_hash="hash2",
            tags=["import", "categories"]
        )

        metadata3 = ImportMetadata(
            file_name="test3.xlsx",
            file_type="products",
            table_name="products",
            row_count=200,
            column_count=5,
            content_hash="hash3",
            tags=["import", "products"]
        )

        store.save(metadata1)
        store.save(metadata2)
        store.save(metadata3)

        # Get by tag
        products = store.get_by_tag("products")
        assert len(products) == 2

        categories = store.get_by_tag("categories")
        assert len(categories) == 1

    def test_get_by_table(self, store, temp_dir):
        """Test getting metadata by table name."""
        metadata1 = ImportMetadata(
            file_name="test1.xlsx",
            file_type="products",
            table_name="products",
            row_count=100,
            column_count=5,
            content_hash="hash1"
        )

        metadata2 = ImportMetadata(
            file_name="test2.xlsx",
            file_type="categories",
            table_name="categories",
            row_count=50,
            column_count=3,
            content_hash="hash2"
        )

        store.save(metadata1)
        store.save(metadata2)

        # Get by table
        products = store.get_by_table("products")
        assert len(products) == 1
        assert products[0].table_name == "products"

    def test_list_all(self, store, temp_dir):
        """Test listing all metadata."""
        metadata1 = ImportMetadata(
            file_name="test1.xlsx",
            file_type="type1",
            table_name="table1",
            row_count=100,
            column_count=5,
            content_hash="hash1"
        )

        metadata2 = ImportMetadata(
            file_name="test2.xlsx",
            file_type="type2",
            table_name="table2",
            row_count=50,
            column_count=3,
            content_hash="hash2"
        )

        store.save(metadata1)
        store.save(metadata2)

        all_metadata = store.list_all()
        assert len(all_metadata) == 2

    def test_delete(self, store, sample_metadata):
        """Test deleting metadata."""
        store.save(sample_metadata)

        # Verify it exists
        assert store.get_by_hash("abc123") is not None

        # Delete it
        result = store.delete("abc123")
        assert result is True

        # Verify it's gone
        assert store.get_by_hash("abc123") is None

    def test_delete_nonexistent(self, store):
        """Test deleting non-existent metadata."""
        result = store.delete("nonexistent")
        assert result is False

    def test_search(self, store, temp_dir):
        """Test searching metadata."""
        metadata1 = ImportMetadata(
            file_name="products.xlsx",
            file_type="products",
            table_name="products",
            row_count=100,
            column_count=5,
            content_hash="hash1",
            tags=["import"]
        )

        metadata2 = ImportMetadata(
            file_name="categories.xlsx",
            file_type="categories",
            table_name="categories",
            row_count=50,
            column_count=3,
            content_hash="hash2",
            tags=["import", "manual"]
        )

        store.save(metadata1)
        store.save(metadata2)

        # Search by table name
        results = store.search({"table_name": "products"})
        assert len(results) == 1

        # Search by tag
        results = store.search({"tags": ["manual"]})
        assert len(results) == 1

        # Search with multiple criteria
        results = store.search({"table_name": "products", "tags": ["import"]})
        assert len(results) == 1

    def test_timestamp_ordering(self, store, temp_dir):
        """Test that metadata is ordered by timestamp."""
        metadata1 = ImportMetadata(
            file_name="test1.xlsx",
            file_type="type1",
            table_name="table1",
            row_count=100,
            column_count=5,
            content_hash="hash1",
            timestamp="2024-01-01T00:00:00"
        )

        metadata2 = ImportMetadata(
            file_name="test2.xlsx",
            file_type="type2",
            table_name="table2",
            row_count=50,
            column_count=3,
            content_hash="hash2",
            timestamp="2024-01-02T00:00:00"
        )

        store.save(metadata1)
        store.save(metadata2)

        all_metadata = store.list_all()

        # Should be ordered newest first
        assert all_metadata[0].file_name == "test2.xlsx"
        assert all_metadata[1].file_name == "test1.xlsx"
