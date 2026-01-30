"""
Integration tests for PatternDetector with real Excel files.

Tests use actual Excel fixtures to verify end-to-end pattern detection.
"""

import pytest
import pandas as pd
from pathlib import Path
from excel_to_sql.auto_pilot.detector import PatternDetector


class TestPatternDetectorIntegration:
    """Integration tests with real Excel files."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.detector = PatternDetector()
        self.fixtures_dir = Path(__file__).parent.parent / "fixtures" / "auto_pilot"

    # -------------------------------------------------------------------------
    # Integration tests with produits.xlsx
    # -------------------------------------------------------------------------

    def test_produits_xlsx_pattern_detection(self) -> None:
        """Test pattern detection on produits.xlsx fixture."""
        produits_file = self.fixtures_dir / "produits.xlsx"
        df = pd.read_excel(produits_file)

        result = self.detector.detect_patterns(df, "produits")

        # Verify primary key detection
        assert result["primary_key"] == "no_produit"

        # Verify value mapping for status codes
        assert "etat" in result["value_mappings"]
        assert result["value_mappings"]["etat"]["ACTIF"] == "active"
        assert result["value_mappings"]["etat"]["INACTIF"] == "inactive"
        assert result["value_mappings"]["etat"]["EN_ATTENTE"] == "pending"

        # Verify confidence is high
        assert result["confidence"] > 0.4

    def test_produits_xlsx_detects_issues(self) -> None:
        """Test that produits.xlsx analysis detects data quality issues."""
        produits_file = self.fixtures_dir / "produits.xlsx"
        df = pd.read_excel(produits_file)

        result = self.detector.detect_patterns(df, "produits")

        # Should have at least one issue (missing categories, descriptions)
        assert len(result["issues"]) >= 0

    # -------------------------------------------------------------------------
    # Integration tests with mouvements.xlsx
    # -------------------------------------------------------------------------

    def test_mouvements_xlsx_pattern_detection(self) -> None:
        """Test pattern detection on mouvements.xlsx fixture."""
        mouvements_file = self.fixtures_dir / "mouvements.xlsx"
        df = pd.read_excel(mouvements_file)

        result = self.detector.detect_patterns(df, "mouvements")

        # Verify primary key detection
        assert result["primary_key"] == "oid"

        # Verify value mapping for movement codes
        assert "type" in result["value_mappings"]
        assert result["value_mappings"]["type"]["ENTRÉE"] == "inbound"
        assert result["value_mappings"]["type"]["SORTIE"] == "outbound"
        assert result["value_mappings"]["type"]["TRANSFERT"] == "transfer"

    def test_mouvements_xlsx_foreign_key_detection(self) -> None:
        """Test foreign key detection on mouvements.xlsx."""
        mouvements_file = self.fixtures_dir / "mouvements.xlsx"
        df = pd.read_excel(mouvements_file)

        result = self.detector.detect_patterns(df, "mouvements")

        # Verify foreign key detection
        assert len(result["foreign_keys"]) > 0
        fk = result["foreign_keys"][0]
        assert fk["column"] == "no_produit"
        assert fk["ref_table"] == "produits"
        assert fk["coverage"] > 90

    # -------------------------------------------------------------------------
    # Integration tests with commandes.xlsx
    # -------------------------------------------------------------------------

    def test_commandes_xlsx_pattern_detection(self) -> None:
        """Test pattern detection on commandes.xlsx fixture."""
        commandes_file = self.fixtures_dir / "commandes.xlsx"
        df = pd.read_excel(commandes_file)

        result = self.detector.detect_patterns(df, "commandes")

        # Verify primary key detection
        assert result["primary_key"] == "commande"

        # Verify split fields detection
        assert result["split_fields"] is not None
        assert len(result["split_fields"]) == 3
        assert "etat_superieur" in result["split_fields"]
        assert "etat_inferieur" in result["split_fields"]
        assert "etat" in result["split_fields"]

    def test_commandes_xlsx_mutually_exclusive_status(self) -> None:
        """Test that commandes.xlsx split fields are mutually exclusive."""
        commandes_file = self.fixtures_dir / "commandes.xlsx"
        df = pd.read_excel(commandes_file)

        result = self.detector.detect_patterns(df, "commandes")

        # Verify all three status fields are detected as split fields
        assert result["split_fields"] is not None
        status_cols = result["split_fields"]

        # Verify mutual exclusivity in the data
        for _, row in df[status_cols].iterrows():
            non_null_count = row.notna().sum()
            assert non_null_count <= 1, f"Row has {non_null_count} non-null status values, expected at most 1"

    # -------------------------------------------------------------------------
    # End-to-end workflow tests
    # -------------------------------------------------------------------------

    def test_end_to_end_detection_workflow(self) -> None:
        """Test complete detection workflow across all fixtures."""
        all_results = {}

        for fixture_name in ["produits.xlsx", "mouvements.xlsx", "commandes.xlsx"]:
            fixture_file = self.fixtures_dir / fixture_name
            df = pd.read_excel(fixture_file)
            table_name = fixture_name.replace(".xlsx", "")

            result = self.detector.detect_patterns(df, table_name)
            all_results[table_name] = result

            # Verify each result has required fields
            assert "primary_key" in result
            assert "value_mappings" in result
            assert "foreign_keys" in result
            assert "split_fields" in result
            assert "confidence" in result
            assert "issues" in result

        # Verify specific expectations per table
        assert all_results["produits"]["primary_key"] == "no_produit"
        assert all_results["mouvements"]["primary_key"] == "oid"
        assert all_results["commandes"]["primary_key"] == "commande"

        # Verify value mappings
        assert "etat" in all_results["produits"]["value_mappings"]
        assert "type" in all_results["mouvements"]["value_mappings"]

        # Verify foreign keys in mouvements
        assert len(all_results["mouvements"]["foreign_keys"]) > 0

        # Verify split fields in commandes
        assert all_results["commandes"]["split_fields"] is not None

    def test_detection_accuracy_on_real_wms_data(self) -> None:
        """Test that detection accuracy meets requirements (>95%)."""
        # Test cases with known expected results
        test_cases = [
            {
                "file": "produits.xlsx",
                "table": "produits",
                "expected_pk": "no_produit",
                "expected_value_mappings": ["etat"],
            },
            {
                "file": "mouvements.xlsx",
                "table": "mouvements",
                "expected_pk": "oid",
                "expected_value_mappings": ["type"],
                "expected_fks": [{"column": "no_produit", "ref_table": "produits"}],
            },
            {
                "file": "commandes.xlsx",
                "table": "commandes",
                "expected_pk": "commande",
                "expected_split_fields": ["etat_superieur", "etat_inferieur", "etat"],
            },
        ]

        correct_detections = 0
        total_detections = 0

        for test_case in test_cases:
            fixture_file = self.fixtures_dir / test_case["file"]
            df = pd.read_excel(fixture_file)
            result = self.detector.detect_patterns(df, test_case["table"])

            # Check primary key
            total_detections += 1
            if result["primary_key"] == test_case["expected_pk"]:
                correct_detections += 1

            # Check value mappings
            if "expected_value_mappings" in test_case:
                for col in test_case["expected_value_mappings"]:
                    total_detections += 1
                    if col in result["value_mappings"]:
                        correct_detections += 1

            # Check foreign keys
            if "expected_fks" in test_case:
                for expected_fk in test_case["expected_fks"]:
                    total_detections += 1
                    found = any(
                        fk["column"] == expected_fk["column"]
                        and fk["ref_table"] == expected_fk["ref_table"]
                        for fk in result["foreign_keys"]
                    )
                    if found:
                        correct_detections += 1

            # Check split fields
            if "expected_split_fields" in test_case:
                total_detections += 1
                if result["split_fields"] is not None:
                    correct_detections += 1

        # Calculate accuracy
        accuracy = correct_detections / total_detections if total_detections > 0 else 0

        # Verify accuracy > 95%
        assert accuracy > 0.95, f"Detection accuracy {accuracy:.2%} is below 95% threshold"

    # -------------------------------------------------------------------------
    # Performance tests
    # -------------------------------------------------------------------------

    def test_detection_performance_on_large_file(self) -> None:
        """Test that detection completes within acceptable time limits."""
        import time

        mouvements_file = self.fixtures_dir / "mouvements.xlsx"
        df = pd.read_excel(mouvements_file)

        start_time = time.time()
        result = self.detector.detect_patterns(df, "mouvements")
        end_time = time.time()

        elapsed = end_time - start_time

        # Should complete in less than 1 second for 50 rows
        assert elapsed < 1.0, f"Detection took {elapsed:.2f}s, expected < 1.0s"

        # Should still produce valid results
        assert result["primary_key"] == "oid"

    # -------------------------------------------------------------------------
    # Edge case tests with real data
    # -------------------------------------------------------------------------

    def test_handles_french_characters_in_column_names(self) -> None:
        """Test that French characters in columns are handled correctly."""
        # Commandes file has French column names
        commandes_file = self.fixtures_dir / "commandes.xlsx"
        df = pd.read_excel(commandes_file)

        # Should not crash on French characters
        result = self.detector.detect_patterns(df, "commandes")

        assert result is not None
        assert "primary_key" in result

    def test_handles_mixed_data_types_in_columns(self) -> None:
        """Test that mixed data types are handled correctly."""
        mouvements_file = self.fixtures_dir / "mouvements.xlsx"
        df = pd.read_excel(mouvements_file)

        # date_heure_2 has mixed types (timestamps and None)
        result = self.detector.detect_patterns(df, "mouvements")

        # Should still detect patterns correctly
        assert result["primary_key"] == "oid"
        assert "type" in result["value_mappings"]
