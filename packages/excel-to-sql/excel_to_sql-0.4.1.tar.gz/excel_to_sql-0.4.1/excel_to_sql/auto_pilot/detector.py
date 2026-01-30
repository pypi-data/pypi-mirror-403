"""
Pattern Detection Module for Auto-Pilot Mode.

This module provides automatic detection of common WMS (Warehouse Management System)
patterns in Excel files, including primary keys, value mappings, foreign keys,
and split status fields.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


class PatternDetector:
    """
    Automatically detects patterns in Excel files for WMS data imports.

    This class analyzes pandas DataFrames and identifies common patterns found in
    Warehouse Management System exports, including:
    - Primary keys (columns with unique, non-null values)
    - Value mappings (French codes that need translation)
    - Foreign keys (relationships between tables)
    - Split fields (mutually exclusive status fields)

    Example:
        >>> detector = PatternDetector()
        >>> patterns = detector.detect_patterns(df, table_name="produits")
        >>> print(patterns["primary_key"])
        'no_produit'
    """

    # French WMS code dictionaries for common patterns
    FRENCH_STATUS_CODES = {
        "ACTIF": "active",
        "INACTIF": "inactive",
        "EN_ATTENTE": "pending",
    }

    FRENCH_MOVEMENT_CODES = {
        "ENTRÉE": "inbound",
        "SORTIE": "outbound",
        "TRANSFERT": "transfer",
        "AJUSTEMENT": "adjustment",
        "INVENTAIRE": "inventory",
    }

    # Column naming patterns for different field types
    PK_PATTERNS = [
        r"^id$",
        r"^code$",
        r"^no_\w+$",
        r"\w+_id$",
        r"\w+_no$",
        r"\w+_code$",
        r"^\w+_numero$",
        r"^oid$",
    ]

    FK_PATTERNS = [
        r"\w+_id$",
        r"\w+_no$",
        r"\w+_code$",
        r"^\w+_numero$",
        r"^no_\w+$",
    ]

    def __init__(self) -> None:
        """Initialize the PatternDetector."""
        self._confidence: float = 0.0

    @staticmethod
    def _pluralize(word: str) -> str:
        """
        Simple pluralization for common English words.

        Args:
            word: Singular word to pluralize

        Returns:
            Plural form of the word

        Example:
            >>> PatternDetector._pluralize("category")
            'categories'
            >>> PatternDetector._pluralize("product")
            'products'
        """
        # Common irregular plurals
        irregular = {
            "category": "categories",
            "person": "people",
            "child": "children",
            "man": "men",
            "woman": "women",
            "tooth": "teeth",
            "foot": "feet",
            "mouse": "mice",
            "goose": "geese",
        }

        if word in irregular:
            return irregular[word]

        # Words ending in 'y' -> 'ies'
        if word.endswith("y"):
            return word[:-1] + "ies"

        # Words ending in 's', 'x', 'z', 'ch', 'sh' -> 'es'
        if word.endswith(("s", "x", "z", "ch", "sh")):
            return word + "es"

        # Default: add 's'
        return word + "s"

    def detect_patterns(
        self, df: pd.DataFrame, table_name: str
    ) -> dict[str, Any]:
        """
        Run all detection algorithms on a DataFrame.

        Args:
            df: Input DataFrame to analyze
            table_name: Name of the table (for reference in output)

        Returns:
            Dictionary containing all detected patterns:
            {
                "primary_key": str | None,
                "value_mappings": dict[str, dict[str, str]],
                "foreign_keys": list[dict[str, Any]],
                "split_fields": list[str] | None,
                "confidence": float,
                "issues": list[str],
            }

        Example:
            >>> detector = PatternDetector()
            >>> df = pd.DataFrame({"no_produit": [1, 2, 3], "nom": ["A", "B", "C"]})
            >>> patterns = detector.detect_patterns(df, "products")
        """
        results: dict[str, Any] = {
            "table_name": table_name,
            "primary_key": None,
            "value_mappings": {},
            "foreign_keys": [],
            "split_fields": None,
            "confidence": 0.0,
            "issues": [],
        }

        # Primary key detection
        pk = self._detect_primary_key(df)
        if pk:
            results["primary_key"] = pk
            results["confidence"] += 0.25
        else:
            results["issues"].append("No clear primary key detected")

        # Value mapping detection
        value_mappings = self._detect_value_mappings(df)
        if value_mappings:
            results["value_mappings"] = value_mappings
            results["confidence"] += 0.20 * len(value_mappings) / 3

        # Foreign key detection
        foreign_keys = self._detect_foreign_keys(df, table_name)
        if foreign_keys:
            results["foreign_keys"] = foreign_keys
            results["confidence"] += 0.20 * len(foreign_keys) / 2

        # Split field detection
        split_fields = self._detect_split_fields(df)
        if split_fields:
            results["split_fields"] = split_fields
            results["confidence"] += 0.20

        # Base confidence for successful analysis
        results["confidence"] = min(1.0, results["confidence"] + 0.15)

        return results

    def _detect_primary_key(self, df: pd.DataFrame) -> str | None:
        """
        Detect the primary key column in a DataFrame.

        A primary key candidate must:
        1. Match naming patterns (id, no_*, *_id, etc.)
        2. Have all unique values
        3. Have no null values

        Args:
            df: Input DataFrame

        Returns:
            Name of the detected primary key column, or None if not found

        Example:
            >>> df = pd.DataFrame({"no_produit": [1, 2, 3], "nom": ["A", "B", "C"]})
            >>> detector = PatternDetector()
            >>> pk = detector._detect_primary_key(df)
            >>> print(pk)
            'no_produit'
        """
        import re

        candidates: list[str] = []

        # Find columns matching PK patterns
        for col in df.columns:
            col_str = str(col)
            col_lower = col_str.lower().strip()
            for pattern in self.PK_PATTERNS:
                if re.match(pattern, col_lower, re.IGNORECASE):
                    candidates.append(col)
                    break

        # If no pattern matches, check all columns
        if not candidates:
            candidates = list(df.columns)

        # Validate each candidate
        for col in candidates:
            # Check for null values
            if df[col].isna().any():
                continue

            # Check for uniqueness
            if df[col].nunique() == len(df):
                return col

        # No valid primary key found
        return None

    def _detect_value_mappings(self, df: pd.DataFrame) -> dict[str, dict[str, str]]:
        """
        Detect columns containing French WMS codes that need mapping.

        Checks if column values overlap with known French code dictionaries
        for status and movement types.

        Args:
            df: Input DataFrame

        Returns:
            Dictionary mapping column names to their value mapping dictionaries

        Example:
            >>> df = pd.DataFrame({"etat": ["ACTIF", "INACTIF", "ACTIF"]})
            >>> detector = PatternDetector()
            >>> mappings = detector._detect_value_mappings(df)
            >>> print(mappings)
            {'etat': {'ACTIF': 'active', 'INACTIF': 'inactive'}}
        """
        mappings: dict[str, dict[str, str]] = {}

        # Check all string/object columns
        for col in df.select_dtypes(include=["object", "string"]).columns:
            unique_values = set(df[col].dropna().unique())

            # Check against status codes
            if unique_values & self.FRENCH_STATUS_CODES.keys():
                detected_mapping = {
                    k: v
                    for k, v in self.FRENCH_STATUS_CODES.items()
                    if k in unique_values
                }
                if detected_mapping:
                    mappings[col] = detected_mapping

            # Check against movement codes
            if unique_values & self.FRENCH_MOVEMENT_CODES.keys():
                detected_mapping = {
                    k: v
                    for k, v in self.FRENCH_MOVEMENT_CODES.items()
                    if k in unique_values
                }
                if detected_mapping:
                    mappings[col] = detected_mapping

        return mappings

    def _detect_foreign_keys(
        self, df: pd.DataFrame, table_name: str
    ) -> list[dict[str, Any]]:
        """
        Detect foreign key relationships in a DataFrame.

        Identifies columns with FK naming patterns and attempts to determine
        the referenced table name from the column name.

        Args:
            df: Input DataFrame
            table_name: Name of the current table

        Returns:
            List of detected foreign key relationships with metadata

        Example:
            >>> df = pd.DataFrame({"no_produit": [1, 2, 3]})
            >>> detector = PatternDetector()
            >>> fks = detector._detect_foreign_keys(df, "mouvements")
            >>> print(fks)
            [{'column': 'no_produit', 'ref_table': 'produits', ...}]
        """
        import re

        foreign_keys: list[dict[str, Any]] = []

        for col in df.columns:
            col_str = str(col)
            col_lower = col_str.lower().strip()

            # Check if column matches FK patterns
            is_fk = any(re.match(pattern, col_lower, re.IGNORECASE) for pattern in self.FK_PATTERNS)

            if not is_fk:
                continue

            # Extract referenced table name from column name
            ref_table = None

            # Pattern: no_<table> or <table>_id
            if col_lower.startswith("no_"):
                ref_table = self._pluralize(col_lower[3:])
            elif col_lower.endswith("_id"):
                ref_table = self._pluralize(col_lower[:-3])
            elif col_lower.endswith("_no"):
                ref_table = self._pluralize(col_lower[:-3])
            elif col_lower.endswith("_code"):
                ref_table = self._pluralize(col_lower[:-5])

            # Skip if FK references itself
            if ref_table and ref_table == table_name.lower():
                continue

            # Calculate coverage (percentage of non-null values)
            coverage = (df[col].notna().sum() / len(df)) * 100 if len(df) > 0 else 0

            if ref_table and coverage >= 50:
                foreign_keys.append(
                    {
                        "column": col,
                        "ref_table": ref_table,
                        "ref_column": col,  # Assume same column name in ref table
                        "coverage": round(coverage, 2),
                    }
                )

        return foreign_keys

    def _detect_split_fields(self, df: pd.DataFrame) -> list[str] | None:
        """
        Detect mutually exclusive status/state fields that should be combined.

        Identifies columns with status/state patterns in their names and checks
        if they are mutually exclusive (only one has a value per row).

        Args:
            df: Input DataFrame

        Returns:
            List of column names that are part of a split field group, or None

        Example:
            >>> df = pd.DataFrame({
            ...     "etat_superieur": ["A", None, "B"],
            ...     "etat_inferieur": [None, "C", None],
            ...     "etat": [None, None, None]
            ... })
            >>> detector = PatternDetector()
            >>> split = detector._detect_split_fields(df)
            >>> print(split)
            ['etat_superieur', 'etat_inferieur', 'etat']
        """
        import re

        # Find columns with status/state patterns
        status_pattern = re.compile(r"(etat|status|state)", re.IGNORECASE)
        status_cols = [col for col in df.columns if status_pattern.search(str(col))]

        if len(status_cols) < 2:
            return None

        # Check if fields are mutually exclusive
        # For each row, only one status column should have a value
        is_mutually_exclusive = True

        for _, row in df[status_cols].iterrows():
            # Count non-null values in status columns for this row
            non_null_count = row.notna().sum()

            # If more than one status column has a value, not mutually exclusive
            if non_null_count > 1:
                is_mutually_exclusive = False
                break

        if is_mutually_exclusive:
            return status_cols

        return None
