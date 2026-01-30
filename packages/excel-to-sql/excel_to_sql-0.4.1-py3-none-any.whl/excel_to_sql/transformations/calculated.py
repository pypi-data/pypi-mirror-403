"""
Calculated/derived columns support.

Allows creating new columns based on expressions or custom functions.
"""

from typing import Any, Callable, Dict, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime


class CalculatedColumn:
    """
    Defines a calculated/derived column.

    Supports:
    - Arithmetic expressions (col1 + col2)
    - Custom Python functions
    - String operations
    - Date calculations
    - Conditional logic

    Example:
        # Using expression
        calc = CalculatedColumn(
            name="total_price",
            expression="quantity * unit_price"
        )

        # Using function
        calc = CalculatedColumn(
            name="full_name",
            func=lambda row: f"{row['first_name']} {row['last_name']}"
        )
    """

    def __init__(
        self,
        name: str,
        expression: Optional[str] = None,
        func: Optional[Callable[[pd.Series], Any]] = None,
        dtype: Optional[str] = None,
    ) -> None:
        """
        Initialize calculated column.

        Args:
            name: Name of the new column
            expression: String expression (evaluated in DataFrame context)
            func: Function to apply to each row
            dtype: Expected data type (optional)

        Note:
            Either expression or func must be provided.
            Expression is evaluated using pandas eval() for performance.
        """
        if expression is None and func is None:
            raise ValueError("Either expression or func must be provided")

        self.name = name
        self.expression = expression
        self.func = func
        self.dtype = dtype

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply calculated column to DataFrame.

        Args:
            df: DataFrame to transform

        Returns:
            DataFrame with new column added

        Raises:
            ValueError: If expression references invalid columns
        """
        result = df.copy()

        try:
            if self.expression is not None:
                # Use pandas eval for expressions
                result[self.name] = result.eval(self.expression)
            else:
                # Apply custom function
                result[self.name] = result.apply(self.func, axis=1)

            # Convert dtype if specified
            if self.dtype:
                result[self.name] = result[self.name].astype(self.dtype)

        except Exception as e:
            raise ValueError(f"Failed to apply calculated column '{self.name}': {e}") from e

        return result

    def validate(self, df: pd.DataFrame) -> List[str]:
        """
        Validate that expression can be applied.

        Args:
            df: DataFrame to validate against

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        if self.expression:
            # Check if referenced columns exist
            # Simple regex to extract column names
            import re

            # Find potential column names (alphanumeric + underscore)
            tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", self.expression)

            # Filter out Python keywords
            keywords = {"and", "or", "not", "in", "is", "lambda", "def", "class"}
            columns = [t for t in tokens if t not in keywords]

            for col in columns:
                if col not in df.columns:
                    errors.append(f"Column '{col}' not found in DataFrame")

        return errors


class CalculatedColumns:
    """
    Manages multiple calculated columns.

    Example:
        columns = CalculatedColumns([
            CalculatedColumn("total", "quantity * price"),
            CalculatedColumn("tax", "total * 0.1"),
            CalculatedColumn("grand_total", "total + tax")
        ])
        result = columns.apply(df)
    """

    def __init__(self, columns: List[CalculatedColumn]) -> None:
        """
        Initialize calculated columns collection.

        Args:
            columns: List of CalculatedColumn objects
        """
        self._columns = columns

    def apply(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all calculated columns to DataFrame.

        Args:
            df: DataFrame to transform

        Returns:
            DataFrame with all calculated columns added

        Note:
            Columns are applied in order, so later columns
            can reference earlier calculated columns.
        """
        result = df.copy()

        for column in self._columns:
            result = column.apply(result)

        return result

    def validate(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        Validate all calculated columns.

        Args:
            df: DataFrame to validate against

        Returns:
            Dictionary mapping column names to validation errors
        """
        errors = {}

        for column in self._columns:
            column_errors = column.validate(df)
            if column_errors:
                errors[column.name] = column_errors

        return errors

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "CalculatedColumns":
        """
        Create CalculatedColumns from configuration dict.

        Args:
            config: Configuration with "calculated_columns" key

        Example:
            config = {
                "calculated_columns": [
                    {
                        "name": "total",
                        "expression": "quantity * price"
                    },
                    {
                        "name": "full_name",
                        "expression": "first_name + ' ' + last_name"
                    }
                ]
            }
            columns = CalculatedColumns.from_config(config)
        """
        columns_config = config.get("calculated_columns", [])

        columns = []
        for col_config in columns_config:
            column = CalculatedColumn(
                name=col_config["name"],
                expression=col_config.get("expression"),
                dtype=col_config.get("type"),
            )
            columns.append(column)

        return cls(columns)
