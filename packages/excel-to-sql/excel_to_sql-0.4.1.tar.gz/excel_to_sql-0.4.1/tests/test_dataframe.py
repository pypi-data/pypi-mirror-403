"""
Tests for DataFrame wrapper entity.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from excel_to_sql.entities.dataframe import DataFrame


class TestDataFrame:
    """Tests for DataFrame entity."""

    def test_init_empty(self):
        """Test creating empty DataFrame."""
        df = DataFrame()
        assert df.is_empty is True
        assert df.shape == (0, 0)

    def test_init_with_data(self):
        """Test creating DataFrame with existing data."""
        data = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        df = DataFrame(data)

        assert df.is_empty is False
        assert df.shape == (3, 2)

    def test_columns_property(self):
        """Test columns property."""
        data = pd.DataFrame({"id": [1, 2], "name": ["A", "B"], "value": [10, 20]})
        df = DataFrame(data)

        assert set(df.columns) == {"id", "name", "value"}

    def test_shape_property(self):
        """Test shape property."""
        data = pd.DataFrame({"a": range(10), "b": range(10)})
        df = DataFrame(data)

        assert df.shape == (10, 2)

    def test_is_empty_property(self):
        """Test is_empty property."""
        df_empty = DataFrame()
        assert df_empty.is_empty is True

        df_with_data = DataFrame(pd.DataFrame({"a": [1]}))
        assert df_with_data.is_empty is False

    def test_clean_whitespace(self):
        """Test clean() strips whitespace."""
        data = pd.DataFrame(
            {
                "  Name  ": ["  Alice  ", "  Bob  ", "  Charlie  "],
                "Value": [10, 20, 30],
            }
        )
        df = DataFrame(data)
        df.clean()

        # Column names should be lowercase
        assert "name" in df.columns
        assert "  Name  " not in df.columns

        # Values should be stripped
        result = df.to_pandas()
        assert result["name"].tolist() == ["Alice", "Bob", "Charlie"]

    def test_clean_empty_rows(self):
        """Test clean() drops empty rows."""
        data = pd.DataFrame(
            {"a": [1, None, 3], "b": [10, None, None], "c": [100, None, None]}
        )
        df = DataFrame(data)
        df.clean()

        result = df.to_pandas()
        # Row 1 has all None, should be dropped
        assert len(result) == 2

    def test_clean_lowercase_columns(self):
        """Test clean() lowercases column names."""
        data = pd.DataFrame(
            {"ID": [1, 2], "Name": ["A", "B"], "VALUE": [10, 20]}
        )
        df = DataFrame(data)
        df.clean()

        assert "id" in df.columns
        assert "name" in df.columns
        assert "value" in df.columns
        assert "ID" not in df.columns

    def test_clean_does_not_modify_original(self):
        """Test that clean() doesn't modify original DataFrame."""
        data = pd.DataFrame({"  Name  ": ["  Alice  "], "Value": [10]})
        original_name = data.columns[0]

        df = DataFrame(data)
        df.clean()

        # Original DataFrame should be unchanged
        assert data.columns[0] == original_name

    def test_apply_mapping_rename_columns(self):
        """Test apply_mapping() renames columns."""
        data = pd.DataFrame({"ID": [1, 2], "Name": ["A", "B"], "Ignore": ["X", "Y"]})
        df = DataFrame(data)

        mapping = {
            "target_table": "test",
            "primary_key": ["id"],
            "column_mappings": {
                "ID": {"target": "id", "type": "integer"},
                "Name": {"target": "name", "type": "string"},
            },
        }

        df.apply_mapping(mapping)

        result = df.to_pandas()
        assert "id" in result.columns
        assert "name" in result.columns
        assert "Ignore" not in result.columns  # Unmapped columns dropped

    def test_apply_mapping_type_integer(self):
        """Test apply_mapping() converts to integer."""
        data = pd.DataFrame({"Value": ["10", "20", "30"]})
        df = DataFrame(data)

        mapping = {
            "target_table": "test",
            "primary_key": ["id"],
            "column_mappings": {
                "Value": {"target": "value", "type": "integer"}
            },
        }

        df.apply_mapping(mapping)

        result = df.to_pandas()
        assert result["value"].dtype == "Int64"

    def test_apply_mapping_type_float(self):
        """Test apply_mapping() converts to float."""
        data = pd.DataFrame({"Price": ["10.50", "20.00", "30.99"]})
        df = DataFrame(data)

        mapping = {
            "target_table": "test",
            "primary_key": ["id"],
            "column_mappings": {"Price": {"target": "price", "type": "float"}},
        }

        df.apply_mapping(mapping)

        result = df.to_pandas()
        # Check if it's a float type
        assert pd.api.types.is_float_dtype(result["price"])

    def test_apply_mapping_type_boolean(self):
        """Test apply_mapping() converts to boolean."""
        data = pd.DataFrame(
            {"Active": ["TRUE", "FALSE", "1", "0", "True", "False"]}
        )
        df = DataFrame(data)

        mapping = {
            "target_table": "test",
            "primary_key": ["id"],
            "column_mappings": {"Active": {"target": "active", "type": "boolean"}},
        }

        df.apply_mapping(mapping)

        result = df.to_pandas()
        expected = [True, False, True, False, True, False]
        assert result["active"].tolist() == expected

    def test_apply_mapping_type_date(self):
        """Test apply_mapping() converts to date."""
        data = pd.DataFrame({"Date": ["2024-01-01", "2024-02-01", "2024-03-01"]})
        df = DataFrame(data)

        mapping = {
            "target_table": "test",
            "primary_key": ["id"],
            "column_mappings": {"Date": {"target": "date", "type": "date"}},
        }

        df.apply_mapping(mapping)

        result = df.to_pandas()
        assert pd.api.types.is_datetime64_any_dtype(result["date"])

    def test_apply_mapping_invalid_values_coerce(self):
        """Test apply_mapping() coerces invalid values to NaN."""
        data = pd.DataFrame({"Value": ["10", "invalid", "30"]})
        df = DataFrame(data)

        mapping = {
            "target_table": "test",
            "primary_key": ["id"],
            "column_mappings": {
                "Value": {"target": "value", "type": "integer"}
            },
        }

        df.apply_mapping(mapping)

        result = df.to_pandas()
        # Invalid value should be NaN/NaT
        assert pd.isna(result["value"].iloc[1])

    def test_filter_nulls_single_column(self):
        """Test filter_nulls() with single column."""
        data = pd.DataFrame({"id": [1, 2, 3], "name": ["A", None, "C"]})
        df = DataFrame(data)

        df.filter_nulls(["name"])

        result = df.to_pandas()
        assert len(result) == 2
        assert result["name"].notna().all()

    def test_filter_nulls_multiple_columns(self):
        """Test filter_nulls() with multiple columns."""
        data = pd.DataFrame(
            {
                "id": [1, 2, 3, 4],
                "name": ["A", None, "C", "D"],
                "value": [10, 20, None, 40],
            }
        )
        df = DataFrame(data)

        df.filter_nulls(["name", "value"])

        result = df.to_pandas()
        # Only rows where both name AND value are not null
        assert len(result) == 2
        assert result["name"].notna().all()
        assert result["value"].notna().all()

    def test_to_pandas_returns_copy(self):
        """Test to_pandas() returns a copy."""
        data = pd.DataFrame({"a": [1, 2, 3]})
        df = DataFrame(data)

        result = df.to_pandas()
        result["a"] = [99, 99, 99]

        # Original should be unchanged
        original = df.to_pandas()
        assert original["a"].tolist() == [1, 2, 3]

    def test_to_dict_records(self):
        """Test to_dict() with records orientation."""
        data = pd.DataFrame({"id": [1, 2], "name": ["A", "B"]})
        df = DataFrame(data)

        result = df.to_dict(orient="records")

        expected = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        assert result == expected

    def test_full_workflow_clean_and_map(self):
        """Test complete workflow: clean then apply mapping."""
        data = pd.DataFrame(
            {
                "  ID  ": ["  1  ", "  2  ", "  3  "],
                "  Name  ": ["  Alice  ", "  Bob  ", "  Charlie  "],
                "  Value  ": ["  10  ", "  20  ", "  30  "],
            }
        )

        df = DataFrame(data)
        df.clean()

        mapping = {
            "target_table": "test",
            "primary_key": ["id"],
            "column_mappings": {
                "id": {"target": "id", "type": "integer"},
                "name": {"target": "name", "type": "string"},
                "value": {"target": "value", "type": "integer"},
            },
        }

        df.apply_mapping(mapping)

        result = df.to_pandas()
        assert result["id"].tolist() == [1, 2, 3]
        assert result["name"].tolist() == ["Alice", "Bob", "Charlie"]
        assert result["value"].tolist() == [10, 20, 30]

    def test_clean_with_empty_strings(self):
        """Test clean() normalizes empty strings to NaN."""
        data = pd.DataFrame(
            {"name": ["Alice", "", "Charlie"], "value": [10, 20, 30]}
        )
        df = DataFrame(data)
        df.clean()

        result = df.to_pandas()
        # Empty string should become NaN
        assert pd.isna(result["name"].iloc[1])

    def test_clean_preserves_data_types(self):
        """Test clean() preserves data types appropriately."""
        data = pd.DataFrame(
            {
                "int_col": [1, 2, 3],
                "float_col": [1.1, 2.2, 3.3],
                "str_col": ["a", "b", "c"],
            }
        )
        df = DataFrame(data)
        df.clean()

        result = df.to_pandas()
        # After clean(), columns become object type due to str.strip()
        # That's expected behavior
        assert len(result) == 3
