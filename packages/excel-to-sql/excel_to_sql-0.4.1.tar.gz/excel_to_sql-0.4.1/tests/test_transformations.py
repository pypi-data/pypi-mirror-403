"""
Tests for data transformations.
"""

import pytest
import pandas as pd
from excel_to_sql.transformations.mapping import ValueMapping
from excel_to_sql.transformations.calculated import CalculatedColumn, CalculatedColumns


class TestValueMapping:
    """Tests for ValueMapping."""

    def test_simple_mapping(self):
        """Test simple value mapping."""
        df = pd.DataFrame({
            "status": ["1", "0", "1", "0"],
            "value": [10, 20, 30, 40]
        })

        mapping = ValueMapping({
            "status": {"1": "Active", "0": "Inactive"}
        })

        result = mapping.apply(df)

        assert result["status"].tolist() == ["Active", "Inactive", "Active", "Inactive"]
        assert result["value"].tolist() == [10, 20, 30, 40]

    def test_multiple_columns(self):
        """Test mapping multiple columns."""
        df = pd.DataFrame({
            "state": ["NY", "CA", "TX"],
            "level": ["1", "2", "3"]
        })

        mapping = ValueMapping({
            "state": {"NY": "New York", "CA": "California", "TX": "Texas"},
            "level": {"1": "Low", "2": "Medium", "3": "High"}
        })

        result = mapping.apply(df)

        assert result["state"].tolist() == ["New York", "California", "Texas"]
        assert result["level"].tolist() == ["Low", "Medium", "High"]

    def test_preserves_unmapped_values(self):
        """Test that unmapped values are preserved."""
        df = pd.DataFrame({
            "category": ["A", "B", "C"]
        })

        mapping = ValueMapping({
            "category": {"A": "Alpha", "B": "Beta"}
            # Note: "C" is not mapped
        })

        result = mapping.apply(df)

        assert result["category"].tolist() == ["Alpha", "Beta", "C"]

    def test_preserves_nulls(self):
        """Test that null values are preserved."""
        df = pd.DataFrame({
            "status": ["1", None, "0", None]
        })

        mapping = ValueMapping({
            "status": {"1": "Active", "0": "Inactive"}
        })

        result = mapping.apply(df)

        assert result["status"].tolist()[0] == "Active"
        assert pd.isna(result["status"].tolist()[1])
        assert result["status"].tolist()[2] == "Inactive"
        assert pd.isna(result["status"].tolist()[3])

    def test_get_mapping_stats(self):
        """Test getting mapping statistics."""
        df = pd.DataFrame({
            "state": ["NY", "NY", "CA", "TX", "NY"]
        })

        mapping = ValueMapping({
            "state": {"NY": "New York", "CA": "California"}
        })

        stats = mapping.get_mapping_stats(df)

        assert stats["state"]["NY"] == 3
        assert stats["state"]["CA"] == 1
        assert "TX" not in stats["state"]


class TestCalculatedColumn:
    """Tests for CalculatedColumn."""

    def test_simple_expression(self):
        """Test simple calculated column with expression."""
        df = pd.DataFrame({
            "quantity": [2, 3, 4],
            "price": [10, 20, 30]
        })

        column = CalculatedColumn(
            name="total",
            expression="quantity * price"
        )

        result = column.apply(df)

        assert result["total"].tolist() == [20, 60, 120]

    def test_string_expression(self):
        """Test calculated column with string concatenation."""
        df = pd.DataFrame({
            "first": ["John", "Jane"],
            "last": ["Doe", "Smith"]
        })

        column = CalculatedColumn(
            name="full_name",
            expression="first.str.cat(last, sep=' ')"
        )

        result = column.apply(df)

        assert result["full_name"].tolist() == ["John Doe", "Jane Smith"]

    def test_with_dtype_conversion(self):
        """Test calculated column with type conversion."""
        df = pd.DataFrame({
            "value": [1.5, 2.7, 3.9]
        })

        column = CalculatedColumn(
            name="rounded",
            expression="value.round()",
            dtype="int"
        )

        result = column.apply(df)

        assert result["rounded"].dtype == "int"
        assert result["rounded"].tolist() == [2, 3, 4]

    def test_validate_success(self):
        """Test validation with valid expression."""
        df = pd.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6]
        })

        column = CalculatedColumn(
            name="sum",
            expression="a + b"
        )

        errors = column.validate(df)

        assert errors == []

    def test_validate_missing_column(self):
        """Test validation with missing column."""
        df = pd.DataFrame({
            "a": [1, 2, 3]
        })

        column = CalculatedColumn(
            name="sum",
            expression="a + b"  # 'b' doesn't exist
        )

        errors = column.validate(df)

        assert len(errors) > 0
        assert "b" in errors[0]


class TestCalculatedColumns:
    """Tests for CalculatedColumns collection."""

    def test_multiple_columns(self):
        """Test applying multiple calculated columns."""
        df = pd.DataFrame({
            "quantity": [2, 3, 4],
            "price": [10, 20, 30]
        })

        columns = CalculatedColumns([
            CalculatedColumn("subtotal", "quantity * price"),
            CalculatedColumn("tax", "subtotal * 0.1"),
            CalculatedColumn("total", "subtotal + tax")
        ])

        result = columns.apply(df)

        assert "subtotal" in result.columns
        assert "tax" in result.columns
        assert "total" in result.columns

        # Check first row
        assert result["subtotal"].iloc[0] == 20
        assert result["tax"].iloc[0] == 2.0
        assert result["total"].iloc[0] == 22.0

    def test_validate_all(self):
        """Test validating all calculated columns."""
        df = pd.DataFrame({
            "a": [1, 2, 3]
        })

        columns = CalculatedColumns([
            CalculatedColumn("double", "a * 2"),
            CalculatedColumn("triple", "a * 3"),
        ])

        errors = columns.validate(df)

        assert errors == {}

    def test_validate_with_errors(self):
        """Test validation with errors."""
        df = pd.DataFrame({
            "a": [1, 2, 3]
        })

        columns = CalculatedColumns([
            CalculatedColumn("double", "a * 2"),
            CalculatedColumn("missing_ref", "a + b"),  # 'b' doesn't exist
        ])

        errors = columns.validate(df)

        assert "missing_ref" in errors
        assert len(errors["missing_ref"]) > 0
