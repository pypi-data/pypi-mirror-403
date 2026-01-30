"""
DataFrame wrapper entity for cleaning and transformation.

Encapsulates data cleaning, column mapping, and type conversion logic.
"""

from typing import Optional, List, Dict, Any

import pandas as pd
import numpy as np

from excel_to_sql.transformations.mapping import ValueMapping
from excel_to_sql.transformations.calculated import CalculatedColumns
from excel_to_sql.validators.base import ValidationResult
from excel_to_sql.validators.rules import RuleSet
from excel_to_sql.validators.reference import ReferenceValidator


class DataFrame:
    """
    Wrapper around pandas.DataFrame with cleaning and transformation.

    Usage:
        df = DataFrame(raw_df)
        df.clean()
        df.apply_mapping(mapping)
        result = df.to_pandas()
    """

    def __init__(self, data: Optional[pd.DataFrame] = None) -> None:
        """
        Initialize DataFrame wrapper.

        Args:
            data: Existing DataFrame or None for empty DataFrame
        """
        if data is None:
            self._df = pd.DataFrame()
        else:
            self._df = data.copy()

    # ──────────────────────────────────────────────────────────────
    # PROPERTIES
    # ──────────────────────────────────────────────────────────────

    @property
    def columns(self) -> list[str]:
        """Column names."""
        return self._df.columns.tolist()

    @property
    def shape(self) -> tuple[int, int]:
        """(rows, columns) dimensions."""
        return self._df.shape

    @property
    def is_empty(self) -> bool:
        """True if no rows."""
        return len(self._df) == 0

    # ──────────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ──────────────────────────────────────────────────────────────

    def clean(self, strip_columns: bool = True) -> None:
        """
        Clean data in place.

        Transformations:
        1. Strip whitespace from string columns
        2. Normalize empty strings to NaN
        3. Drop completely empty rows
        4. Convert column names to lowercase

        Args:
            strip_columns: If True, strip column names too

        Example:
            Before: ["  Name  ", "Date", ""]
            After:  ["name", "date", NaN]
        """
        df = self._df

        # 1. Strip whitespace from string columns
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].astype(str).str.strip()

        # 2. Normalize empty strings to NaN
        df.replace(r"^\s*$", np.nan, regex=True, inplace=True)

        # 3. Drop completely empty rows
        df.dropna(how="all", inplace=True)

        # 4. Lowercase and strip column names
        if strip_columns:
            df.columns = df.columns.str.lower().str.strip()

    def apply_mapping(self, mapping: dict) -> None:
        """
        Apply column mapping and type conversion.

        Args:
            mapping: Dictionary from mappings.json

        Mapping structure:
            {
                "target_table": "products",
                "primary_key": ["id"],
                "column_mappings": {
                    "ID": {"target": "id", "type": "integer"},
                    "Name": {"target": "name", "type": "string"},
                    "Price": {"target": "price", "type": "float"}
                }
            }

        What it does:
        1. Rename columns: ID -> id, Name -> name (case-insensitive)
        2. Drop unmapped columns
        3. Convert types according to mapping

        Example:
            Before: {"ID": [1, 2], "Name": ["A", "B"], "Ignore": ["X", "Y"]}
            After:  {"id": [1, 2], "name": ["A", "B"]}
        """
        column_mappings = mapping["column_mappings"]

        # Build rename dict with both exact and lowercase matching
        # This handles both cases: when clean() was called (lowercase columns)
        # and when it wasn't (original case columns)
        rename_dict = {}
        type_conversions = {}

        for source_col, config in column_mappings.items():
            target_col = config["target"]
            col_type = config.get("type", "string")

            # Try exact match first, then lowercase
            rename_dict[source_col] = target_col
            rename_dict[source_col.lower()] = target_col
            type_conversions[target_col] = col_type

        # Rename columns using case-insensitive matching
        self._df = self._df.rename(columns=rename_dict)

        # Keep only mapped columns
        mapped_columns = list(rename_dict.values())
        # Remove duplicates from mapped_columns
        seen = set()
        unique_mapped_columns = []
        for col in mapped_columns:
            if col not in seen:
                seen.add(col)
                unique_mapped_columns.append(col)

        self._df = self._df[unique_mapped_columns]

        # Convert types
        for col, col_type in type_conversions.items():
            if col_type == "integer":
                self._df[col] = pd.to_numeric(self._df[col], errors="coerce").astype(
                    "Int64"
                )
            elif col_type == "float":
                self._df[col] = pd.to_numeric(self._df[col], errors="coerce")
            elif col_type == "boolean":
                self._df[col] = self._df[col].map(
                    {
                        "TRUE": True,
                        "FALSE": False,
                        "True": True,
                        "False": False,
                        "1": True,
                        "0": False,
                        True: True,
                        False: False,
                        1: True,
                        0: False,
                    }
                )
            elif col_type == "date":
                self._df[col] = pd.to_datetime(self._df[col], errors="coerce")
            # string is default (do nothing)

    def filter_nulls(self, columns: list[str]) -> None:
        """
        Remove rows where any of these columns are null.

        Args:
            columns: Columns to check for null values

        Example:
            df.filter_nulls(["id", "name"])
            # Removes rows where id OR name is null
        """
        self._df.dropna(subset=columns, inplace=True)

    def apply_value_mapping(self, value_mapping: ValueMapping) -> None:
        """
        Apply value mapping to standardize data.

        Args:
            value_mapping: ValueMapping instance

        Example:
            mapping = ValueMapping({"status": {"1": "Active", "0": "Inactive"}})
            df.apply_value_mapping(mapping)
        """
        self._df = value_mapping.apply(self._df)

    def apply_calculated_columns(self, calculated_columns: CalculatedColumns) -> None:
        """
        Apply calculated columns to DataFrame.

        Args:
            calculated_columns: CalculatedColumns instance

        Example:
            columns = CalculatedColumns([
                CalculatedColumn("total", "quantity * price")
            ])
            df.apply_calculated_columns(columns)
        """
        self._df = calculated_columns.apply(self._df)

    def validate(self, ruleset: RuleSet) -> ValidationResult:
        """
        Validate DataFrame against ruleset.

        Args:
            ruleset: RuleSet with validation rules

        Returns:
            ValidationResult with errors and warnings

        Example:
            rules = RuleSet([
                ValidationRule("id", "unique"),
                ValidationRule("email", "regex", {"pattern": r"^[^@]+@[^@]+$"})
            ])
            result = df.validate(rules)
        """
        return ruleset.validate(self._df)

    def validate_references(
        self, reference_validators: List[ReferenceValidator]
    ) -> ValidationResult:
        """
        Validate DataFrame against reference tables.

        Args:
            reference_validators: List of ReferenceValidator instances

        Returns:
            Combined ValidationResult from all validators

        Example:
            validators = [
                ReferenceValidator("category_id", db, "categories"),
                ReferenceValidator("user_id", db, "users")
            ]
            result = df.validate_references(validators)
        """
        final_result = ValidationResult(is_valid=True)

        for validator in reference_validators:
            result = validator.validate(self._df)
            final_result.merge(result)

        return final_result

    def apply_transformations(self, mapping: Dict[str, Any]) -> None:
        """
        Apply all transformations from mapping configuration.

        This is a convenience method that applies:
        1. Value mappings
        2. Calculated columns

        Args:
            mapping: Full mapping configuration dict
        """
        # Apply value mappings
        if "value_mappings" in mapping and mapping["value_mappings"]:
            mappings_dict = {}
            for vm_config in mapping["value_mappings"]:
                mappings_dict[vm_config.column] = vm_config.mappings

            value_mapping = ValueMapping(mappings_dict)
            self.apply_value_mapping(value_mapping)

        # Apply calculated columns
        if "calculated_columns" in mapping and mapping["calculated_columns"]:
            calc_columns = CalculatedColumns.from_config(mapping)
            self.apply_calculated_columns(calc_columns)

    def to_pandas(self) -> pd.DataFrame:
        """Get underlying pandas DataFrame."""
        return self._df.copy()

    def to_dict(self, orient: str = "records") -> list[dict]:
        """Convert to list of dictionaries."""
        return self._df.to_dict(orient=orient)
