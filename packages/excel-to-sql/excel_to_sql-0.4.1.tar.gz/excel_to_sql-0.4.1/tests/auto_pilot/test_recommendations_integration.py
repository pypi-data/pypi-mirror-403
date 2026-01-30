"""
Integration tests for Recommendations Engine.

Tests RecommendationEngine with PatternDetector and QualityScorer
using real Excel fixture files.
"""

import pytest
import pandas as pd
from pathlib import Path

from excel_to_sql.auto_pilot.detector import PatternDetector
from excel_to_sql.auto_pilot.recommender import RecommendationEngine, Priority


class TestRecommendationsIntegration:
    """Integration tests for RecommendationEngine."""

    @pytest.fixture
    def fixtures_dir(self) -> Path:
        """Get path to fixtures directory."""
        return Path(__file__).parent.parent / "fixtures" / "auto_pilot"

    @pytest.fixture
    def detector(self) -> PatternDetector:
        """Get PatternDetector instance."""
        return PatternDetector()

    @pytest.fixture
    def recommender(self) -> RecommendationEngine:
        """Get RecommendationEngine instance."""
        return RecommendationEngine()

    def test_recommendations_for_commandes_table(
        self,
        detector: PatternDetector,
        recommender: RecommendationEngine,
        fixtures_dir: Path
    ) -> None:
        """Test generating recommendations for commandes table."""
        # Load commandes Excel file
        commandes_file = fixtures_dir / "commandes.xlsx"
        df = pd.read_excel(commandes_file)

        # Detect patterns
        patterns = detector.detect_patterns(df, "commandes")

        # Generate quality report (we need QualityScorer here, but for now
        # we'll create a minimal quality report)
        quality_report = {
            "score": 85,
            "grade": "B",
            "issues": []
        }

        # Check for potential issues in the data
        if "montant" in df.columns:
            # Check for negative amounts
            negative = (df["montant"] < 0).sum()
            if negative > 0:
                quality_report["issues"].append({
                    "type": "negative_quantity",
                    "column": "montant",
                    "count": int(negative)
                })

        # Check for null values
        for col in df.columns:
            null_count = df[col].isna().sum()
            if null_count > 0:
                null_percentage = (null_count / len(df)) * 100
                if null_percentage > 10:
                    quality_report["issues"].append({
                        "type": "high_null_percentage",
                        "column": col,
                        "null_count": int(null_count),
                        "null_percentage": null_percentage
                    })

        # Generate recommendations
        recommendations = recommender.generate_recommendations(
            df, "commandes", quality_report, patterns
        )

        # Verify recommendations
        assert isinstance(recommendations, list)

        # Get summary
        summary = recommender.get_summary()
        assert summary["total"] == len(recommendations)

        # Verify structure of recommendations
        for rec in recommendations:
            assert "priority" in rec
            assert "issue" in rec
            assert "table" in rec
            assert rec["table"] == "commandes"
            assert "action" in rec
            assert "impact" in rec
            assert "auto_fix" in rec
            assert isinstance(rec["auto_fix"], bool)

    def test_recommendations_for_mouvements_table(
        self,
        detector: PatternDetector,
        recommender: RecommendationEngine,
        fixtures_dir: Path
    ) -> None:
        """Test generating recommendations for mouvements table."""
        # Load mouvements Excel file
        mouvements_file = fixtures_dir / "mouvements.xlsx"
        df = pd.read_excel(mouvements_file)

        # Detect patterns
        patterns = detector.detect_patterns(df, "mouvements")

        # Generate quality report
        quality_report = {
            "score": 90,
            "grade": "A",
            "issues": []
        }

        # Check for null values
        for col in df.columns:
            null_count = df[col].isna().sum()
            if null_count > 0:
                null_percentage = (null_count / len(df)) * 100
                if null_percentage > 5:
                    quality_report["issues"].append({
                        "type": "low_null_percentage",
                        "column": col,
                        "null_count": int(null_count),
                        "null_percentage": null_percentage
                    })

        # Check for future dates
        date_cols = [col for col in df.columns if "date" in col.lower()]
        for col in date_cols:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                future_count = (df[col] > pd.Timestamp.now()).sum()
                if future_count > 0:
                    quality_report["issues"].append({
                        "type": "future_dates",
                        "column": col,
                        "count": int(future_count)
                    })

        # Generate recommendations
        recommendations = recommender.generate_recommendations(
            df, "mouvements", quality_report, patterns
        )

        # Verify
        assert isinstance(recommendations, list)
        summary = recommender.get_summary()

        # Should have recommendations if issues were found
        if len(quality_report["issues"]) > 0:
            assert summary["total"] > 0

    def test_recommendations_for_produits_table(
        self,
        detector: PatternDetector,
        recommender: RecommendationEngine,
        fixtures_dir: Path
    ) -> None:
        """Test generating recommendations for produits table."""
        # Load produits Excel file
        produits_file = fixtures_dir / "produits.xlsx"
        df = pd.read_excel(produits_file)

        # Detect patterns
        patterns = detector.detect_patterns(df, "produits")

        # Generate quality report
        quality_report = {
            "score": 88,
            "grade": "B",
            "issues": []
        }

        # Check for null values in important columns
        if "description" in df.columns:
            null_count = df["description"].isna().sum()
            if null_count > 0:
                quality_report["issues"].append({
                    "type": "missing_default",
                    "column": "description",
                    "count": int(null_count)
                })

        # Generate recommendations
        recommendations = recommender.generate_recommendations(
            df, "produits", quality_report, patterns
        )

        # Verify
        assert isinstance(recommendations, list)

        # If recommendations exist, verify structure
        for rec in recommendations:
            assert rec["table"] == "produits"
            assert rec["priority"] in [Priority.HIGH, Priority.MEDIUM, Priority.LOW]

    def test_recommendations_priority_sorting_integration(
        self,
        detector: PatternDetector,
        recommender: RecommendationEngine,
        fixtures_dir: Path
    ) -> None:
        """Test that recommendations are sorted by priority in real data."""
        # Load commandes Excel file
        commandes_file = fixtures_dir / "commandes.xlsx"
        df = pd.read_excel(commandes_file)

        # Detect patterns
        patterns = detector.detect_patterns(df, "commandes")

        # Create quality report with mixed priorities
        quality_report = {
            "score": 70,
            "grade": "C",
            "issues": [
                {
                    "type": "low_null_percentage",
                    "column": "client",
                    "null_count": 2,
                    "null_percentage": 10.0
                },
                {
                    "type": "negative_quantity",
                    "column": "montant",
                    "count": 1
                }
            ]
        }

        # Generate recommendations
        recommendations = recommender.generate_recommendations(
            df, "commandes", quality_report, patterns
        )

        # Verify sorting (should be MEDIUM → MEDIUM → LOW if we add a LOW priority issue)
        if len(recommendations) >= 2:
            priorities = [r["priority"] for r in recommendations]
            # Check that HIGH comes before MEDIUM comes before LOW
            if Priority.HIGH in priorities and Priority.LOW in priorities:
                high_index = priorities.index(Priority.HIGH)
                low_index = priorities.index(Priority.LOW)
                assert high_index < low_index

    def test_auto_fixable_vs_manual_review(
        self,
        detector: PatternDetector,
        recommender: RecommendationEngine,
        fixtures_dir: Path
    ) -> None:
        """Test distinction between auto-fixable and manual review recommendations."""
        # Load produits Excel file
        produits_file = fixtures_dir / "produits.xlsx"
        df = pd.read_excel(produits_file)

        # Detect patterns
        patterns = detector.detect_patterns(df, "produits")

        # Create quality report with both types
        quality_report = {
            "score": 75,
            "grade": "C",
            "issues": [
                {
                    "type": "missing_default",
                    "column": "description",
                    "count": 5
                }
            ]
        }

        # Generate recommendations
        recommendations = recommender.generate_recommendations(
            df, "produits", quality_report, patterns
        )

        # Get auto-fixable and manual review
        auto_fixable = recommender.get_auto_fixable_recommendations()
        manual_review = recommender.get_manual_review_recommendations()

        # Verify
        assert isinstance(auto_fixable, list)
        assert isinstance(manual_review, list)

        # Auto-fixable should have auto_fix=True
        for rec in auto_fixable:
            assert rec["auto_fix"] is True

        # Manual review should have auto_fix=False
        for rec in manual_review:
            assert rec["auto_fix"] is False

    def test_recommendations_summary_statistics(
        self,
        detector: PatternDetector,
        recommender: RecommendationEngine,
        fixtures_dir: Path
    ) -> None:
        """Test summary statistics for recommendations."""
        # Load produits Excel file
        produits_file = fixtures_dir / "produits.xlsx"
        df = pd.read_excel(produits_file)

        # Detect patterns
        patterns = detector.detect_patterns(df, "produits")

        # Create quality report
        quality_report = {
            "score": 80,
            "grade": "B",
            "issues": [
                {
                    "type": "low_null_percentage",
                    "column": "description",
                    "null_count": 3,
                    "null_percentage": 30.0
                }
            ]
        }

        # Generate recommendations
        recommender.generate_recommendations(df, "produits", quality_report, patterns)

        # Get summary
        summary = recommender.get_summary()

        # Verify summary structure
        assert "total" in summary
        assert "high" in summary
        assert "medium" in summary
        assert "low" in summary
        assert "auto_fixable" in summary
        assert "manual_review" in summary

        # Verify counts match
        assert summary["total"] == summary["high"] + summary["medium"] + summary["low"]
        assert summary["total"] == summary["auto_fixable"] + summary["manual_review"]

    def test_empty_recommendations_for_clean_data(
        self,
        detector: PatternDetector,
        recommender: RecommendationEngine,
        fixtures_dir: Path
    ) -> None:
        """Test that clean data generates no recommendations."""
        # Create a clean DataFrame
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "name": ["Product A", "Product B", "Product C", "Product D", "Product E"],
            "price": [10.0, 20.0, 30.0, 40.0, 50.0],
            "active": [True, True, True, True, True]
        })

        # Detect patterns
        patterns = detector.detect_patterns(df, "clean_table")

        # Perfect quality report
        quality_report = {
            "score": 100,
            "grade": "A+",
            "issues": []
        }

        # Generate recommendations
        recommendations = recommender.generate_recommendations(
            df, "clean_table", quality_report, patterns
        )

        # Should have no recommendations
        assert len(recommendations) == 0

        # Summary should reflect this
        summary = recommender.get_summary()
        assert summary["total"] == 0

    def test_multiple_tables_integration(
        self,
        detector: PatternDetector,
        recommender: RecommendationEngine,
        fixtures_dir: Path
    ) -> None:
        """Test recommendations across multiple tables."""
        all_recommendations = []

        # Process all three fixture files
        for table_name in ["commandes", "mouvements", "produits"]:
            file_path = fixtures_dir / f"{table_name}.xlsx"
            df = pd.read_excel(file_path)

            patterns = detector.detect_patterns(df, table_name)

            quality_report = {
                "score": 85,
                "grade": "B",
                "issues": []
            }

            # Check for null values
            for col in df.columns:
                null_count = df[col].isna().sum()
                if null_count > 0:
                    null_percentage = (null_count / len(df)) * 100
                    quality_report["issues"].append({
                        "type": "high_null_percentage" if null_percentage > 10 else "low_null_percentage",
                        "column": col,
                        "null_count": int(null_count),
                        "null_percentage": null_percentage
                    })

            recommendations = recommender.generate_recommendations(
                df, table_name, quality_report, patterns
            )

            all_recommendations.extend(recommendations)

        # Verify we got recommendations for all tables
        tables_represented = set(r["table"] for r in all_recommendations)

        # Should have recommendations for at least one table
        assert len(tables_represented) >= 1

        # All recommendations should have valid structure
        for rec in all_recommendations:
            assert rec["table"] in ["commandes", "mouvements", "produits"]
            assert rec["priority"] in [Priority.HIGH, Priority.MEDIUM, Priority.LOW]
