"""
Tests for data profiling.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from excel_to_sql.profiling.profiler import DataProfiler, ColumnProfile, DataFrameProfile
from excel_to_sql.profiling.report import QualityReport
from pathlib import Path


class TestDataProfiler:
    """Tests for DataProfiler."""

    def test_profile_dataframe(self):
        """Test profiling a DataFrame."""
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
            "age": [25, 30, 35, 40, 45],
            "score": [95.5, 87.3, 92.1, 88.9, 90.5],
        })

        profiler = DataProfiler()
        profile = profiler.profile(df)

        assert profile.total_rows == 5
        assert profile.total_columns == 4
        assert profile.total_cells == 20
        assert profile.total_nulls == 0
        assert profile.null_percentage == 0.0

    def test_profile_with_nulls(self):
        """Test profiling DataFrame with null values."""
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "name": ["Alice", None, "Charlie", "David", None],
            "age": [25, 30, None, 40, 45],
        })

        profiler = DataProfiler()
        profile = profiler.profile(df)

        assert profile.total_nulls == 3
        assert profile.null_percentage == 20.0  # 3 out of 15 cells

    def test_column_profile(self):
        """Test profiling a single column."""
        df = pd.DataFrame({
            "age": [25, 30, 35, 40, 45]
        })

        profiler = DataProfiler()
        profile = profiler.profile(df)

        assert len(profile.column_profiles) == 1

        col_profile = profile.column_profiles[0]
        assert col_profile.name == "age"
        assert col_profile.count == 5
        assert col_profile.null_count == 0
        assert col_profile.unique_count == 5
        assert col_profile.min_value == 25
        assert col_profile.max_value == 45
        assert col_profile.mean_value == 35.0
        assert col_profile.median_value == 35.0

    def test_string_column_profile(self):
        """Test profiling string columns."""
        df = pd.DataFrame({
            "category": ["A", "B", "A", "C", "B"]
        })

        profiler = DataProfiler()
        profile = profiler.profile(df)

        col_profile = profile.column_profiles[0]
        assert col_profile.name == "category"
        assert col_profile.unique_count == 3
        assert col_profile.min_value is None  # No stats for strings
        assert col_profile.max_value is None
        assert set(col_profile.distinct_values) == {"A", "B", "C"}

    def test_low_cardinality_detection(self):
        """Test detection of low cardinality columns."""
        df = pd.DataFrame({
            "status": ["active", "inactive", "active", "active", "inactive"]
        })

        profiler = DataProfiler()
        profile = profiler.profile(df)

        issues = profile.get_issues()

        # Should detect low cardinality (only 2 unique values)
        low_card = [i for i in issues if i["issue"] == "Low cardinality"]
        assert len(low_card) > 0

    def test_high_null_detection(self):
        """Test detection of high null columns."""
        df = pd.DataFrame({
            "column1": [1, 2, None, None, None],  # 60% null
            "column2": [1, 2, 3, 4, 5],  # 0% null
        })

        profiler = DataProfiler()
        profile = profiler.profile(df)

        issues = profile.get_issues()

        # Should detect high null count in column1
        high_nulls = [i for i in issues if i["issue"] == "High null count" and i["column"] == "column1"]
        assert len(high_nulls) > 0

    def test_key_column_detection(self):
        """Test detection of potential key columns."""
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # Need more than 10 rows
        })

        profiler = DataProfiler()
        profile = profiler.profile(df)

        issues = profile.get_issues()

        # Should detect potential key column
        keys = [i for i in issues if i["issue"] == "Potential key column"]
        assert len(keys) > 0

    def test_to_dict(self):
        """Test converting profile to dictionary."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })

        profiler = DataProfiler()
        profile = profiler.profile(df)

        d = profile.to_dict()

        assert "summary" in d
        assert "columns" in d
        assert "issues" in d
        assert d["summary"]["total_rows"] == 3
        assert len(d["columns"]) == 2

    def test_to_markdown(self):
        """Test converting profile to markdown."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })

        profiler = DataProfiler()
        profile = profiler.profile(df)

        markdown = profile.to_markdown()

        assert "# Data Quality Report" in markdown
        assert "## Summary" in markdown
        assert "## Columns" in markdown
        assert "3" in markdown  # Row count


class TestQualityReport:
    """Tests for QualityReport."""

    def test_generate_report(self):
        """Test generating a quality report."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })

        report = QualityReport()
        profile = report.generate(df)

        assert profile.total_rows == 3
        assert profile.total_columns == 2

    def test_save_json_report(self, tmp_path):
        """Test saving report as JSON."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })

        report = QualityReport()
        profile = report.generate(df)

        output_file = tmp_path / "report.json"
        report.save_report(profile, output_file)

        assert output_file.exists()

        # Load and verify
        import json
        with open(output_file) as f:
            data = json.load(f)

        assert data["summary"]["total_rows"] == 3

    def test_save_markdown_report(self, tmp_path):
        """Test saving report as Markdown."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })

        report = QualityReport()
        profile = report.generate(df)

        output_file = tmp_path / "report.md"
        report.save_report(profile, output_file)

        assert output_file.exists()

        content = output_file.read_text(encoding="utf-8")
        assert "# Data Quality Report" in content

    def test_save_html_report(self, tmp_path):
        """Test saving report as HTML."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })

        report = QualityReport()
        profile = report.generate(df)

        output_file = tmp_path / "report.html"
        report.save_report(profile, output_file)

        assert output_file.exists()

        content = output_file.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "Data Quality Report" in content

    def test_generate_with_output_path(self, tmp_path):
        """Test generating report directly to file."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"]
        })

        report = QualityReport()
        output_file = tmp_path / "report.json"

        profile = report.generate(df, output_path=output_file)

        assert output_file.exists()
        assert profile.total_rows == 3
