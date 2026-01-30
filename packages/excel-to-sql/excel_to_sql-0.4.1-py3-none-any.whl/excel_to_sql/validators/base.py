"""
Base validator classes.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import pandas as pd


@dataclass
class ValidationError:
    """
    Represents a single validation error.
    """

    column: str
    row: int
    message: str
    value: Any = None
    severity: str = "error"  # error, warning, info


@dataclass
class ValidationResult:
    """
    Result of a validation operation.
    """

    is_valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        """Number of errors."""
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        """Number of warnings."""
        return len(self.warnings)

    @property
    def total_issues(self) -> int:
        """Total number of issues."""
        return self.error_count + self.warning_count

    def add_error(self, column: str, row: int, message: str, value: Any = None) -> None:
        """Add an error."""
        self.errors.append(ValidationError(column, row, message, value, "error"))
        self.is_valid = False

    def add_warning(self, column: str, row: int, message: str, value: Any = None) -> None:
        """Add a warning."""
        self.warnings.append(ValidationError(column, row, message, value, "warning"))

    def merge(self, other: "ValidationResult") -> "ValidationResult":
        """
        Merge another result into this one.

        Args:
            other: Another ValidationResult

        Returns:
            Merged result
        """
        self.is_valid = self.is_valid and other.is_valid
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "errors": [
                {
                    "column": e.column,
                    "row": e.row,
                    "message": e.message,
                    "value": str(e.value) if e.value is not None else None,
                }
                for e in self.errors
            ],
            "warnings": [
                {
                    "column": w.column,
                    "row": w.row,
                    "message": w.message,
                    "value": str(w.value) if w.value is not None else None,
                }
                for w in self.warnings
            ],
        }


class BaseValidator(ABC):
    """
    Abstract base class for validators.

    All validators must inherit from this class and implement validate().
    """

    def __init__(self, column: str) -> None:
        """
        Initialize validator.

        Args:
            column: Column name to validate
        """
        self.column = column

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate DataFrame column.

        Args:
            df: DataFrame to validate

        Returns:
            ValidationResult with errors/warnings
        """
        pass

    def _create_result(self, is_valid: bool = True) -> ValidationResult:
        """Create a ValidationResult."""
        return ValidationResult(is_valid=is_valid)
