"""Excel to SQL - Import Excel files to SQL and export back."""

from excel_to_sql.__version__ import __version__

# Main SDK
from excel_to_sql.sdk import ExcelToSqlite

# Entities
from excel_to_sql.entities.project import Project
from excel_to_sql.entities.database import Database
from excel_to_sql.entities.excel_file import ExcelFile
from excel_to_sql.entities.dataframe import DataFrame
from excel_to_sql.entities.table import Table

# Transformations
from excel_to_sql.transformations.mapping import ValueMapping
from excel_to_sql.transformations.calculated import CalculatedColumn, CalculatedColumns
from excel_to_sql.transformations.hooks import HookSystem, ImportContext, ExportContext

# Validators
from excel_to_sql.validators.base import BaseValidator, ValidationResult
from excel_to_sql.validators.custom import (
    CustomValidator,
    RangeValidator,
    RegexValidator,
    UniqueValidator,
    NotNullValidator,
    EnumValidator,
)
from excel_to_sql.validators.reference import ReferenceValidator
from excel_to_sql.validators.rules import ValidationRule, RuleSet

# Profiling
from excel_to_sql.profiling.profiler import DataProfiler, ColumnProfile, DataFrameProfile
from excel_to_sql.profiling.report import QualityReport

# Metadata
from excel_to_sql.metadata.store import MetadataStore
from excel_to_sql.metadata.models import ImportMetadata

__all__ = [
    # Version
    "__version__",
    # SDK
    "ExcelToSqlite",
    # Entities
    "Project",
    "Database",
    "ExcelFile",
    "DataFrame",
    "Table",
    # Transformations
    "ValueMapping",
    "CalculatedColumn",
    "CalculatedColumns",
    "HookSystem",
    "ImportContext",
    "ExportContext",
    # Validators
    "BaseValidator",
    "ValidationResult",
    "CustomValidator",
    "RangeValidator",
    "RegexValidator",
    "UniqueValidator",
    "NotNullValidator",
    "EnumValidator",
    "ReferenceValidator",
    "ValidationRule",
    "RuleSet",
    # Profiling
    "DataProfiler",
    "ColumnProfile",
    "DataFrameProfile",
    "QualityReport",
    # Metadata
    "MetadataStore",
    "ImportMetadata",
]
