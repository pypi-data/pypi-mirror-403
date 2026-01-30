"""
Metadata storage and retrieval.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime

from excel_to_sql.metadata.models import ImportMetadata


class MetadataStore:
    """
    Stores and retrieves metadata for imports.

    Uses JSON file storage in the project directory.

    Example:
        store = MetadataStore(project_path)
        metadata = ImportMetadata(...)
        store.save(metadata)
        retrieved = store.get_by_hash(content_hash)
    """

    def __init__(self, project_path: Path) -> None:
        """
        Initialize metadata store.

        Args:
            project_path: Path to project directory
        """
        self._project_path = Path(project_path)
        self._metadata_dir = self._project_path / ".excel-to-sqlite" / "metadata"
        self._index_file = self._metadata_dir / "index.json"

        # Create directories if needed
        self._metadata_dir.mkdir(parents=True, exist_ok=True)

        # Initialize index if needed
        if not self._index_file.exists():
            self._index_file.write_text(json.dumps({}))

    def save(self, metadata: ImportMetadata) -> None:
        """
        Save metadata.

        Args:
            metadata: ImportMetadata to save
        """
        # Save individual metadata file
        metadata_file = self._metadata_dir / f"{metadata.content_hash}.json"
        metadata_file.write_text(json.dumps(metadata.to_dict(), indent=2))

        # Update index
        self._update_index(metadata)

    def get_by_hash(self, content_hash: str) -> Optional[ImportMetadata]:
        """
        Get metadata by content hash.

        Args:
            content_hash: SHA-256 hash of file content

        Returns:
            ImportMetadata or None if not found
        """
        metadata_file = self._metadata_dir / f"{content_hash}.json"

        if not metadata_file.exists():
            return None

        data = json.loads(metadata_file.read_text())
        return ImportMetadata.from_dict(data)

    def get_by_tag(self, tag: str) -> List[ImportMetadata]:
        """
        Get all metadata with a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of ImportMetadata with the tag
        """
        index = self._load_index()
        results = []

        for content_hash, entry in index.items():
            if tag in entry.get("tags", []):
                metadata = self.get_by_hash(content_hash)
                if metadata:
                    results.append(metadata)

        return results

    def get_by_table(self, table_name: str) -> List[ImportMetadata]:
        """
        Get all metadata for a specific table.

        Args:
            table_name: Table name to search for

        Returns:
            List of ImportMetadata for the table
        """
        index = self._load_index()
        results = []

        for content_hash, entry in index.items():
            if entry.get("table_name") == table_name:
                metadata = self.get_by_hash(content_hash)
                if metadata:
                    results.append(metadata)

        # Sort by timestamp (newest first)
        results.sort(key=lambda m: m.timestamp, reverse=True)
        return results

    def list_all(self) -> List[ImportMetadata]:
        """
        List all metadata.

        Returns:
            List of all ImportMetadata
        """
        index = self._load_index()
        results = []

        for content_hash in index.keys():
            metadata = self.get_by_hash(content_hash)
            if metadata:
                results.append(metadata)

        # Sort by timestamp (newest first)
        results.sort(key=lambda m: m.timestamp, reverse=True)
        return results

    def delete(self, content_hash: str) -> bool:
        """
        Delete metadata by hash.

        Args:
            content_hash: SHA-256 hash of file content

        Returns:
            True if deleted, False if not found
        """
        metadata_file = self._metadata_dir / f"{content_hash}.json"

        if not metadata_file.exists():
            return False

        # Delete file
        metadata_file.unlink()

        # Update index
        index = self._load_index()
        if content_hash in index:
            del index[content_hash]
            self._save_index(index)

        return True

    def search(self, query: Dict[str, Any]) -> List[ImportMetadata]:
        """
        Search metadata by criteria.

        Args:
            query: Search criteria (e.g., {"table_name": "products", "tags": ["important"]})

        Returns:
            List of matching ImportMetadata
        """
        all_metadata = self.list_all()
        results = []

        for metadata in all_metadata:
            match = True
            data = metadata.to_dict()

            for key, value in query.items():
                if key not in data:
                    match = False
                    break

                if isinstance(value, list):
                    # For lists, check if any item matches
                    if not any(item in data[key] for item in value):
                        match = False
                        break
                else:
                    if data[key] != value:
                        match = False
                        break

            if match:
                results.append(metadata)

        return results

    def _load_index(self) -> Dict[str, Any]:
        """Load metadata index."""
        if not self._index_file.exists():
            return {}

        return json.loads(self._index_file.read_text())

    def _save_index(self, index: Dict[str, Any]) -> None:
        """Save metadata index."""
        self._index_file.write_text(json.dumps(index, indent=2))

    def _update_index(self, metadata: ImportMetadata) -> None:
        """Update metadata index."""
        index = self._load_index()

        index[metadata.content_hash] = {
            "file_name": metadata.file_name,
            "file_type": metadata.file_type,
            "table_name": metadata.table_name,
            "row_count": metadata.row_count,
            "column_count": metadata.column_count,
            "tags": metadata.tags,
            "timestamp": metadata.timestamp,
        }

        self._save_index(index)
