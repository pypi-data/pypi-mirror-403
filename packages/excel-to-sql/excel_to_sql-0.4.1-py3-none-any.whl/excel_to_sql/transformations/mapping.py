"""
Value mapping for data standardization.

Allows mapping source values to standardized target values.
"""

from typing import Any, Dict, Optional
import pandas as pd
import numpy as np


class ValueMapping:
    """
    Maps source values to standardized target values.

    Useful for:
    - Standardizing state codes (NY -> New York)
    - Fixing typos (colour -> color)
    - Normalizing categories (M, Male, m -> Male)
    - Legacy data migration

    Example:
        mapping = ValueMapping({
            "state": {
                "NY": "New York",
                "CA": "California",
                "TX": "Texas"
            },
            "status": {
                "1": "Active",
                "0": "Inactive",
                "TRUE": "Active"
            }
        })
        mapping.apply(df)
    """

    def __init__(self, mappings: Dict[str, Dict[Any, Any]]) -> None:
        """
        Initialize value mapping.

        Args:
            mappings: Dictionary mapping column names to value maps
                     Format: {column_name: {source_value: target_value}}
        """
        self._mappings = mappings

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply value mappings to DataFrame.

        Args:
            df: DataFrame to transform

        Returns:
            Transformed DataFrame with mapped values

        Note:
            - Values not in mapping are left unchanged
            - Mapping is case-sensitive by default
            - None/NaN values are preserved
        """
        result = df.copy()

        for column, value_map in self._mappings.items():
            if column not in result.columns:
                continue

            # Apply mapping, preserving NaN
            result[column] = result[column].apply(
                lambda x: value_map.get(x, x) if pd.notna(x) else x
            )

        return result

    def to_dict(self) -> Dict[str, Dict[Any, Any]]:
        """Get mappings as dictionary."""
        return self._mappings.copy()

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "ValueMapping":
        """
        Create ValueMapping from configuration dict.

        Args:
            config: Configuration with "value_mappings" key

        Example:
            config = {
                "value_mappings": {
                    "state": {"NY": "New York"}
                }
            }
            mapping = ValueMapping.from_config(config)
        """
        mappings = config.get("value_mappings", {})
        return cls(mappings)

    def get_mapping_stats(self, df: pd.DataFrame) -> Dict[str, Dict[Any, int]]:
        """
        Get statistics about what would be mapped.

        Args:
            df: DataFrame to analyze

        Returns:
            Dictionary with mapping statistics per column

        Example:
            {
                "state": {"NY": 15, "CA": 20},
                "status": {"1": 50}
            }
        """
        stats = {}

        for column, value_map in self._mappings.items():
            if column not in df.columns:
                continue

            # Count occurrences of mapped values
            counts = df[df[column].isin(value_map.keys())][column].value_counts()
            stats[column] = counts.to_dict()

        return stats
