"""
Unit tests for Recommendations Engine.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta

from excel_to_sql.auto_pilot.recommender import (
    RecommendationEngine,
    Priority
)


class TestRecommendationEngine:
    """Unit tests for RecommendationEngine class."""

    def test_initialization(self) -> None:
        """Test that RecommendationEngine initializes correctly."""
        engine = RecommendationEngine()
        assert engine.recommendations == []

    def test_priority_enum(self) -> None:
        """Test Priority enum values."""
        assert Priority.HIGH.value == "high"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.LOW.value == "low"

    def test_generate_recommendations_empty_issues(self) -> None:
        """Test generating recommendations with no issues."""
        engine = RecommendationEngine()
        df = pd.DataFrame({"id": [1, 2, 3], "name": ["A", "B", "C"]})

        quality_report = {
            "score": 100,
            "grade": "A+",
            "issues": []
        }

        patterns = {"primary_key": "id"}

        recommendations = engine.generate_recommendations(df, "test_table", quality_report, patterns)

        assert len(recommendations) == 0
        assert engine.get_summary()["total"] == 0

    def test_recommend_duplicate_pk(self) -> None:
        """Test recommendation for duplicate primary key."""
        engine = RecommendationEngine()
        df = pd.DataFrame({
            "id": [1, 2, 2, 3, 3, 3],
            "name": ["A", "B", "C", "D", "E", "F"]
        })

        quality_report = {
            "score": 70,
            "grade": "C",
            "issues": [
                {
                    "type": "duplicate_pk",
                    "column": "id",
                    "count": 3
                }
            ]
        }

        patterns = {"primary_key": "id"}

        recommendations = engine.generate_recommendations(df, "test_table", quality_report, patterns)

        assert len(recommendations) == 1
        assert recommendations[0]["priority"] == Priority.HIGH
        assert "Duplicate primary key" in recommendations[0]["issue"]
        assert recommendations[0]["column"] == "id"
        assert recommendations[0]["auto_fix"] is False
        assert "Cannot import" in recommendations[0]["impact"]

    def test_recommend_null_values_high_percentage(self) -> None:
        """Test recommendation for high null percentage."""
        engine = RecommendationEngine()
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "category": ["A", None, None, None, None]  # 80% null
        })

        quality_report = {
            "score": 75,
            "grade": "C",
            "issues": [
                {
                    "type": "high_null_percentage",
                    "column": "category",
                    "null_count": 4,
                    "null_percentage": 80.0
                }
            ]
        }

        patterns = {"primary_key": "id"}

        recommendations = engine.generate_recommendations(df, "products", quality_report, patterns)

        assert len(recommendations) == 1
        assert recommendations[0]["priority"] == Priority.HIGH
        assert "Missing values" in recommendations[0]["issue"]
        assert "80.0%" in recommendations[0]["issue"]
        assert recommendations[0]["column"] == "category"
        assert recommendations[0]["auto_fix"] is True
        assert "suggested_default" in recommendations[0]

    def test_recommend_null_values_medium_percentage(self) -> None:
        """Test recommendation for medium null percentage."""
        engine = RecommendationEngine()
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "description": [None] * 2 + ["Desc"] * 8  # 20% null
        })

        quality_report = {
            "score": 85,
            "grade": "B",
            "issues": [
                {
                    "type": "high_null_percentage",
                    "column": "description",
                    "null_count": 2,
                    "null_percentage": 20.0
                }
            ]
        }

        patterns = {"primary_key": "id"}

        recommendations = engine.generate_recommendations(df, "products", quality_report, patterns)

        assert len(recommendations) == 1
        assert recommendations[0]["priority"] == Priority.MEDIUM
        assert recommendations[0]["auto_fix"] is True
        assert "Sans description" in recommendations[0]["suggested_default"]

    def test_recommend_future_dates(self) -> None:
        """Test recommendation for future dates."""
        engine = RecommendationEngine()
        future_date = datetime.now() + timedelta(days=30)

        df = pd.DataFrame({
            "id": [1, 2, 3, 4],
            "date_created": [
                datetime(2024, 1, 1),
                datetime(2024, 2, 1),
                future_date,
                datetime(2024, 3, 1)
            ]
        })

        quality_report = {
            "score": 90,
            "grade": "A",
            "issues": [
                {
                    "type": "future_dates",
                    "column": "date_created",
                    "count": 1
                }
            ]
        }

        patterns = {"primary_key": "id"}

        recommendations = engine.generate_recommendations(df, "orders", quality_report, patterns)

        assert len(recommendations) == 1
        assert recommendations[0]["priority"] == Priority.LOW
        assert "Future dates" in recommendations[0]["issue"]
        assert recommendations[0]["auto_fix"] is False
        assert "Review date entry" in recommendations[0]["action"]

    def test_recommend_invalid_values_negative(self) -> None:
        """Test recommendation for negative quantity values."""
        engine = RecommendationEngine()
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "quantity": [10, -5, 20]
        })

        quality_report = {
            "score": 85,
            "grade": "B",
            "issues": [
                {
                    "type": "negative_quantity",
                    "column": "quantity",
                    "count": 1
                }
            ]
        }

        patterns = {"primary_key": "id"}

        recommendations = engine.generate_recommendations(df, "inventory", quality_report, patterns)

        assert len(recommendations) == 1
        assert recommendations[0]["priority"] == Priority.MEDIUM
        assert "Negative values" in recommendations[0]["issue"]
        assert recommendations[0]["auto_fix"] is False
        assert ">= 0" in recommendations[0]["action"]

    def test_recommend_missing_default(self) -> None:
        """Test recommendation for missing default values."""
        engine = RecommendationEngine()
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "status": ["active", "inactive", None]
        })

        quality_report = {
            "score": 88,
            "grade": "B",
            "issues": [
                {
                    "type": "missing_default",
                    "column": "status",
                    "count": 3
                }
            ]
        }

        patterns = {"primary_key": "id"}

        recommendations = engine.generate_recommendations(df, "products", quality_report, patterns)

        assert len(recommendations) == 1
        assert recommendations[0]["priority"] == Priority.MEDIUM
        assert "Missing default" in recommendations[0]["issue"]
        assert recommendations[0]["auto_fix"] is True
        assert "suggested_default" in recommendations[0]

    def test_recommendations_priority_sorting(self) -> None:
        """Test that recommendations are sorted by priority."""
        engine = RecommendationEngine()
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "category": [None, None, None, "A", "B"],
            "quantity": [10, -5, 20, 15, 30]
        })

        future_date = datetime.now() + timedelta(days=30)
        df["date"] = [datetime(2024, 1, 1)] * 4 + [future_date]

        quality_report = {
            "score": 70,
            "grade": "C",
            "issues": [
                {
                    "type": "high_null_percentage",
                    "column": "category",
                    "null_count": 3,
                    "null_percentage": 60.0
                },
                {
                    "type": "negative_quantity",
                    "column": "quantity",
                    "count": 1
                },
                {
                    "type": "future_dates",
                    "column": "date",
                    "count": 1
                }
            ]
        }

        patterns = {"primary_key": "id"}

        recommendations = engine.generate_recommendations(df, "test", quality_report, patterns)

        assert len(recommendations) == 3
        # Should be sorted: HIGH (null) -> MEDIUM (negative) -> LOW (future)
        assert recommendations[0]["priority"] == Priority.HIGH
        assert recommendations[1]["priority"] == Priority.MEDIUM
        assert recommendations[2]["priority"] == Priority.LOW

    def test_get_recommendations_by_priority(self) -> None:
        """Test filtering recommendations by priority."""
        engine = RecommendationEngine()
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "category": [None, None, None],
            "date": [datetime(2024, 1, 1), datetime(2024, 2, 1), datetime(2024, 3, 1)]
        })

        quality_report = {
            "score": 75,
            "grade": "C",
            "issues": [
                {
                    "type": "high_null_percentage",
                    "column": "category",
                    "null_count": 3,
                    "null_percentage": 100.0
                }
            ]
        }

        patterns = {"primary_key": "id"}

        engine.generate_recommendations(df, "test", quality_report, patterns)

        high_recs = engine.get_recommendations_by_priority(Priority.HIGH)
        medium_recs = engine.get_recommendations_by_priority(Priority.MEDIUM)
        low_recs = engine.get_recommendations_by_priority(Priority.LOW)

        assert len(high_recs) == 1
        assert len(medium_recs) == 0
        assert len(low_recs) == 0

    def test_get_auto_fixable_recommendations(self) -> None:
        """Test getting auto-fixable recommendations."""
        engine = RecommendationEngine()
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "category": [None, None, None]
        })

        quality_report = {
            "score": 75,
            "grade": "C",
            "issues": [
                {
                    "type": "high_null_percentage",
                    "column": "category",
                    "null_count": 3,
                    "null_percentage": 100.0
                }
            ]
        }

        patterns = {"primary_key": "id"}

        engine.generate_recommendations(df, "products", quality_report, patterns)

        auto_fixable = engine.get_auto_fixable_recommendations()
        manual = engine.get_manual_review_recommendations()

        # Null values should be auto-fixable
        assert len(auto_fixable) == 1
        assert auto_fixable[0]["auto_fix"] is True
        assert len(manual) == 0

    def test_get_manual_review_recommendations(self) -> None:
        """Test getting manual review recommendations."""
        engine = RecommendationEngine()
        df = pd.DataFrame({
            "id": [1, 2, 2, 3],
            "name": ["A", "B", "C", "D"]
        })

        quality_report = {
            "score": 70,
            "grade": "C",
            "issues": [
                {
                    "type": "duplicate_pk",
                    "column": "id",
                    "count": 1
                }
            ]
        }

        patterns = {"primary_key": "id"}

        engine.generate_recommendations(df, "test", quality_report, patterns)

        auto_fixable = engine.get_auto_fixable_recommendations()
        manual = engine.get_manual_review_recommendations()

        # Duplicate PK should require manual review
        assert len(auto_fixable) == 0
        assert len(manual) == 1
        assert manual[0]["auto_fix"] is False

    def test_get_summary(self) -> None:
        """Test getting recommendation summary."""
        engine = RecommendationEngine()
        df = pd.DataFrame({
            "id": [1, 2, 3, 4],
            "category": [None, None, "A", "B"],
            "quantity": [10, -5, 20, 30]
        })

        quality_report = {
            "score": 70,
            "grade": "C",
            "issues": [
                {
                    "type": "high_null_percentage",
                    "column": "category",
                    "null_count": 2,
                    "null_percentage": 50.0
                },
                {
                    "type": "negative_quantity",
                    "column": "quantity",
                    "count": 1
                }
            ]
        }

        patterns = {"primary_key": "id"}

        engine.generate_recommendations(df, "test", quality_report, patterns)

        summary = engine.get_summary()

        assert summary["total"] == 2
        assert summary["high"] >= 1
        assert summary["auto_fixable"] >= 1
        assert summary["manual_review"] >= 1

    def test_suggest_default_value_numeric(self) -> None:
        """Test suggesting default value for numeric column."""
        engine = RecommendationEngine()
        series = pd.Series([1, 2, 3, 4, 5], name="price")

        default = engine._suggest_default_value(series)

        assert default == "0"

    def test_suggest_default_value_string_category(self) -> None:
        """Test suggesting default value for category column."""
        engine = RecommendationEngine()
        series = pd.Series(["A", "B", None], name="category")

        default = engine._suggest_default_value(series)

        assert default == "Non catégorisé"

    def test_suggest_default_value_string_description(self) -> None:
        """Test suggesting default value for description column."""
        engine = RecommendationEngine()
        series = pd.Series(["Desc 1", "Desc 2", None], name="description")

        default = engine._suggest_default_value(series)

        assert default == "Sans description"

    def test_suggest_default_value_datetime(self) -> None:
        """Test suggesting default value for datetime column."""
        engine = RecommendationEngine()
        series = pd.Series([
            datetime(2024, 1, 1),
            datetime(2024, 2, 1),
            datetime(2024, 3, 1)
        ], name="created_at")

        default = engine._suggest_default_value(series)

        assert default == "CURRENT_TIMESTAMP"

    def test_multiple_recommendations_same_table(self) -> None:
        """Test generating multiple recommendations for one table."""
        engine = RecommendationEngine()
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "category": [None, "A", None],
            "quantity": [10, -5, 20],
            "status": ["active", None, "inactive"]
        })

        quality_report = {
            "score": 70,
            "grade": "C",
            "issues": [
                {
                    "type": "low_null_percentage",
                    "column": "category",
                    "null_count": 2,
                    "null_percentage": 66.7
                },
                {
                    "type": "negative_quantity",
                    "column": "quantity",
                    "count": 1
                },
                {
                    "type": "missing_default",
                    "column": "status",
                    "count": 1
                }
            ]
        }

        patterns = {"primary_key": "id"}

        recommendations = engine.generate_recommendations(df, "products", quality_report, patterns)

        assert len(recommendations) == 3

        # Check that all have the correct table
        for rec in recommendations:
            assert rec["table"] == "products"

    def test_recommendation_without_primary_key(self) -> None:
        """Test recommendations when no primary key is detected."""
        engine = RecommendationEngine()
        df = pd.DataFrame({
            "name": ["A", "B", "C"],
            "value": [1, 2, 3]
        })

        quality_report = {
            "score": 100,
            "grade": "A+",
            "issues": []
        }

        patterns = {}  # No primary key

        recommendations = engine.generate_recommendations(df, "test", quality_report, patterns)

        assert len(recommendations) == 0

    def test_unknown_issue_type(self) -> None:
        """Test that unknown issue types are ignored."""
        engine = RecommendationEngine()
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "value": [1, 2, 3]
        })

        quality_report = {
            "score": 90,
            "grade": "A",
            "issues": [
                {
                    "type": "unknown_issue_type",
                    "column": "value",
                    "count": 1
                }
            ]
        }

        patterns = {"primary_key": "id"}

        recommendations = engine.generate_recommendations(df, "test", quality_report, patterns)

        # Unknown issue type should be skipped
        assert len(recommendations) == 0
