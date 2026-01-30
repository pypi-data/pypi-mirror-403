"""
Reference/lookup validation.

Validates that values in one column exist in a reference table/query.
"""

from typing import Any, Dict, List, Optional, Union
import pandas as pd
import numpy as np

from excel_to_sql.validators.base import BaseValidator, ValidationResult
from excel_to_sql.entities.database import Database


class ReferenceValidator(BaseValidator):
    """
    Validates that values exist in a reference table.

    Useful for:
    - Foreign key validation
    - Lookup tables (states, countries, categories)
    - Referential integrity checks

    Example:
        validator = ReferenceValidator(
            column="category_id",
            database=db,
            reference_table="categories",
            reference_column="id"
        )
        result = validator.validate(df)
    """

    def __init__(
        self,
        column: str,
        database: Database,
        reference_table: str,
        reference_column: str = "id",
        cache_results: bool = True,
    ) -> None:
        """
        Initialize reference validator.

        Args:
            column: Column to validate
            database: Database entity for queries
            reference_table: Table to reference
            reference_column: Column in reference table (default: "id")
            cache_results: Whether to cache reference values
        """
        super().__init__(column)
        self.database = database
        self.reference_table = reference_table
        self.reference_column = reference_column
        self.cache_results = cache_results
        self._cached_values: Optional[set] = None

    def _get_reference_values(self) -> set:
        """
        Get allowed values from reference table.

        Returns:
            Set of allowed values
        """
        if self.cache_results and self._cached_values is not None:
            return self._cached_values

        query = f"SELECT DISTINCT {self.reference_column} FROM {self.reference_table}"
        result_df = self.database.query(query)

        if result_df is None or result_df.empty:
            allowed_values = set()
        else:
            allowed_values = set(result_df[self.reference_column].dropna().tolist())

        if self.cache_results:
            self._cached_values = allowed_values

        return allowed_values

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate against reference table.

        Args:
            df: DataFrame to validate

        Returns:
            ValidationResult with missing references
        """
        result = ValidationResult()

        if self.column not in df.columns:
            result.add_error(self.column, -1, f"Column '{self.column}' not found")
            return result

        # Get reference values
        try:
            allowed_values = self._get_reference_values()
        except Exception as e:
            result.add_error(self.column, -1, f"Failed to query reference table: {e}")
            return result

        # Check each value
        series = df[self.column]

        for idx, value in enumerate(series):
            if pd.isna(value):
                continue

            if value not in allowed_values:
                result.add_error(
                    self.column,
                    idx,
                    f"Value '{value}' not found in {self.reference_table}.{self.reference_column}",
                    value,
                )

        result.is_valid = result.error_count == 0
        return result

    def clear_cache(self) -> None:
        """Clear cached reference values."""
        self._cached_values = None


class MultiColumnReferenceValidator(BaseValidator):
    """
    Validates that combinations of columns exist in a reference table.

    Useful for composite foreign keys.

    Example:
        validator = MultiColumnReferenceValidator(
            columns=["country", "state"],
            database=db,
            reference_table="locations",
            reference_columns=["country", "state"]
        )
        result = validator.validate(df)
    """

    def __init__(
        self,
        columns: List[str],
        database: Database,
        reference_table: str,
        reference_columns: List[str],
        cache_results: bool = True,
    ) -> None:
        """
        Initialize multi-column reference validator.

        Args:
            columns: Columns to validate (must match length of reference_columns)
            database: Database entity for queries
            reference_table: Table to reference
            reference_columns: Columns in reference table
            cache_results: Whether to cache reference values
        """
        # Use first column for BaseValidator
        super().__init__(columns[0])

        if len(columns) != len(reference_columns):
            raise ValueError("columns and reference_columns must have the same length")

        self.columns = columns
        self.database = database
        self.reference_table = reference_table
        self.reference_columns = reference_columns
        self.cache_results = cache_results
        self._cached_combos: Optional[set] = None

    def _get_reference_combinations(self) -> set:
        """Get allowed value combinations from reference table."""
        if self.cache_results and self._cached_combos is not None:
            return self._cached_combos

        cols = ", ".join(self.reference_columns)
        query = f"SELECT DISTINCT {cols} FROM {self.reference_table}"
        result_df = self.database.query(query)

        if result_df is None or result_df.empty:
            allowed_combos = set()
        else:
            # Create tuples from rows
            allowed_combos = set(
                tuple(row) for row in result_df[self.reference_columns].dropna().to_records(index=False)
            )

        if self.cache_results:
            self._cached_combos = allowed_combos

        return allowed_combos

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """Validate multi-column references."""
        result = ValidationResult()

        # Check all columns exist
        missing = [col for col in self.columns if col not in df.columns]
        if missing:
            for col in missing:
                result.add_error(col, -1, f"Column '{col}' not found")
            return result

        # Get reference combinations
        try:
            allowed_combos = self._get_reference_combinations()
        except Exception as e:
            result.add_error(self.columns[0], -1, f"Failed to query reference table: {e}")
            return result

        # Check each row
        for idx, row in df[self.columns].iterrows():
            if row.isna().any():
                continue

            combo = tuple(row)
            if combo not in allowed_combos:
                result.add_error(
                    self.columns[0],
                    idx,
                    f"Combination {dict(zip(self.columns, combo))} not found in {self.reference_table}",
                    combo,
                )

        result.is_valid = result.error_count == 0
        return result

    def clear_cache(self) -> None:
        """Clear cached reference combinations."""
        self._cached_combos = None
