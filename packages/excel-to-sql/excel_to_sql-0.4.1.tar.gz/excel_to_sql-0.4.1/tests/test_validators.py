"""
Tests for validators.
"""

import pytest
import pandas as pd
import numpy as np
from excel_to_sql.validators.base import ValidationResult
from excel_to_sql.validators.custom import (
    RangeValidator,
    RegexValidator,
    UniqueValidator,
    NotNullValidator,
    EnumValidator,
)
from excel_to_sql.validators.rules import ValidationRule, RuleSet


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_create_valid_result(self):
        """Test creating a valid result."""
        result = ValidationResult(is_valid=True)

        assert result.is_valid
        assert result.error_count == 0
        assert result.warning_count == 0
        assert result.total_issues == 0

    def test_add_errors(self):
        """Test adding errors."""
        result = ValidationResult()
        result.add_error("col1", 0, "Error 1")
        result.add_error("col1", 1, "Error 2")

        assert not result.is_valid
        assert result.error_count == 2
        assert len(result.errors) == 2

    def test_add_warnings(self):
        """Test adding warnings."""
        result = ValidationResult()
        result.add_warning("col1", 0, "Warning 1")

        assert result.is_valid  # Warnings don't affect validity
        assert result.warning_count == 1

    def test_merge(self):
        """Test merging results."""
        result1 = ValidationResult()
        result1.add_error("col1", 0, "Error 1")

        result2 = ValidationResult()
        result2.add_error("col2", 0, "Error 2")

        result1.merge(result2)

        assert result1.error_count == 2
        assert not result1.is_valid

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = ValidationResult()
        result.add_error("col1", 0, "Error 1", "bad_value")
        result.add_warning("col2", 1, "Warning 1")

        d = result.to_dict()

        assert d["is_valid"] is False
        assert d["error_count"] == 1
        assert d["warning_count"] == 1
        assert len(d["errors"]) == 1
        assert len(d["warnings"]) == 1


class TestRangeValidator:
    """Tests for RangeValidator."""

    def test_valid_range(self):
        """Test values within valid range."""
        df = pd.DataFrame({"age": [25, 30, 45, 60]})
        validator = RangeValidator("age", min_value=0, max_value=120)

        result = validator.validate(df)

        assert result.is_valid

    def test_below_minimum(self):
        """Test value below minimum."""
        df = pd.DataFrame({"age": [25, -5, 45]})
        validator = RangeValidator("age", min_value=0, max_value=120)

        result = validator.validate(df)

        assert not result.is_valid
        assert result.error_count == 1
        assert result.errors[0].row == 1

    def test_above_maximum(self):
        """Test value above maximum."""
        df = pd.DataFrame({"age": [25, 150, 45]})
        validator = RangeValidator("age", min_value=0, max_value=120)

        result = validator.validate(df)

        assert not result.is_valid
        assert result.error_count == 1

    def test_null_ignored(self):
        """Test that null values are ignored."""
        df = pd.DataFrame({"age": [25, None, 45]})
        validator = RangeValidator("age", min_value=0, max_value=120)

        result = validator.validate(df)

        assert result.is_valid

    def test_exclusive_bounds(self):
        """Test exclusive bounds."""
        df = pd.DataFrame({"value": [0, 5, 10]})
        validator = RangeValidator("value", min_value=0, max_value=10, inclusive=False)

        result = validator.validate(df)

        # 0 and 10 should fail with exclusive bounds
        assert not result.is_valid
        assert result.error_count == 2


class TestRegexValidator:
    """Tests for RegexValidator."""

    def test_valid_pattern(self):
        """Test valid email pattern."""
        df = pd.DataFrame({"email": ["user@example.com", "test@test.org"]})
        validator = RegexValidator("email", r"^[^@]+@[^@]+\.[^@]+$")

        result = validator.validate(df)

        assert result.is_valid

    def test_invalid_pattern(self):
        """Test invalid email pattern."""
        df = pd.DataFrame({"email": ["user@example.com", "invalid", "test@test.org"]})
        validator = RegexValidator("email", r"^[^@]+@[^@]+\.[^@]+$")

        result = validator.validate(df)

        assert not result.is_valid
        assert result.error_count == 1
        assert result.errors[0].row == 1

    def test_null_ignored(self):
        """Test that null values are ignored."""
        df = pd.DataFrame({"email": ["user@example.com", None]})
        validator = RegexValidator("email", r"^[^@]+@[^@]+\.[^@]+$")

        result = validator.validate(df)

        assert result.is_valid


