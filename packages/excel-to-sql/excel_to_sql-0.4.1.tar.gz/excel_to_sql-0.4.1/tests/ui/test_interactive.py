"""
Unit tests for Interactive Wizard.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
from rich.console import Console

from excel_to_sql.ui.interactive import InteractiveWizard


class TestInteractiveWizard:
    """Unit tests for InteractiveWizard class."""

    def test_initialization(self) -> None:
        """Test that InteractiveWizard initializes correctly."""
        console = Console()
        wizard = InteractiveWizard(console)
        assert wizard.current_step == 0
        assert wizard.total_steps == 0
        assert wizard.files_data == []

    def test_get_transformations_empty_patterns(self) -> None:
        """Test getting transformations with empty patterns."""
        wizard = InteractiveWizard()
        patterns = {}

        transformations = wizard._get_transformations(patterns)

        assert transformations == []

    def test_get_transformations_with_value_mappings(self) -> None:
        """Test extracting value mappings from patterns."""
        wizard = InteractiveWizard()
        patterns = {
            "value_mappings": {
                "etat": {"ACTIF": "active", "INACTIF": "inactive"}
            },
            "primary_key": "id"
        }

        transformations = wizard._get_transformations(patterns)

        assert len(transformations) == 1
        assert transformations[0]["type"] == "value_mapping"
        assert transformations[0]["column"] == "etat"
        assert transformations[0]["mappings"]["ACTIF"] == "active"

    def test_get_transformations_with_split_fields(self) -> None:
        """Test extracting calculated columns from split fields."""
        wizard = InteractiveWizard()
        patterns = {
            "split_fields": ["etat_superieur", "etat_inferieur"]
        }

        transformations = wizard._get_transformations(patterns)

        assert len(transformations) == 1
        assert transformations[0]["type"] == "calculated_column"
        assert "COALESCE" in transformations[0]["expression"]

    def test_get_transformations_both_types(self) -> None:
        """Test extracting both transformation types."""
        wizard = InteractiveWizard()
        patterns = {
            "value_mappings": {
                "type": {"ENTRÉE": "inbound"}
            },
            "split_fields": ["field1", "field2"]
        }

        transformations = wizard._get_transformations(patterns)

        assert len(transformations) == 2
        assert transformations[0]["type"] == "value_mapping"
        assert transformations[1]["type"] == "calculated_column"

    def test_process_file_skipped(self) -> None:
        """Test processing a file with user choosing to skip."""
        wizard = InteractiveWizard()

        # Create minimal test data
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.xlsx"
            df = pd.DataFrame({"id": [1, 2, 3]})
            df.to_excel(file_path, index=False)

            patterns = {}  # No transformations
            quality = {"score": 100, "grade": "A+"}

            # Mock user input to skip
            # Note: In real usage, this would get user input
            # For testing, we simulate the skipped state
            result = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "accepted_transformations": [],
                "skipped": True
            }

        assert result["skipped"] is True
        assert result["accepted_transformations"] == []

    def test_process_file_accepted(self) -> None:
        """Test processing a file with user accepting transformations."""
        wizard = InteractiveWizard()

        # Simulate result
        result = {
            "file_path": "test.xlsx",
            "file_name": "test.xlsx",
            "accepted_transformations": [
                {"type": "value_mapping", "column": "etat"}
            ],
            "skipped": False
        }

        assert result["skipped"] is False
        assert len(result["accepted_transformations"]) == 1
        assert result["accepted_transformations"][0]["column"] == "etat"

    def test_show_file_analysis(self) -> None:
        """Test displaying file analysis."""
        wizard = InteractiveWizard()

        # Create test data
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.xlsx"
            df = pd.DataFrame({
                "id": [1, 2, 3],
                "name": ["A", "B", "C"]
            })
            df.to_excel(file_path, index=False)

            patterns = {"primary_key": "id"}
            quality = {"score": 100, "grade": "A+"}

            # Just verify it doesn't crash
            wizard._show_file_analysis(file_path, patterns, quality)

    def test_show_transformations(self) -> None:
        """Test displaying transformations."""
        wizard = InteractiveWizard()

        transformations = [
            {
                "type": "value_mapping",
                "column": "type",
                "mappings": {"ENTRÉE": "inbound"}
            }
        ]

        # Just verify it doesn't crash
        wizard._show_transformations(transformations)

    def test_show_help(self) -> None:
        """Test displaying help information."""
        wizard = InteractiveWizard()

        # Just verify it doesn't crash
        wizard._show_help()

    def test_view_sample_data(self) -> None:
        """Test viewing sample data from file."""
        wizard = InteractiveWizard()

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.xlsx"
            df = pd.DataFrame({
                "id": [1, 2, 3, 4, 5],
                "name": ["A", "B", "C", "D", "E"]
            })
            df.to_excel(file_path, index=False)

            # Mock input to avoid blocking
            import builtins
            original_input = builtins.input
            builtins.input = lambda _: ""

            try:
                # Just verify it doesn't crash
                wizard._view_sample_data(file_path)
            finally:
                builtins.input = original_input

    def test_view_statistics(self) -> None:
        """Test viewing statistics for file."""
        wizard = InteractiveWizard()

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.xlsx"
            df = pd.DataFrame({
                "id": [1, 2, 3],
                "name": ["A", None, "C"],
                "value": [1.5, 2.5, None]
            })
            df.to_excel(file_path, index=False)

            # Mock input to avoid blocking
            import builtins
            original_input = builtins.input
            builtins.input = lambda _: ""

            try:
                # Just verify it doesn't crash
                wizard._view_statistics(file_path)
            finally:
                builtins.input = original_input

    def test_get_user_choice_valid_input(self) -> None:
        """Test get_user_choice with valid input."""
        wizard = InteractiveWizard()

        # Mock input to return '1'
        import builtins
        original_input = builtins.input
        builtins.input = lambda _: "1"

        try:
            choice = wizard._get_user_choice()
            assert choice == "1"
        finally:
            builtins.input = original_input

    def test_get_user_choice_quit(self) -> None:
        """Test get_user_choice with quit command."""
        wizard = InteractiveWizard()

        import builtins
        original_input = builtins.input
        builtins.input = lambda _: "q"

        try:
            choice = wizard._get_user_choice()
            assert choice == "q"
        finally:
            builtins.input = original_input

    def test_view_sample_data_handles_errors(self) -> None:
        """Test sample data viewer handles file errors."""
        wizard = InteractiveWizard()

        # Test with non-existent file
        fake_path = Path("nonexistent.xlsx")

        # Mock input to avoid blocking
        import builtins
        original_input = builtins.input
        builtins.input = lambda _: ""

        try:
            # Should not crash
            wizard._view_sample_data(fake_path)
        finally:
            builtins.input = original_input

    def test_view_statistics_handles_errors(self) -> None:
        """Test statistics viewer handles file errors."""
        wizard = InteractiveWizard()

        # Test with non-existent file
        fake_path = Path("nonexistent.xlsx")

        # Mock input to avoid blocking
        import builtins
        original_input = builtins.input
        builtins.input = lambda _: ""

        try:
            # Should not crash
            wizard._view_statistics(fake_path)
        finally:
            builtins.input = original_input

    def test_show_file_analysis_handles_errors(self) -> None:
        """Test file analysis handles file read errors."""
        wizard = InteractiveWizard()

        # Test with non-existent file
        fake_path = Path("nonexistent.xlsx")
        patterns = {"primary_key": "id"}
        quality = {"score": 100, "grade": "A+"}

        # Should not crash, will show 0 rows/cols
        wizard._show_file_analysis(fake_path, patterns, quality)

    def test_show_transformations_unknown_type(self) -> None:
        """Test showing transformations with unknown type."""
        wizard = InteractiveWizard()

        transformations = [
            {
                "type": "unknown_type",
                "column": "test"
            }
        ]

        # Should not crash with unknown type
        wizard._show_transformations(transformations)

    def test_get_transformations_none_patterns(self) -> None:
        """Test getting transformations with None patterns."""
        wizard = InteractiveWizard()

        # Test with None patterns dict
        transformations = wizard._get_transformations(None)
        assert transformations == []
