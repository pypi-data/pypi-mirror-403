"""
Data profiler for quality analysis.
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from datetime import datetime


@dataclass
class ColumnProfile:
    """
    Profile information for a single column.
    """

    name: str
    dtype: str
    count: int
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    distinct_values: List[Any] = field(default_factory=list)
    min_value: Any = None
    max_value: Any = None
    mean_value: float = None
    median_value: float = None
    std_value: float = None
    sample_values: List[Any] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "dtype": self.dtype,
            "count": self.count,
            "null_count": self.null_count,
            "null_percentage": round(self.null_percentage, 2),
            "unique_count": self.unique_count,
            "unique_percentage": round(self.unique_percentage, 2),
            "distinct_values": self.distinct_values[:20],  # Limit to 20
            "min": str(self.min_value) if self.min_value is not None else None,
            "max": str(self.max_value) if self.max_value is not None else None,
            "mean": round(self.mean_value, 2) if self.mean_value is not None else None,
            "median": round(self.median_value, 2) if self.median_value is not None else None,
            "std": round(self.std_value, 2) if self.std_value is not None else None,
            "sample_values": [str(v) for v in self.sample_values[:10]],
        }


class DataProfiler:
    """
    Analyzes data quality and generates profiles.

    Example:
        profiler = DataProfiler()
        profile = profiler.profile(df)
        print(profile.to_dict())
    """

    def __init__(self, max_distinct: int = 100) -> None:
        """
        Initialize data profiler.

        Args:
            max_distinct: Maximum number of distinct values to track
        """
        self.max_distinct = max_distinct

    def profile(self, df: pd.DataFrame) -> "DataFrameProfile":
        """
        Profile a DataFrame.

        Args:
            df: DataFrame to analyze

        Returns:
            DataFrameProfile with analysis results
        """
        total_rows = len(df)
        total_columns = len(df.columns)
        total_cells = total_rows * total_columns
        total_nulls = df.isnull().sum().sum()

        # Profile each column
        column_profiles = []
        for col in df.columns:
            col_profile = self._profile_column(df[col])
            column_profiles.append(col_profile)

        return DataFrameProfile(
            total_rows=total_rows,
            total_columns=total_columns,
            total_cells=total_cells,
            total_nulls=total_nulls,
            null_percentage=(total_nulls / total_cells * 100) if total_cells > 0 else 0,
            column_profiles=column_profiles,
        )

    def _profile_column(self, series: pd.Series) -> ColumnProfile:
        """Profile a single column."""
        name = series.name
        dtype = str(series.dtype)
        count = len(series)
        null_count = series.isnull().sum()
        null_percentage = (null_count / count * 100) if count > 0 else 0

        # Unique values
        unique_count = series.nunique()
        unique_percentage = (unique_count / count * 100) if count > 0 else 0

        # Distinct values (limited)
        distinct_values = []
        if unique_count <= self.max_distinct:
            distinct_values = series.dropna().unique().tolist()

        # Statistics
        min_value = None
        max_value = None
        mean_value = None
        median_value = None
        std_value = None

        if series.dtype in ["int64", "float64", "Int64", "float"]:
            min_value = series.min()
            max_value = series.max()
            mean_value = series.mean()
            median_value = series.median()
            std_value = series.std()

        # Sample values
        sample_values = series.dropna().head(5).tolist()

        return ColumnProfile(
            name=name,
            dtype=dtype,
            count=count,
            null_count=null_count,
            null_percentage=null_percentage,
            unique_count=unique_count,
            unique_percentage=unique_percentage,
            distinct_values=distinct_values,
            min_value=min_value,
            max_value=max_value,
            mean_value=mean_value,
            median_value=median_value,
            std_value=std_value,
            sample_values=sample_values,
        )


@dataclass
class DataFrameProfile:
    """
    Complete profile of a DataFrame.
    """

    total_rows: int
    total_columns: int
    total_cells: int
    total_nulls: int
    null_percentage: float
    column_profiles: List[ColumnProfile]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_issues(self) -> List[Dict[str, Any]]:
        """
        Identify data quality issues.

        Returns:
            List of issue dictionaries
        """
        issues = []

        # High null columns
        for col in self.column_profiles:
            if col.null_percentage > 50:
                issues.append({
                    "severity": "warning",
                    "column": col.name,
                    "issue": "High null count",
                    "value": f"{col.null_percentage:.1f}% null",
                })

        # Potential ID columns (high uniqueness)
        for col in self.column_profiles:
            if col.unique_percentage > 95 and col.unique_count > 10:
                issues.append({
                    "severity": "info",
                    "column": col.name,
                    "issue": "Potential key column",
                    "value": f"{col.unique_percentage:.1f}% unique",
                })

        # Low cardinality columns (potential enums)
        for col in self.column_profiles:
            if col.unique_count < 10 and col.unique_count > 1:
                issues.append({
                    "severity": "info",
                    "column": col.name,
                    "issue": "Low cardinality",
                    "value": f"{col.unique_count} distinct values",
                })

        return issues

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "summary": {
                "total_rows": self.total_rows,
                "total_columns": self.total_columns,
                "total_cells": self.total_cells,
                "total_nulls": self.total_nulls,
                "null_percentage": round(self.null_percentage, 2),
                "timestamp": self.timestamp,
            },
            "columns": [col.to_dict() for col in self.column_profiles],
            "issues": self.get_issues(),
        }

    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            "# Data Quality Report",
            "",
            f"Generated: {self.timestamp}",
            "",
            "## Summary",
            "",
            f"- **Rows:** {self.total_rows:,}",
            f"- **Columns:** {self.total_columns}",
            f"- **Total Cells:** {self.total_cells:,}",
            f"- **Null Cells:** {self.total_nulls:,} ({self.null_percentage:.1f}%)",
            "",
            "## Columns",
            "",
        ]

        for col in self.column_profiles:
            lines.append(f"### {col.name}")
            lines.append(f"- **Type:** {col.dtype}")
            lines.append(f"- **Null:** {col.null_count:,} ({col.null_percentage:.1f}%)")
            lines.append(f"- **Unique:** {col.unique_count:,} ({col.unique_percentage:.1f}%)")

            if col.min_value is not None:
                lines.append(f"- **Range:** {col.min_value} to {col.max_value}")
            if col.mean_value is not None:
                lines.append(f"- **Mean:** {col.mean_value:.2f}")

            if col.distinct_values:
                lines.append(f"- **Values:** {', '.join(str(v) for v in col.distinct_values[:10])}")

            lines.append("")

        # Issues
        issues = self.get_issues()
        if issues:
            lines.append("## Issues")
            lines.append("")

            for issue in issues:
                icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(issue["severity"], "•")
                lines.append(f"{icon} **{issue['column']}**: {issue['issue']} - {issue['value']}")

            lines.append("")

        return "\n".join(lines)
