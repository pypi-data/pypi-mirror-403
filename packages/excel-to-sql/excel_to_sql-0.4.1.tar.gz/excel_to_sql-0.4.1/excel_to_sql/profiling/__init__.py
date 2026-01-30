"""
Data profiling package.

Analyzes data quality and generates quality reports.
"""

from excel_to_sql.profiling.profiler import DataProfiler
from excel_to_sql.profiling.report import QualityReport

__all__ = [
    "DataProfiler",
    "QualityReport",
]
