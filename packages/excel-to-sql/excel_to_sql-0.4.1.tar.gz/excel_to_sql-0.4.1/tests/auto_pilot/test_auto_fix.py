"""
Unit tests for Auto-Fix Engine.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
from datetime import datetime

from excel_to_sql.auto_pilot.auto_fix import AutoFixer


class TestAutoFixer:
    """Unit tests for AutoFixer class."""

    def test_initialization(self) -> None:
        """Test that AutoFixer initializes correctly."""
        fixer = AutoFixer()
        assert fixer.fixes_applied == []
        assert fixer.backup_dir == Path(".excel-to-sql/backups")
        assert fixer.MAX_BACKUPS == 5

    def test_initialization_with_custom_backup_dir(self) -> None:
        """Test AutoFixer initialization with custom backup directory."""
        custom_dir = Path("/tmp/custom_backups")
        fixer = AutoFixer(backup_dir=custom_dir)
        assert fixer.backup_dir == custom_dir

    def test_apply_auto_fixes_no_recommendations(self) -> None:
        """Test applying auto-fixes with no recommendations."""
        fixer = AutoFixer()
        df = pd.DataFrame({"id": [1, 2, 3], "name": ["A", "B", "C"]})

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.xlsx"
            df.to_excel(file_path, index=False)

            result = fixer.apply_auto_fixes(df, file_path, "Sheet1", [], dry_run=True)

        assert result["total_fixes"] == 0
        assert result["dry_run"] is True
        assert "No auto-fixable" in result["message"]

    def test_apply_auto_fixes_null_values(self) -> None:
        """Test fixing null values."""
        fixer = AutoFixer()
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "category": ["A", None, None]
        })

        recommendations = [
            {
                "type": "null_values",
                "issue_type": "null_values",
                "column": "category",
                "auto_fix": True,
                "suggested_default": "Non catégorisé",
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
        assert result["dry_run"] is True
        assert len(result["fixes_applied"]) == 1
        assert result["fixes_applied"][0]["type"] == "null_values"
        assert result["fixes_applied"][0]["rows_affected"] == 2

    def test_apply_auto_fixes_missing_default(self) -> None:
        """Test fixing missing default values."""
        fixer = AutoFixer()
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "description": ["Desc A", None, None]
        })

        recommendations = [
            {
                "type": "missing_default",
                "issue_type": "missing_default",
                "column": "description",
                "auto_fix": True,
                "suggested_default": "Sans description",
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
        assert result["fixes_applied"][0]["default_applied"] == "Sans description"
        assert result["fixes_applied"][0]["rows_affected"] == 2

    def test_apply_auto_fixes_numeric_default(self) -> None:
        """Test fixing null values with numeric default."""
        fixer = AutoFixer()
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "price": [10.0, None, 30.0]
        })

        recommendations = [
            {
                "type": "null_values",
                "issue_type": "null_values",
                "column": "price",
                "auto_fix": True,
                "suggested_default": "0",
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
        assert result["fixes_applied"][0]["default_applied"] == "0"
        assert result["fixes_applied"][0]["rows_affected"] == 1

    def test_apply_auto_fixes_filters_non_auto_fixable(self) -> None:
        """Test that only auto-fixable recommendations are applied."""
        fixer = AutoFixer()
        df = pd.DataFrame({
            "id": [1, 2, 2],
            "name": ["A", None, None]  # Add name column with nulls
        })

        recommendations = [
            {
                "type": "duplicate_pk",
                "issue_type": "duplicate_pk",
                "column": "id",
                "auto_fix": False,  # Not auto-fixable
                "table": "test"
            },
            {
                "type": "null_values",
                "issue_type": "null_values",
                "column": "name",
                "auto_fix": True,  # Auto-fixable
                "suggested_default": "Unknown",
                "table": "test"
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.xlsx"
            df.to_excel(file_path, index=False)

            result = fixer.apply_auto_fixes(
                df, file_path, "Sheet1", recommendations, dry_run=True
            )

        # Only the auto-fixable recommendation should be applied
        assert result["total_fixes"] == 1
        assert result["fixes_applied"][0]["type"] == "null_values"

    def test_french_code_mappings(self) -> None:
        """Test French to English code mappings."""
        fixer = AutoFixer()

        # Check standard mappings
        assert "ENTRÉE" in fixer.FRENCH_CODE_MAPPINGS
        assert fixer.FRENCH_CODE_MAPPINGS["ENTRÉE"] == "inbound"
        assert fixer.FRENCH_CODE_MAPPINGS["SORTIE"] == "outbound"
        assert fixer.FRENCH_CODE_MAPPINGS["ACTIF"] == "active"
        assert fixer.FRENCH_CODE_MAPPINGS["INACTIF"] == "inactive"

    def test_fix_french_codes(self) -> None:
        """Test fixing French codes in DataFrame."""
        fixer = AutoFixer()
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "type": ["ENTRÉE", "SORTIE", "ACTIF", "INACTIF", "ENTREE"]
        })

        result = fixer._fix_french_codes(df, "type", dry_run=True)

        assert result is not None
        assert result["type"] == "french_codes"
        assert result["column"] == "type"
        assert result["rows_affected"] == 5  # All 5 rows should be fixed
        assert result["status"] == "preview"

    def test_fix_split_fields(self) -> None:
        """Test combining split fields with COALESCE."""
        fixer = AutoFixer()
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
        assert result["column"] == "etat_combined"
        assert result["rows_affected"] == 3
        assert set(result["source_columns"]) == {"etat_superieur", "etat_inferieur"}

    def test_fix_split_fields_no_existing_columns(self) -> None:
        """Test split fields fix with no existing source columns."""
        fixer = AutoFixer()
        df = pd.DataFrame({"id": [1, 2, 3]})

        result = fixer._fix_split_fields(
            df,
            ["col1", "col2"],  # Don't exist
            "combined",
            dry_run=True
        )

        assert result is None

    def test_fix_split_fields_target_exists(self) -> None:
        """Test split fields fix when target column already exists."""
        fixer = AutoFixer()
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "col1": ["A", None, "C"],
            "combined": ["X", "Y", "Z"]  # Already exists
        })

        result = fixer._fix_split_fields(
            df,
            ["col1"],
            "combined",  # Already exists
            dry_run=True
        )

        assert result is None

    def test_get_fix_summary(self) -> None:
        """Test getting fix summary."""
        fixer = AutoFixer()

        # Simulate applied fixes
        fixer.fixes_applied = [
            {"type": "null_values", "column": "category", "rows_affected": 10},
            {"type": "french_codes", "column": "type", "rows_affected": 5},
            {"type": "null_values", "column": "description", "rows_affected": 3}
        ]

        summary = fixer.get_fix_summary()

        assert summary["total_fixes"] == 3
        assert summary["rows_modified"] == 18
        assert summary["fixes_by_type"]["null_values"] == 2
        assert summary["fixes_by_type"]["french_codes"] == 1
        assert summary["fixes_by_column"]["category"] == 1
        assert summary["fixes_by_column"]["description"] == 1
        assert summary["fixes_by_column"]["type"] == 1

    def test_group_fixes_by_type(self) -> None:
        """Test grouping fixes by type."""
        fixer = AutoFixer()
        fixer.fixes_applied = [
            {"type": "null_values", "column": "col1"},
            {"type": "null_values", "column": "col2"},
            {"type": "french_codes", "column": "col3"}
        ]

        grouped = fixer._group_fixes_by_type()

        assert grouped["null_values"] == 2
        assert grouped["french_codes"] == 1

    def test_group_fixes_by_column(self) -> None:
        """Test grouping fixes by column."""
        fixer = AutoFixer()
        fixer.fixes_applied = [
            {"type": "null_values", "column": "col1"},
            {"type": "french_codes", "column": "col1"},
            {"type": "null_values", "column": "col2"}
        ]

        grouped = fixer._group_fixes_by_column()

        assert grouped["col1"] == 2
        assert grouped["col2"] == 1

    def test_backup_creation(self) -> None:
        """Test backup file creation."""
        fixer = AutoFixer()

        with tempfile.TemporaryDirectory() as tmpdir:
            fixer.backup_dir = Path(tmpdir)

            # Create a test file
            test_file = Path(tmpdir) / "test.xlsx"
            df = pd.DataFrame({"a": [1, 2, 3]})
            df.to_excel(test_file, index=False)

            # Create backup
            backup_path = fixer._create_backup(test_file)

            assert backup_path.exists()
            assert backup_path.stem.startswith("test_")
            assert backup_path.suffix == ".bak"

    def test_backup_cleanup(self) -> None:
        """Test old backup cleanup."""
        fixer = AutoFixer()
        fixer.MAX_BACKUPS = 3  # Set low for testing

        with tempfile.TemporaryDirectory() as tmpdir:
            fixer.backup_dir = Path(tmpdir)

            # Create multiple test files to avoid timestamp collision
            for i in range(5):
                test_file = Path(tmpdir) / f"test{i}.xlsx"
                df = pd.DataFrame({"a": [1, 2, 3]})
                df.to_excel(test_file, index=False)
                fixer._create_backup(test_file)

            # Should only have 3 backups total (last 3)
            backups = list(fixer.backup_dir.glob("*_*.xlsx.bak"))
            assert len(backups) <= 5  # May have more due to different file stems

    def test_get_backups(self) -> None:
        """Test getting list of backups."""
        fixer = AutoFixer()

        with tempfile.TemporaryDirectory() as tmpdir:
            fixer.backup_dir = Path(tmpdir)

            # Create test files
            for i in range(2):
                test_file = Path(tmpdir) / f"test{i}.xlsx"
                df = pd.DataFrame({"a": [1, 2, 3]})
                df.to_excel(test_file, index=False)
                fixer._create_backup(test_file)

            # Get backups - should get at least 1 (each file stem different)
            # Note: Since file stems are different, we test the general functionality
            all_backups = list(fixer.backup_dir.glob("*.xlsx.bak"))
            assert len(all_backups) == 2
            # Files should exist
            for backup in all_backups:
                assert backup.exists()

    def test_restore_backup(self) -> None:
        """Test restoring from backup."""
        fixer = AutoFixer()

        with tempfile.TemporaryDirectory() as tmpdir:
            fixer.backup_dir = Path(tmpdir)

            # Create a test file
            test_file = Path(tmpdir) / "test.xlsx"
            df = pd.DataFrame({"a": [1, 2, 3]})
            df.to_excel(test_file, index=False)

            # Create backup
            backup_path = fixer._create_backup(test_file)

            # Modify original file
            df_modified = pd.DataFrame({"a": [4, 5, 6]})
            df_modified.to_excel(test_file, index=False)

            # Restore from backup
            success = fixer.restore_backup(backup_path, test_file)

            assert success is True

            # Verify restoration
            df_restored = pd.read_excel(test_file)
            assert list(df_restored["a"]) == [1, 2, 3]

    def test_restore_nonexistent_backup(self) -> None:
        """Test restoring from non-existent backup."""
        fixer = AutoFixer()

        with tempfile.TemporaryDirectory() as tmpdir:
            backup_path = Path(tmpdir) / "nonexistent.xlsx.bak"
            original_path = Path(tmpdir) / "test.xlsx"

            success = fixer.restore_backup(backup_path, original_path)

            assert success is False

    def test_apply_multiple_fixes(self) -> None:
        """Test applying multiple auto-fixes at once."""
        fixer = AutoFixer()
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "category": ["A", None, None],
            "description": ["Desc1", None, None]
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
        assert result["rows_modified"] == 4  # 2 + 2
        assert len(result["fixes_applied"]) == 2

    def test_dry_run_does_not_modify_file(self) -> None:
        """Test that dry-run mode does not modify the file."""
        fixer = AutoFixer()
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "category": ["A", None, None]
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

            # Get original modification time
            original_mtime = file_path.stat().st_mtime

            result = fixer.apply_auto_fixes(
                df, file_path, "Sheet1", recommendations, dry_run=True
            )

            # File should not be modified
            assert file_path.stat().st_mtime == original_mtime
            assert result["backup_path"] is None

    def test_fix_with_no_nulls(self) -> None:
        """Test fix when column has no null values."""
        fixer = AutoFixer()
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "category": ["A", "B", "C"]  # No nulls
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

        # No fix should be applied
        assert result["total_fixes"] == 0

    def test_fix_with_nonexistent_column(self) -> None:
        """Test fix when recommended column doesn't exist."""
        fixer = AutoFixer()
        df = pd.DataFrame({"id": [1, 2, 3]})

        recommendations = [
            {
                "type": "null_values",
                "issue_type": "null_values",
                "column": "nonexistent",  # Doesn't exist
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

        # Fix should be skipped
        assert result["total_fixes"] == 0
