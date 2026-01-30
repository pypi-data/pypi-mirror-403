"""
Pydantic models for mapping configuration.

Provides validation and type safety for column mappings.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Literal, Union


class ColumnMapping(BaseModel):
    """Configuration for a single column mapping."""

    target: str = Field(..., description="Target column name in database")
    type: Literal["string", "integer", "float", "boolean", "date"] = Field(
        default="string",
        description="SQL type for the column",
    )
    required: bool = Field(
        default=False, description="Whether null values should be rejected"
    )
    default: Optional[Any] = Field(
        default=None, description="Default value if column is missing"
    )


class ValueMappingConfig(BaseModel):
    """Configuration for value mapping."""

    column: str = Field(..., description="Column name to apply mapping to")
    mappings: Dict[str, Any] = Field(..., description="Value mappings: source -> target")


class CalculatedColumnConfig(BaseModel):
    """Configuration for calculated columns."""

    name: str = Field(..., description="Name of the calculated column")
    expression: Optional[str] = Field(None, description="Expression to calculate")
    type: Optional[str] = Field(None, description="Data type for the result")


class ValidationRuleConfig(BaseModel):
    """Configuration for validation rules."""

    column: str = Field(..., description="Column to validate")
    type: Literal["required", "unique", "range", "regex", "enum", "custom"] = Field(
        ..., description="Type of validation rule"
    )
    params: Dict[str, Any] = Field(default_factory=dict, description="Rule parameters")
    message: Optional[str] = Field(None, description="Custom error message")
    severity: Literal["error", "warning", "info"] = Field(
        default="error", description="Severity level"
    )


class ReferenceValidationConfig(BaseModel):
    """Configuration for reference validation."""

    column: str = Field(..., description="Column to validate")
    reference_table: str = Field(..., description="Table to reference")
    reference_column: str = Field(default="id", description="Column in reference table")


class HookConfig(BaseModel):
    """Configuration for processing hooks."""

    type: Literal["pre_import", "post_import", "pre_export", "post_export"] = Field(
        ..., description="When to execute the hook"
    )
    module: str = Field(..., description="Python module containing the hook function")
    function: str = Field(..., description="Function name to call")


class TypeMapping(BaseModel):
    """Configuration for a file type."""

    target_table: str = Field(..., description="Destination table name")
    primary_key: List[str] = Field(
        ..., description="Primary key columns (for UPSERT)"
    )
    column_mappings: Dict[str, ColumnMapping] = Field(
        ..., description="Map of Excel column names to their configuration"
    )
    # New optional fields
    value_mappings: List[ValueMappingConfig] = Field(
        default_factory=list, description="Value mapping configurations"
    )
    calculated_columns: List[CalculatedColumnConfig] = Field(
        default_factory=list, description="Calculated column configurations"
    )
    validation_rules: List[ValidationRuleConfig] = Field(
        default_factory=list, description="Validation rule configurations"
    )
    reference_validations: List[ReferenceValidationConfig] = Field(
        default_factory=list, description="Reference validation configurations"
    )
    hooks: List[HookConfig] = Field(
        default_factory=list, description="Processing hook configurations"
    )
    tags: List[str] = Field(
        default_factory=list, description="Tags for this import type"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Custom metadata"
    )


class Mappings(BaseModel):
    """Root container for all mappings."""

    mappings: Dict[str, TypeMapping]

    def get_type(self, type_name: str) -> TypeMapping | None:
        """
        Get a specific type mapping.

        Args:
            type_name: Name of the type mapping

        Returns:
            TypeMapping or None if not found
        """
        return self.mappings.get(type_name)

    def list_types(self) -> list[str]:
        """List all configured type names."""
        return list(self.mappings.keys())
