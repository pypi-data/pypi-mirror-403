"""
Integration tests for Interactive Wizard.

Tests InteractiveWizard with PatternDetector and real Excel files.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile

from excel_to_sql.ui.interactive import InteractiveWizard
from excel_to_sql.auto_pilot.detector import PatternDetector


class TestInteractiveIntegration:
    """Integration tests for InteractiveWizard."""

    @pytest.fixture
    def fixtures_dir(self) -> Path:
        """Get path to fixtures directory."""
        return Path(__file__).parent.parent / "fixtures" / "auto_pilot"

    @pytest.fixture
    def wizard(self) -> InteractiveWizard:
        """Get InteractiveWizard instance."""
        return InteractiveWizard()

    @pytest.fixture
    def detector(self) -> PatternDetector:
        """Get PatternDetector instance."""
        return PatternDetector()

    def test_integration_with_commandes(
        self,
        wizard: InteractiveWizard,
        detector: PatternDetector,
        fixtures_dir: Path
    ) -> None:
        """Test wizard with commandes table integration."""
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

        # Test _get_transformations with real patterns
        transformations = wizard._get_transformations(patterns)

        # Verify transformations are extracted
        assert isinstance(transformations, list)

        # Test _show_file_analysis with real data
        wizard._show_file_analysis(commandes_file, patterns, quality_report)

    def test_integration_with_mouvements(
        self,
        wizard: InteractiveWizard,
        detector: PatternDetector,
        fixtures_dir: Path
    ) -> None:
        """Test wizard with mouvements table integration."""
        # Load mouvements Excel file
        mouvements_file = fixtures_dir / "mouvements.xlsx"
        df = pd.read_excel(mouvements_file)

        # Detect patterns
        patterns = detector.detect_patterns(df, "mouvements")

        # Create quality report
        quality_report = {
            "score": 90,
            "grade": "A",
            "issues": []
        }

        # Test _show_file_analysis with real data
        wizard._show_file_analysis(mouvements_file, patterns, quality_report)

        # Test _get_transformations
        transformations = wizard._get_transformations(patterns)
        assert isinstance(transformations, list)

    def test_integration_with_products(
        self,
        wizard: InteractiveWizard,
        detector: PatternDetector,
        fixtures_dir: Path
    ) -> None:
        """Test wizard with produits table integration."""
        # Load produits Excel file
        produits_file = fixtures_dir / "produits.xlsx"
        df = pd.read_excel(produits_file)

        # Detect patterns
        patterns = detector.detect_patterns(df, "produits")

        # Create quality report
        quality_report = {
            "score": 95,
            "grade": "A+",
            "issues": []
        }

        # Test with real file
        wizard._show_file_analysis(produits_file, patterns, quality_report)

        # Test transformations extraction
        transformations = wizard._get_transformations(patterns)
        assert isinstance(transformations, list)

    def test_integration_value_mappings_display(
        self,
        wizard: InteractiveWizard,
        detector: PatternDetector,
        fixtures_dir: Path
    ) -> None:
        """Test displaying value mappings from real data."""
        # Load commandes file
        commandes_file = fixtures_dir / "commandes.xlsx"
        df = pd.read_excel(commandes_file)

        # Detect patterns
        patterns = detector.detect_patterns(df, "commandes")

        # Get transformations
        transformations = wizard._get_transformations(patterns)

        # Display transformations
        wizard._show_transformations(transformations)

    def test_integration_split_fields_detection(
        self,
        wizard: InteractiveWizard
    ) -> None:
        """Test split fields detection and transformation."""
        # Create test data with split fields
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "etat_superieur": ["active", None, "pending"],
            "etat_inferieur": [None, "inactive", "pending"]
        })

        patterns = {
            "split_fields": ["etat_superieur", "etat_inferieur"],
            "primary_key": "id"
        }

        # Get transformations
        transformations = wizard._get_transformations(patterns)

        # Should have one calculated column transformation
        assert len(transformations) == 1
        assert transformations[0]["type"] == "calculated_column"
        assert "COALESCE" in transformations[0]["expression"]

    def test_integration_with_quality_issues(
        self,
        wizard: InteractiveWizard,
        fixtures_dir: Path
    ) -> None:
        """Test wizard displays quality issues correctly."""
        # Load commandes file
        commandes_file = fixtures_dir / "commandes.xlsx"

        # Create quality report with issues
        quality_report = {
            "score": 65,
            "grade": "C",
            "issues": [
                {
                    "type": "high_null_percentage",
                    "column": "description",
                    "null_count": 10,
                    "null_percentage": 50.0
                },
                {
                    "type": "duplicate_pk",
                    "column": "id",
                    "duplicate_count": 2
                }
            ]
        }

        patterns = {"primary_key": "id"}

        # Test display with quality issues
        wizard._show_file_analysis(commandes_file, patterns, quality_report)

    def test_integration_sample_data_from_real_file(
        self,
        wizard: InteractiveWizard,
        fixtures_dir: Path
    ) -> None:
        """Test viewing sample data from real Excel file."""
        # Load commandes file
        commandes_file = fixtures_dir / "commandes.xlsx"

        # Mock input to avoid blocking
        import builtins
        original_input = builtins.input
        builtins.input = lambda _: ""

        try:
            # View sample data
            wizard._view_sample_data(commandes_file)
        finally:
            builtins.input = original_input

    def test_integration_statistics_from_real_file(
        self,
        wizard: InteractiveWizard,
        fixtures_dir: Path
    ) -> None:
        """Test viewing statistics from real Excel file."""
        # Load commandes file
        commandes_file = fixtures_dir / "commandes.xlsx"

        # Mock input to avoid blocking
        import builtins
        original_input = builtins.input
        builtins.input = lambda _: ""

        try:
            # View statistics
            wizard._view_statistics(commandes_file)
        finally:
            builtins.input = original_input

    def test_integration_multiple_transformation_types(
        self,
        wizard: InteractiveWizard,
        detector: PatternDetector
    ) -> None:
        """Test wizard with multiple transformation types."""
        # Create test data with both value mappings and split fields
        df = pd.DataFrame({
            "id": [1, 2, 3, 4],
            "type": ["ENTRÉE", "SORTIE", "ACTIF", "INACTIF"],
            "etat_superieur": ["active", None, "pending", None],
            "etat_inferieur": [None, "inactive", "pending", "active"]
        })

        # Detect patterns (manual for this test)
        patterns = {
            "primary_key": "id",
            "value_mappings": {
                "type": {"ENTRÉE": "inbound", "SORTIE": "outbound", "ACTIF": "active", "INACTIF": "inactive"}
            },
            "split_fields": ["etat_superieur", "etat_inferieur"]
        }

        # Get transformations
        transformations = wizard._get_transformations(patterns)

        # Should have both types
        assert len(transformations) == 2
        types = [t["type"] for t in transformations]
        assert "value_mapping" in types
        assert "calculated_column" in types

        # Display transformations
        wizard._show_transformations(transformations)

    def test_integration_empty_transformation_workflow(
        self,
        wizard: InteractiveWizard,
        detector: PatternDetector,
        fixtures_dir: Path
    ) -> None:
        """Test wizard workflow when no transformations are detected."""
        # Create simple file with no patterns
        with tempfile.TemporaryDirectory() as tmpdir:
            simple_file = Path(tmpdir) / "simple.xlsx"
            df = pd.DataFrame({
                "id": [1, 2, 3],
                "name": ["A", "B", "C"],
                "value": [10, 20, 30]
            })
            df.to_excel(simple_file, index=False)

            # Detect patterns
            patterns = detector.detect_patterns(df, "simple")

            # Get quality
            quality = {"score": 100, "grade": "A+", "issues": []}

            # Should handle empty transformations gracefully
            transformations = wizard._get_transformations(patterns)

            # Show file analysis
            wizard._show_file_analysis(simple_file, patterns, quality)
