"""
Validation rules engine.

Allows defining complex validation rules with conditionals.
"""

from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

from excel_to_sql.validators.base import BaseValidator, ValidationResult
from excel_to_sql.validators.custom import (
    RangeValidator,
    RegexValidator,
    UniqueValidator,
    NotNullValidator,
    EnumValidator,
)


@dataclass
class ValidationRule:
    """
    Defines a validation rule for a column.

    Rules can be:
    - Required: Column must not be null
    - Unique: Values must be unique
    - Range: Numeric values within range
    - Regex: String matches pattern
    - Enum: Value from allowed set
    - Custom: Custom validation function
    """

    column: str
    rule_type: str  # required, unique, range, regex, enum, custom
    params: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None
    severity: str = "error"  # error, warning

    def to_validator(self) -> BaseValidator:
        """
        Convert rule to validator instance.

        Returns:
            BaseValidator instance

        Raises:
            ValueError: If rule_type is invalid
        """
        if self.rule_type == "required":
            return NotNullValidator(self.column)

        elif self.rule_type == "unique":
            return UniqueValidator(self.column)

        elif self.rule_type == "range":
            return RangeValidator(
                self.column,
                min_value=self.params.get("min"),
                max_value=self.params.get("max"),
                inclusive=self.params.get("inclusive", True),
            )

        elif self.rule_type == "regex":
            return RegexValidator(
                self.column,
                self.params.get("pattern", ""),
                flags=self.params.get("flags", 0),
            )

        elif self.rule_type == "enum":
            return EnumValidator(
                self.column,
                self.params.get("values", []),
                case_sensitive=self.params.get("case_sensitive", True),
            )

        else:
            raise ValueError(f"Unknown rule type: {self.rule_type}")


class RuleSet:
    """
    Collection of validation rules.

    Example:
        rules = RuleSet([
            ValidationRule("id", "unique"),
            ValidationRule("email", "regex", {"pattern": r"^[^@]+@[^@]+$"}),
            ValidationRule("age", "range", {"min": 0, "max": 120}),
            ValidationRule("status", "enum", {"values": ["active", "inactive"]}),
        ])
        result = rules.validate(df)
    """

    def __init__(self, rules: List[ValidationRule]) -> None:
        """
        Initialize ruleset.

        Args:
            rules: List of validation rules
        """
        self._rules = rules

    def validate(self, df: pd.DataFrame) -> ValidationResult:
        """
        Validate DataFrame against all rules.

        Args:
            df: DataFrame to validate

        Returns:
            Combined ValidationResult from all rules
        """
        final_result = ValidationResult(is_valid=True)

        for rule in self._rules:
            validator = rule.to_validator()
            result = validator.validate(df)

            # Update severity based on rule
            for error in result.errors:
                error.severity = rule.severity

            final_result.merge(result)

        return final_result

    def get_rules_for_column(self, column: str) -> List[ValidationRule]:
        """
        Get all rules for a specific column.

        Args:
            column: Column name

        Returns:
            List of rules for the column
        """
        return [r for r in self._rules if r.column == column]

    def add_rule(self, rule: ValidationRule) -> None:
        """Add a rule to the ruleset."""
        self._rules.append(rule)

    def remove_rule(self, column: str, rule_type: str) -> None:
        """
        Remove a rule from the ruleset.

        Args:
            column: Column name
            rule_type: Type of rule to remove
        """
        self._rules = [r for r in self._rules if not (r.column == column and r.rule_type == rule_type)]

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "RuleSet":
        """
        Create RuleSet from configuration dict.

        Args:
            config: Configuration with "validation_rules" key

        Example:
            config = {
                "validation_rules": [
                    {
                        "column": "id",
                        "type": "unique"
                    },
                    {
                        "column": "email",
                        "type": "regex",
                        "pattern": "^[^@]+@[^@]+$"
                    }
                ]
            }
            rules = RuleSet.from_config(config)
        """
        rules_config = config.get("validation_rules", [])

        rules = []
        for rule_config in rules_config:
            rule = ValidationRule(
                column=rule_config["column"],
                rule_type=rule_config["type"],
                params=rule_config.get("params", {}),
                message=rule_config.get("message"),
                severity=rule_config.get("severity", "error"),
            )
            rules.append(rule)

        return cls(rules)
