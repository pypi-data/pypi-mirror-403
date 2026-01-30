"""
Metadata models.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ImportMetadata:
    """
    Metadata for an import operation.
    """

    file_name: str
    file_type: str
    table_name: str
    row_count: int
    column_count: int
    content_hash: str
    tags: List[str] = field(default_factory=list)
    custom_metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_name": self.file_name,
            "file_type": self.file_type,
            "table_name": self.table_name,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "content_hash": self.content_hash,
            "tags": self.tags,
            "custom_metadata": self.custom_metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ImportMetadata":
        """Create from dictionary."""
        return cls(
            file_name=data["file_name"],
            file_type=data["file_type"],
            table_name=data["table_name"],
            row_count=data["row_count"],
            column_count=data["column_count"],
            content_hash=data["content_hash"],
            tags=data.get("tags", []),
            custom_metadata=data.get("custom_metadata", {}),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
        )