class TestUniqueValidator:
    """Tests for UniqueValidator."""

    def test_unique_values(self):
        """Test unique values."""
        df = pd.DataFrame({"id": [1, 2, 3, 4]})
        validator = UniqueValidator("id")

        result = validator.validate(df)

        assert result.is_valid

    def test_duplicate_values(self):
        """Test duplicate values."""
        df = pd.DataFrame({"id": [1, 2, 2, 3]})
        validator = UniqueValidator("id")

        result = validator.validate(df)

        assert not result.is_valid
        # All duplicates should be flagged
        assert result.error_count >= 2

    def test_nulls_ignored(self):
        """Test that nulls are ignored by default."""
        df = pd.DataFrame({"id": [1, None, 2, None]})
        validator = UniqueValidator("id", ignore_nulls=True)

        result = validator.validate(df)

        assert result.is_valid

    def test_nulls_not_ignored(self):
        """Test that nulls are not ignored when configured."""
        df = pd.DataFrame({"id": [1, None, 2, None]})
        validator = UniqueValidator("id", ignore_nulls=False)

        result = validator.validate(df)

        assert not result.is_valid


class TestNotNullValidator:
    """Tests for NotNullValidator."""

    def test_no_nulls(self):
        """Test column with no nulls."""
        df = pd.DataFrame({"name": ["Alice", "Bob", "Charlie"]})
        validator = NotNullValidator("name")

        result = validator.validate(df)

        assert result.is_valid

    def test_with_nulls(self):
        """Test column with nulls."""
        df = pd.DataFrame({"name": ["Alice", None, "Charlie"]})
        validator = NotNullValidator("name")

        result = validator.validate(df)

        assert not result.is_valid
        assert result.error_count == 1
        assert result.errors[0].row == 1


class TestEnumValidator:
    """Tests for EnumValidator."""

    def test_valid_values(self):
        """Test values in allowed set."""
        df = pd.DataFrame({"status": ["active", "inactive", "pending"]})
        validator = EnumValidator("status", ["active", "inactive", "pending"])

        result = validator.validate(df)

        assert result.is_valid

    def test_invalid_values(self):
        """Test values not in allowed set."""
        df = pd.DataFrame({"status": ["active", "unknown", "pending"]})
        validator = EnumValidator("status", ["active", "inactive", "pending"])

        result = validator.validate(df)

        assert not result.is_valid
        assert result.error_count == 1

    def test_case_insensitive(self):
        """Test case-insensitive validation."""
        df = pd.DataFrame({"status": ["Active", "INACTIVE", "Pending"]})
        validator = EnumValidator("status", ["active", "inactive", "pending"], case_sensitive=False)

        result = validator.validate(df)

        assert result.is_valid

    def test_case_sensitive(self):
        """Test case-sensitive validation."""
        df = pd.DataFrame({"status": ["Active", "inactive"]})
        validator = EnumValidator("status", ["active", "inactive"], case_sensitive=True)

        result = validator.validate(df)

        assert not result.is_valid
        assert result.error_count == 1


class TestRuleSet:
    """Tests for RuleSet."""

    def test_single_rule(self):
        """Test ruleset with single rule."""
        df = pd.DataFrame({"id": [1, 2, 3]})
        rules = RuleSet([
            ValidationRule("id", "unique")
        ])

        result = rules.validate(df)

        assert result.is_valid

    def test_multiple_rules(self):
        """Test ruleset with multiple rules."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "age": [25, 30, 45],
            "email": ["user@example.com", "test@test.org", "admin@test.com"]
        })
        rules = RuleSet([
            ValidationRule("id", "unique"),
            ValidationRule("age", "range", {"min": 0, "max": 120}),
            ValidationRule("email", "regex", {"pattern": r"^[^@]+@[^@]+\.[^@]+$"}),
        ])

        result = rules.validate(df)

        assert result.is_valid

    def test_mixed_errors(self):
        """Test with both errors and warnings."""
        df = pd.DataFrame({
            "id": [1, 1, 3],  # Duplicate
            "age": [25, 30, 150]  # Out of range
        })
        rules = RuleSet([
            ValidationRule("id", "unique"),
            ValidationRule("age", "range", {"min": 0, "max": 120}, severity="warning"),
        ])

        result = rules.validate(df)

        assert not result.is_valid
        assert result.error_count > 0
        # Check that warnings are in errors with warning severity
        warning_severity_errors = [e for e in result.errors if e.severity == "warning"]
        assert len(warning_severity_errors) > 0

    def test_get_rules_for_column(self):
        """Test getting rules for specific column."""
        rules = RuleSet([
            ValidationRule("id", "unique"),
            ValidationRule("id", "required"),
            ValidationRule("name", "required"),
        ])

        id_rules = rules.get_rules_for_column("id")

        assert len(id_rules) == 2
        assert all(r.column == "id" for r in id_rules)

    def test_add_rule(self):
        """Test adding a rule."""
        rules = RuleSet([])
        assert len(rules._rules) == 0

        rules.add_rule(ValidationRule("id", "unique"))
        assert len(rules._rules) == 1

    def test_remove_rule(self):
        """Test removing a rule."""
        rules = RuleSet([
            ValidationRule("id", "unique"),
            ValidationRule("id", "required"),
        ])

        rules.remove_rule("id", "unique")

        assert len(rules._rules) == 1
        assert rules._rules[0].rule_type == "required"
