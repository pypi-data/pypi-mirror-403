"""
Integration tests for Auto-Fix Engine.

Tests AutoFixer with PatternDetector and RecommendationEngine
using real Excel fixture files.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil

from excel_to_sql.auto_pilot.detector import PatternDetector
from excel_to_sql.auto_pilot.recommender import RecommendationEngine
from excel_to_sql.auto_pilot.auto_fix import AutoFixer


class TestAutoFixIntegration:
    """Integration tests for AutoFixer."""

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

    @pytest.fixture
    def fixer(self) -> AutoFixer:
        """Get AutoFixer instance."""
        return AutoFixer()

    def test_auto_fix_workflow_with_commandes(
        self,
        detector: PatternDetector,
        recommender: RecommendationEngine,
        fixer: AutoFixer,
        fixtures_dir: Path
    ) -> None:
        """Test complete auto-fix workflow with commandes table."""
        # Load commandes Excel file
        commandes_file = fixtures_dir / "commandes.xlsx"
        df = pd.read_excel(commandes_file)

        # Detect patterns
        patterns = detector.detect_patterns(df, "commandes")

        # Create quality report
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

        # Generate recommendations
        recommendations = recommender.generate_recommendations(
            df, "commandes", quality_report, patterns
        )

        # Apply auto-fixes (dry-run)
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_file = Path(tmpdir) / "commandes.xlsx"
            shutil.copy2(commandes_file, temp_file)

            result = fixer.apply_auto_fixes(
                df, temp_file, "Sheet1", recommendations, dry_run=True
            )

            # Verify result
            assert result["dry_run"] is True
            assert "total_fixes" in result
            assert result["status"] == "success"

    def test_auto_fix_with_null_values(
        self,
        fixer: AutoFixer
    ) -> None:
        """Test auto-fix with null values."""
        # Create test DataFrame with nulls
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "category": ["A", None, None, "B", None]
        })

        recommendations = [
            {
                "type": "null_values",
                "issue_type": "null_values",
                "column": "category",
                "auto_fix": True,
                "suggested_default": "Other",
                "table": "test"
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.xlsx"
            df.to_excel(file_path, index=False)

            result = fixer.apply_auto_fixes(
                df, file_path, "Sheet1", recommendations, dry_run=True
            )

            assert result["total_fixes"] == 1
            assert result["rows_modified"] == 3

    def test_auto_fix_with_french_codes(
        self,
        fixer: AutoFixer
    ) -> None:
        """Test auto-fix with French codes."""
        df = pd.DataFrame({
            "id": [1, 2, 3, 4],
            "type": ["ENTRÉE", "SORTIE", "ACTIF", "INACTIF"]
        })

        # This would normally come from recommendations, but we test directly
        result = fixer._fix_french_codes(df, "type", dry_run=True)

        assert result is not None
        assert result["rows_affected"] == 4
        assert result["type"] == "french_codes"

    def test_backup_and_restore_workflow(
        self,
        fixer: AutoFixer
    ) -> None:
        """Test complete backup and restore workflow."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["Original A", "Original B", "Original C"]
        })

        with tempfile.TemporaryDirectory() as tmpdir:
            fixer.backup_dir = Path(tmpdir)
            file_path = Path(tmpdir) / "test.xlsx"
            df.to_excel(file_path, index=False)

            # Create backup
            backup_path = fixer._create_backup(file_path)

            # Verify backup exists
            assert backup_path.exists()
            assert backup_path.suffix == ".bak"

            # Modify original file
            df_modified = pd.DataFrame({
                "id": [4, 5, 6],
                "name": ["Modified A", "Modified B", "Modified C"]
            })
            df_modified.to_excel(file_path, index=False)

            # Restore from backup
            success = fixer.restore_backup(backup_path, file_path)

            assert success is True

            # Verify restoration
            df_restored = pd.read_excel(file_path)
            assert list(df_restored["id"]) == [1, 2, 3]
            assert list(df_restored["name"]) == ["Original A", "Original B", "Original C"]

    def test_auto_fix_summary(
        self,
        fixer: AutoFixer
    ) -> None:
        """Test getting fix summary."""
        # Simulate applied fixes
        fixer.fixes_applied = [
            {"type": "null_values", "column": "category", "rows_affected": 10},
            {"type": "french_codes", "column": "type", "rows_affected": 5}
        ]

        summary = fixer.get_fix_summary()

        assert summary["total_fixes"] == 2
        assert summary["rows_modified"] == 15
        assert summary["fixes_by_type"]["null_values"] == 1
        assert summary["fixes_by_type"]["french_codes"] == 1
        assert summary["fixes_by_column"]["category"] == 1
        assert summary["fixes_by_column"]["type"] == 1

    def test_multiple_fix_types_in_one_run(
        self,
        fixer: AutoFixer
    ) -> None:
        """Test applying multiple fix types in a single run."""
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "category": ["A", None, "B", None, None],
            "description": ["Desc1", None, "Desc3", None, None]
        })

        recommendations = [
            {
                "type": "null_values",
                "issue_type": "null_values",
                "column": "category",
                "auto_fix": True,
                "suggested_default": "Other",
                "table": "test"
            },
            {
                "type": "null_values",
                "issue_type": "null_values",
                "column": "description",
                "auto_fix": True,
                "suggested_default": "No desc",
                "table": "test"
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.xlsx"
            df.to_excel(file_path, index=False)

            result = fixer.apply_auto_fixes(
                df, file_path, "Sheet1", recommendations, dry_run=True
            )

            assert result["total_fixes"] == 2
            # Row 3 has nulls in both category and description, so it's counted twice
            assert result["rows_modified"] >= 5

    def test_get_backups_for_file(
        self,
        fixer: AutoFixer
    ) -> None:
        """Test getting backups for a specific file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fixer.backup_dir = Path(tmpdir)

            # Create test file and multiple backups
            test_file = Path(tmpdir) / "test.xlsx"
            df = pd.DataFrame({"a": [1, 2, 3]})

            df.to_excel(test_file, index=False)
            fixer._create_backup(test_file)
            fixer._create_backup(test_file)

            # Get backups
            backups = fixer.get_backups("test")

            # Should have at least 1 backup
            assert len(backups) >= 1
            # All should exist
            for backup in backups:
                assert backup.exists()

    def test_auto_fix_preserves_data_integrity(
        self,
        fixer: AutoFixer
    ) -> None:
        """Test that auto-fix preserves data integrity."""
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "value": [10, 20, 30, 40, 50],
            "name": ["A", "B", None, "D", "E"]
        })

        recommendations = [
            {
                "type": "null_values",
                "issue_type": "null_values",
                "column": "name",
                "auto_fix": True,
                "suggested_default": "Unknown",
                "table": "test"
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.xlsx"
            df.to_excel(file_path, index=False)

            result = fixer.apply_auto_fixes(
                df, file_path, "Sheet1", recommendations, dry_run=False
            )

            # Verify fix was applied
            assert result["total_fixes"] == 1

            # Read back and verify data integrity
            df_fixed = pd.read_excel(file_path)

            # Non-null values should be preserved
            assert df_fixed.loc[df_fixed["id"] == 1, "name"].values[0] == "A"
            assert df_fixed.loc[df_fixed["id"] == 2, "name"].values[0] == "B"
            assert df_fixed.loc[df_fixed["id"] == 4, "name"].values[0] == "D"
            assert df_fixed.loc[df_fixed["id"] == 5, "name"].values[0] == "E"

            # Values should be preserved
            assert list(df_fixed["value"]) == [10, 20, 30, 40, 50]

            # Null should be filled
            assert df_fixed.loc[df_fixed["id"] == 3, "name"].values[0] == "Unknown"

    def test_split_fields_combination(
        self,
        fixer: AutoFixer
    ) -> None:
        """Test combining split fields with COALESCE."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "etat_superieur": ["active", None, "pending"],
            "etat_inferieur": [None, "inactive", "pending"]
        })

        result = fixer._fix_split_fields(
            df,
            ["etat_superieur", "etat_inferieur"],
            "etat_combined",
            dry_run=True
        )

        assert result is not None
        assert result["type"] == "split_fields"
        assert result["rows_affected"] == 3
        assert set(result["source_columns"]) == {"etat_superieur", "etat_inferieur"}
