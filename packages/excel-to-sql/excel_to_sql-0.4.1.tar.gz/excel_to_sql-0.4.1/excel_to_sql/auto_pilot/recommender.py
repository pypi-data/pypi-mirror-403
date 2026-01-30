"""
Recommendations Engine for Auto-Pilot Mode.

Analyzes quality issues and generates prioritized, actionable recommendations.
"""

from typing import Dict, List, Any, Optional
from enum import Enum
import pandas as pd
from datetime import datetime


class Priority(Enum):
    """Priority levels for recommendations."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RecommendationEngine:
    """
    Generates prioritized recommendations based on quality analysis.

    Analyzes detected issues and provides actionable recommendations
    with priority levels, impact assessment, and auto-fix capability.
    """

    # Issue type to priority mapping
    PRIORITY_MAPPING = {
        "duplicate_pk": Priority.HIGH,
        "critical_validation": Priority.HIGH,
        "high_null_percentage": Priority.MEDIUM,
        "missing_default": Priority.MEDIUM,
        "future_dates": Priority.LOW,
        "low_null_percentage": Priority.LOW,
        "invalid_range": Priority.MEDIUM,
        "negative_quantity": Priority.MEDIUM,
        "minor_inconsistency": Priority.LOW,
    }

    # Auto-fixable issue types
    AUTO_FIXABLE = {
        "missing_default",
        "high_null_percentage",
        "low_null_percentage",
    }

    def __init__(self) -> None:
        """Initialize the recommendations engine."""
        self.recommendations: List[Dict[str, Any]] = []

    def generate_recommendations(
        self,
        df: pd.DataFrame,
        table_name: str,
        quality_report: Dict[str, Any],
        patterns: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on quality analysis.

        Args:
            df: DataFrame to analyze
            table_name: Name of the table
            quality_report: Quality analysis report from QualityScorer
            patterns: Detected patterns from PatternDetector

        Returns:
            List of prioritized recommendations
        """
        self.recommendations = []

        # Get primary key for reference
        primary_key = patterns.get("primary_key")

        # Process issues from quality report
        issues = quality_report.get("issues", [])

        for issue in issues:
            recommendation = self._generate_recommendation_for_issue(
                issue, df, table_name, primary_key
            )
            if recommendation:
                self.recommendations.append(recommendation)

        # Sort by priority (HIGH → MEDIUM → LOW)
        priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        self.recommendations.sort(
            key=lambda r: priority_order.get(r["priority"], 99)
        )

        return self.recommendations

    def _generate_recommendation_for_issue(
        self,
        issue: Dict[str, Any],
        df: pd.DataFrame,
        table_name: str,
        primary_key: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a recommendation for a single issue.

        Args:
            issue: Issue details from quality report
            df: DataFrame being analyzed
            table_name: Name of the table
            primary_key: Primary key column name

        Returns:
            Recommendation dictionary or None
        """
        issue_type = issue.get("type")
        column = issue.get("column")

        # Route to appropriate recommendation generator
        if issue_type == "duplicate_pk":
            return self._recommend_duplicate_pk(
                issue, df, table_name, primary_key
            )
        elif issue_type in ("high_null_percentage", "low_null_percentage"):
            return self._recommend_null_values(
                issue, df, table_name, column
            )
        elif issue_type == "future_dates":
            return self._recommend_future_dates(
                issue, df, table_name, column
            )
        elif issue_type in ("invalid_range", "negative_quantity"):
            return self._recommend_invalid_values(
                issue, df, table_name, column
            )
        elif issue_type == "missing_default":
            return self._recommend_missing_default(
                issue, df, table_name, column
            )

        return None

    def _recommend_duplicate_pk(
        self,
        issue: Dict[str, Any],
        df: pd.DataFrame,
        table_name: str,
        primary_key: Optional[str]
    ) -> Dict[str, Any]:
        """Generate recommendation for duplicate primary key."""
        column = issue.get("column", "id")
        count = issue.get("count", 0)

        # Find affected rows
        if primary_key and primary_key in df.columns:
            affected = df[df[primary_key].duplicated(keep=False)][primary_key].unique()
            affected_rows = affected[:5].tolist()  # Show up to 5 examples
        else:
            affected_rows = []

        return {
            "priority": Priority.HIGH,
            "issue": f"Duplicate primary key values ({count} duplicates)",
            "column": column,
            "table": table_name,
            "affected_rows": len(affected_rows) if affected_rows else count,
            "affected_examples": affected_rows,
            "impact": "Cannot import with duplicate primary keys. Data integrity violation.",
            "action": f"Review {column} values and remove duplicates",
            "auto_fix": False,
            "issue_type": "duplicate_pk"
        }

    def _recommend_null_values(
        self,
        issue: Dict[str, Any],
        df: pd.DataFrame,
        table_name: str,
        column: Optional[str]
    ) -> Dict[str, Any]:
        """Generate recommendation for high null percentage."""
        if not column:
            return None

        null_count = issue.get("null_count", 0)
        null_percentage = issue.get("null_percentage", 0)

        # Determine priority based on percentage
        if null_percentage > 20:
            priority = Priority.HIGH
            impact = f"Severe data quality impact. {null_percentage:.1f}% of rows missing."
        elif null_percentage > 10:
            priority = Priority.MEDIUM
            impact = f"Moderate analysis impact. {null_percentage:.1f}% of rows missing."
        else:
            priority = Priority.LOW
            impact = f"Minor analysis impact. {null_percentage:.1f}% of rows missing."

        # Suggest default value based on column type
        default_value = self._suggest_default_value(df[column])

        return {
            "priority": priority,
            "issue": f"Missing values in {column} ({null_percentage:.1f}%, {null_count} rows)",
            "column": column,
            "table": table_name,
            "affected_rows": null_count,
            "affected_examples": [],
            "impact": impact,
            "action": f"Set default value: '{default_value}' or review data entry process",
            "auto_fix": True,
            "suggested_default": default_value,
            "issue_type": "null_values"
        }

    def _recommend_future_dates(
        self,
        issue: Dict[str, Any],
        df: pd.DataFrame,
        table_name: str,
        column: Optional[str]
    ) -> Dict[str, Any]:
        """Generate recommendation for future dates."""
        if not column:
            return None

        count = issue.get("count", 0)

        return {
            "priority": Priority.LOW,
            "issue": f"Future dates detected in {column} ({count} rows)",
            "column": column,
            "table": table_name,
            "affected_rows": count,
            "affected_examples": [],
            "impact": "Minor analysis accuracy. Future dates may indicate data entry errors.",
            "action": "Review date entry process and correct future dates",
            "auto_fix": False,
            "issue_type": "future_dates"
        }

    def _recommend_invalid_values(
        self,
        issue: Dict[str, Any],
        df: pd.DataFrame,
        table_name: str,
        column: Optional[str]
    ) -> Dict[str, Any]:
        """Generate recommendation for invalid/out-of-range values."""
        if not column:
            return None

        count = issue.get("count", 0)
        issue_type = issue.get("type", "")

        if "negative" in issue_type:
            description = f"Negative values in {column}"
            action = f"Review {column} values and set validation rule: >= 0"
        else:
            description = f"Values outside valid range in {column}"
            action = f"Define validation rules for {column}"

        return {
            "priority": Priority.MEDIUM,
            "issue": f"{description} ({count} rows)",
            "column": column,
            "table": table_name,
            "affected_rows": count,
            "affected_examples": [],
            "impact": "Data validation needed. Invalid values affect analysis accuracy.",
            "action": action,
            "auto_fix": False,
            "issue_type": "invalid_values"
        }

    def _recommend_missing_default(
        self,
        issue: Dict[str, Any],
        df: pd.DataFrame,
        table_name: str,
        column: Optional[str]
    ) -> Dict[str, Any]:
        """Generate recommendation for missing default values."""
        if not column:
            return None

        count = issue.get("count", 0)
        default_value = self._suggest_default_value(df[column])

        return {
            "priority": Priority.MEDIUM,
            "issue": f"Missing default for {column} ({count} rows would benefit)",
            "column": column,
            "table": table_name,
            "affected_rows": count,
            "affected_examples": [],
            "impact": "Analysis accuracy. Default values improve data completeness.",
            "action": f"Set default value: '{default_value}'",
            "auto_fix": True,
            "suggested_default": default_value,
            "issue_type": "missing_default"
        }

    def _suggest_default_value(self, series: pd.Series) -> str:
        """
        Suggest an appropriate default value for a column.

        Args:
            series: Pandas Series to analyze

        Returns:
            Suggested default value as string
        """
        dtype = series.dtype

        # For numeric columns
        if pd.api.types.is_numeric_dtype(dtype):
            return "0"

        # For datetime columns
        if pd.api.types.is_datetime64_any_dtype(dtype):
            return "CURRENT_TIMESTAMP"

        # For string columns, look for common patterns
        if pd.api.types.is_string_dtype(dtype) or pd.api.types.is_object_dtype(dtype):
            col_lower = str(series.name).lower()

            # Common category columns
            if any(keyword in col_lower for keyword in ["category", "categorie", "type", "etat", "status"]):
                return "Non catégorisé"

            # Common description columns
            if any(keyword in col_lower for keyword in ["description", "desc", "comment", "remarque"]):
                return "Sans description"

            # Name columns
            if any(keyword in col_lower for keyword in ["nom", "name", "titre", "title"]):
                return "Sans nom"

        # Default fallback
        return "NULL"

    def get_recommendations_by_priority(
        self,
        priority: Priority
    ) -> List[Dict[str, Any]]:
        """
        Get all recommendations for a specific priority level.

        Args:
            priority: Priority level to filter by

        Returns:
            List of recommendations with specified priority
        """
        return [r for r in self.recommendations if r["priority"] == priority]

    def get_auto_fixable_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get all auto-fixable recommendations.

        Returns:
            List of recommendations that can be auto-fixed
        """
        return [r for r in self.recommendations if r.get("auto_fix", False)]

    def get_manual_review_recommendations(self) -> List[Dict[str, Any]]:
        """
        Get all recommendations requiring manual review.

        Returns:
            List of recommendations requiring manual review
        """
        return [r for r in self.recommendations if not r.get("auto_fix", False)]

    def get_summary(self) -> Dict[str, int]:
        """
        Get summary statistics of recommendations.

        Returns:
            Dictionary with counts by priority and auto-fix status
        """
        return {
            "total": len(self.recommendations),
            "high": len(self.get_recommendations_by_priority(Priority.HIGH)),
            "medium": len(self.get_recommendations_by_priority(Priority.MEDIUM)),
            "low": len(self.get_recommendations_by_priority(Priority.LOW)),
            "auto_fixable": len(self.get_auto_fixable_recommendations()),
            "manual_review": len(self.get_manual_review_recommendations())
        }
