"""
Custom validators for data validation.
"""

import re
from typing import Any, Callable, Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime

from excel_to_sql.validators.base import BaseValidator, ValidationResult


class CustomValidator(BaseValidator):
    """
    Custom validator using a user-provided function.

    Example:
        def validate_age(age_series):
            result = ValidationResult()
            for idx, age in enumerate(age_series):
                if age < 0 or age > 120:
                    result.add_error("age", idx, "Age must be between 0 and 120", age)
            return result

        validator = CustomValidator("age", validate_age)
        result = validator.validate(df)
    """

    def __init__(self, column: str, func: Callable[[pd.Series], ValidationResult]) -> None:
        """
        Initialize custom validator.

        Args:
            column: Column name to validate
            func: Validation function that takes a Series and returns ValidationResult
        """
        super().__init__(column)
        self.func = func

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate using custom function.

        Args:
            df: DataFrame to validate

        Returns:
            ValidationResult from custom function
        """
        if self.column not in df.columns:
            result = ValidationResult(is_valid=False)
            result.add_error(self.column, -1, f"Column '{self.column}' not found")
            return result

        return self.func(df[self.column])


class RangeValidator(BaseValidator):
    """
    Validates that numeric values are within a specified range.

    Example:
        validator = RangeValidator("age", min_value=0, max_value=120)
        result = validator.validate(df)
    """

    def __init__(
        self,
        column: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        inclusive: bool = True,
    ) -> None:
        """
        Initialize range validator.

        Args:
            column: Column name to validate
            min_value: Minimum allowed value (None for no minimum)
            max_value: Maximum allowed value (None for no maximum)
            inclusive: Whether bounds are inclusive
        """
        super().__init__(column)
        self.min_value = min_value
        self.max_value = max_value
        self.inclusive = inclusive

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """Validate numeric range."""
        result = ValidationResult()

        if self.column not in df.columns:
            result.add_error(self.column, -1, f"Column '{self.column}' not found")
            return result

        series = df[self.column]

        for idx, value in enumerate(series):
            if pd.isna(value):
                continue

            is_valid = True

            if self.min_value is not None:
                if self.inclusive:
                    is_valid = is_valid and (value >= self.min_value)
                else:
                    is_valid = is_valid and (value > self.min_value)

            if self.max_value is not None:
                if self.inclusive:
                    is_valid = is_valid and (value <= self.max_value)
                else:
                    is_valid = is_valid and (value < self.max_value)

            if not is_valid:
                result.add_error(
                    self.column,
                    idx,
                    f"Value {value} is outside valid range [{self.min_value}, {self.max_value}]",
                    value,
                )

        return result


class RegexValidator(BaseValidator):
    """
    Validates that string values match a regex pattern.

    Example:
        validator = RegexValidator("email", r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
        result = validator.validate(df)
    """

    def __init__(self, column: str, pattern: str, flags: int = 0) -> None:
        """
        Initialize regex validator.

        Args:
            column: Column name to validate
            pattern: Regular expression pattern
            flags: Regex flags (e.g., re.IGNORECASE)
        """
        super().__init__(column)
        self.pattern = pattern
        self.regex = re.compile(pattern, flags)

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """Validate regex pattern."""
        result = ValidationResult()

        if self.column not in df.columns:
            result.add_error(self.column, -1, f"Column '{self.column}' not found")
            return result

        series = df[self.column]

        for idx, value in enumerate(series):
            if pd.isna(value):
                continue

            str_value = str(value)
            if not self.regex.match(str_value):
                result.add_error(
                    self.column,
                    idx,
                    f"Value '{value}' does not match pattern '{self.pattern}'",
                    value,
                )

        return result


class UniqueValidator(BaseValidator):
    """
    Validates that all values in a column are unique.

    Example:
        validator = UniqueValidator("id")
        result = validator.validate(df)
    """

    def __init__(self, column: str, ignore_nulls: bool = True) -> None:
        """
        Initialize unique validator.

        Args:
            column: Column name to validate
            ignore_nulls: Whether to ignore null values when checking uniqueness
        """
        super().__init__(column)
        self.ignore_nulls = ignore_nulls

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """Validate uniqueness."""
        result = ValidationResult()

        if self.column not in df.columns:
            result.add_error(self.column, -1, f"Column '{self.column}' not found")
            return result

        series = df[self.column]

        # Find duplicates
        if self.ignore_nulls:
            duplicates = series[series.duplicated(keep=False) & series.notna()]
        else:
            duplicates = series[series.duplicated(keep=False)]

        for idx, value in duplicates.items():
            result.add_error(
                self.column,
                idx,
                f"Duplicate value found: '{value}'",
                value,
            )

        result.is_valid = len(duplicates) == 0
        return result


class NotNullValidator(BaseValidator):
    """
    Validates that a column has no null values.

    Example:
        validator = NotNullValidator("required_field")
        result = validator.validate(df)
    """

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """Validate not null."""
        result = ValidationResult()

        if self.column not in df.columns:
            result.add_error(self.column, -1, f"Column '{self.column}' not found")
            return result

        null_rows = df[df[self.column].isna()].index.tolist()

        for idx in null_rows:
            result.add_error(self.column, idx, "Null value not allowed", None)

        result.is_valid = len(null_rows) == 0
        return result


class EnumValidator(BaseValidator):
    """
    Validates that values are from a predefined set.

    Example:
        validator = EnumValidator("status", ["active", "inactive", "pending"])
        result = validator.validate(df)
    """

    def __init__(self, column: str, allowed_values: List[Any], case_sensitive: bool = True) -> None:
        """
        Initialize enum validator.

        Args:
            column: Column name to validate
            allowed_values: List of allowed values
            case_sensitive: Whether string comparison is case-sensitive
        """
        super().__init__(column)
        self.allowed_values = allowed_values
        self.case_sensitive = case_sensitive

        if not case_sensitive:
            self.allowed_values_lower = [str(v).lower() for v in allowed_values]

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """Validate enum values."""
        result = ValidationResult()

        if self.column not in df.columns:
            result.add_error(self.column, -1, f"Column '{self.column}' not found")
            return result

        series = df[self.column]

        for idx, value in enumerate(series):
            if pd.isna(value):
                continue

            is_valid = False
            if self.case_sensitive:
                is_valid = value in self.allowed_values
            else:
                is_valid = str(value).lower() in self.allowed_values_lower

            if not is_valid:
                result.add_error(
                    self.column,
                    idx,
                    f"Value '{value}' not in allowed values: {self.allowed_values}",
                    value,
                )

        return result
