"""
Unit tests for PatternDetector class.

Tests cover all detection methods with various edge cases and scenarios.
"""

import pytest
import pandas as pd
from excel_to_sql.auto_pilot.detector import PatternDetector


class TestPatternDetector:
    """Test suite for PatternDetector class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.detector = PatternDetector()

    # -------------------------------------------------------------------------
    # Tests for detect_patterns (main orchestration method)
    # -------------------------------------------------------------------------

    def test_detect_patterns_with_primary_key(self) -> None:
        """Test pattern detection with a clear primary key."""
        df = pd.DataFrame({
            "no_produit": [1, 2, 3, 4, 5],
            "nom": ["A", "B", "C", "D", "E"],
            "prix": [10.0, 20.0, 30.0, 40.0, 50.0],
        })

        result = self.detector.detect_patterns(df, "produits")

        assert result["table_name"] == "produits"
        assert result["primary_key"] == "no_produit"
        assert result["confidence"] > 0
        assert isinstance(result["value_mappings"], dict)
        assert isinstance(result["foreign_keys"], list)

    def test_detect_patterns_with_french_codes(self) -> None:
        """Test pattern detection with French status codes."""
        df = pd.DataFrame({
            "no_produit": [1, 2, 3],
            "nom": ["A", "B", "C"],
            "etat": ["ACTIF", "INACTIF", "EN_ATTENTE"],
        })

        result = self.detector.detect_patterns(df, "produits")

        assert result["primary_key"] == "no_produit"
        assert "etat" in result["value_mappings"]
        assert result["value_mappings"]["etat"]["ACTIF"] == "active"
        assert result["value_mappings"]["etat"]["INACTIF"] == "inactive"

    def test_detect_patterns_with_movement_codes(self) -> None:
        """Test pattern detection with French movement codes."""
        df = pd.DataFrame({
            "oid": [1, 2, 3],
            "type": ["ENTRÉE", "SORTIE", "TRANSFERT"],
            "quantite": [10, 20, 30],
        })

        result = self.detector.detect_patterns(df, "mouvements")

        assert result["primary_key"] == "oid"
        assert "type" in result["value_mappings"]
        assert result["value_mappings"]["type"]["ENTRÉE"] == "inbound"
        assert result["value_mappings"]["type"]["SORTIE"] == "outbound"

    def test_detect_patterns_with_foreign_key(self) -> None:
        """Test pattern detection with foreign key column."""
        df = pd.DataFrame({
            "oid": [1, 2, 3],
            "no_produit": [101, 102, 103],
            "quantite": [10, 20, 30],
        })

        result = self.detector.detect_patterns(df, "mouvements")

        assert result["primary_key"] == "oid"
        assert len(result["foreign_keys"]) > 0
        assert result["foreign_keys"][0]["column"] == "no_produit"
        assert result["foreign_keys"][0]["ref_table"] == "produits"

    def test_detect_patterns_with_split_fields(self) -> None:
        """Test pattern detection with mutually exclusive status fields."""
        df = pd.DataFrame({
            "no_commande": [1, 2, 3, 4],
            "etat_superieur": ["EN_COURS", None, None, None],
            "etat_inferieur": [None, "EN_ATTENTE", None, None],
            "etat": [None, None, "COMPLETE", "ANNULEE"],
        })

        result = self.detector.detect_patterns(df, "commandes")

        assert result["primary_key"] == "no_commande"
        assert result["split_fields"] is not None
        assert len(result["split_fields"]) == 3

    def test_detect_patterns_confidence_calculation(self) -> None:
        """Test that confidence score is calculated correctly."""
        df = pd.DataFrame({
            "no_produit": [1, 2, 3],
            "etat": ["ACTIF", "INACTIF", "ACTIF"],
            "no_categorie": [10, 20, 30],
        })

        result = self.detector.detect_patterns(df, "produits")

        # Should have high confidence with PK, value mapping, and FK
        assert result["confidence"] > 0.5
        assert result["confidence"] <= 1.0

    def test_detect_patterns_with_issues(self) -> None:
        """Test that issues are reported when patterns are not found."""
        df = pd.DataFrame({
            "col1": [1, 2, 3],
            "col2": ["A", "B", "C"],
        })

        result = self.detector.detect_patterns(df, "table")

        # No clear PK pattern, should report issue
        assert isinstance(result["issues"], list)
        # col1 could be detected as PK (unique, no nulls)

    # -------------------------------------------------------------------------
    # Tests for _detect_primary_key
    # -------------------------------------------------------------------------

    def test_detect_primary_key_with_id_column(self) -> None:
        """Test PK detection with 'id' column."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", "B", "no_id"],  # 'no_id' should not be detected as PK
        })

        pk = self.detector._detect_primary_key(df)
        assert pk == "id"

    def test_detect_primary_key_with_no_prefix(self) -> None:
        """Test PK detection with 'no_' prefix pattern."""
        df = pd.DataFrame({
            "no_produit": [101, 102, 103],
            "nom": ["A", "B", "C"],
        })

        pk = self.detector._detect_primary_key(df)
        assert pk == "no_produit"

    def test_detect_primary_key_with_id_suffix(self) -> None:
        """Test PK detection with '_id' suffix pattern."""
        df = pd.DataFrame({
            "product_id": [1, 2, 3],
            "name": ["A", "B", "C"],
        })

        pk = self.detector._detect_primary_key(df)
        assert pk == "product_id"

    def test_detect_primary_key_with_oid(self) -> None:
        """Test PK detection with 'oid' column."""
        df = pd.DataFrame({
            "oid": [1001, 1002, 1003],
            "data": ["X", "Y", "Z"],
        })

        pk = self.detector._detect_primary_key(df)
        assert pk == "oid"

    def test_detect_primary_key_rejects_null_values(self) -> None:
        """Test that PK candidate with null values is rejected."""
        df = pd.DataFrame({
            "no_produit": [101, None, 103],
            "nom": ["A", "B", "C"],
        })

        pk = self.detector._detect_primary_key(df)
        assert pk is None

    def test_detect_primary_key_rejects_duplicates(self) -> None:
        """Test that PK candidate with duplicates is rejected."""
        df = pd.DataFrame({
            "no_produit": [101, 101, 103],
            "nom": ["A", "B", "C"],
        })

        pk = self.detector._detect_primary_key(df)
        assert pk is None

    def test_detect_primary_key_fallback_to_first_column(self) -> None:
        """Test PK detection falls back to first unique column if no pattern match."""
        df = pd.DataFrame({
            "random_col": [1, 2, 3],
            "name": ["A", "B", "C"],
        })

        pk = self.detector._detect_primary_key(df)
        # First column with unique, non-null values
        assert pk == "random_col"

    def test_detect_primary_key_returns_none_if_no_valid_candidate(self) -> None:
        """Test that None is returned when no valid PK exists."""
        df = pd.DataFrame({
            "col1": [1, 1, 2],  # Duplicates
            "col2": [1, None, 2],  # Nulls
        })

        pk = self.detector._detect_primary_key(df)
        assert pk is None

    # -------------------------------------------------------------------------
    # Tests for _detect_value_mappings
    # -------------------------------------------------------------------------

    def test_detect_value_mappings_french_status_codes(self) -> None:
        """Test value mapping detection for French status codes."""
        df = pd.DataFrame({
            "no_produit": [1, 2, 3],
            "etat": ["ACTIF", "INACTIF", "EN_ATTENTE"],
        })

        mappings = self.detector._detect_value_mappings(df)

        assert "etat" in mappings
        assert mappings["etat"]["ACTIF"] == "active"
        assert mappings["etat"]["INACTIF"] == "inactive"
        assert mappings["etat"]["EN_ATTENTE"] == "pending"

    def test_detect_value_mappings_french_movement_codes(self) -> None:
        """Test value mapping detection for French movement codes."""
        df = pd.DataFrame({
            "oid": [1, 2, 3],
            "type_mouvement": ["ENTRÉE", "SORTIE", "TRANSFERT"],
        })

        mappings = self.detector._detect_value_mappings(df)

        assert "type_mouvement" in mappings
        assert mappings["type_mouvement"]["ENTRÉE"] == "inbound"
        assert mappings["type_mouvement"]["SORTIE"] == "outbound"
        assert mappings["type_mouvement"]["TRANSFERT"] == "transfer"

    def test_detect_value_mappings_partial_match(self) -> None:
        """Test value mapping detection with partial code overlap."""
        df = pd.DataFrame({
            "status": ["ACTIF", "INACTIF", "UNKNOWN"],
        })

        mappings = self.detector._detect_value_mappings(df)

        assert "status" in mappings
        assert mappings["status"]["ACTIF"] == "active"
        assert mappings["status"]["INACTIF"] == "inactive"
        # UNKNOWN should not be in mappings (not a known French code)

    def test_detect_value_mappings_no_match(self) -> None:
        """Test value mapping detection with no French codes."""
        df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "city": ["Paris", "London", "New York"],
        })

        mappings = self.detector._detect_value_mappings(df)
        assert len(mappings) == 0

    def test_detect_value_mappings_ignores_nulls(self) -> None:
        """Test value mapping detection handles null values correctly."""
        df = pd.DataFrame({
            "etat": ["ACTIF", None, "INACTIF", None],
        })

        mappings = self.detector._detect_value_mappings(df)

        assert "etat" in mappings
        assert len(mappings["etat"]) == 2

    def test_detect_value_mappings_case_sensitive(self) -> None:
        """Test value mapping detection is case-sensitive."""
        df = pd.DataFrame({
            "etat": ["actif", "INACTIF"],  # Lowercase 'actif'
        })

        mappings = self.detector._detect_value_mappings(df)

        # Only INACTIF should match (uppercase)
        assert "etat" in mappings
        assert "actif" not in mappings["etat"]
        assert "INACTIF" in mappings["etat"]

    # -------------------------------------------------------------------------
    # Tests for _detect_foreign_keys
    # -------------------------------------------------------------------------

    def test_detect_foreign_keys_with_no_prefix(self) -> None:
        """Test FK detection with 'no_' prefix pattern."""
        df = pd.DataFrame({
            "oid": [1, 2, 3],
            "no_produit": [101, 102, 103],
        })

        fks = self.detector._detect_foreign_keys(df, "mouvements")

        assert len(fks) == 1
        assert fks[0]["column"] == "no_produit"
        assert fks[0]["ref_table"] == "produits"

    def test_detect_foreign_keys_with_id_suffix(self) -> None:
        """Test FK detection with '_id' suffix pattern."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "product_id": [101, 102, 103],
        })

        fks = self.detector._detect_foreign_keys(df, "orders")

        assert len(fks) == 1
        assert fks[0]["column"] == "product_id"
        assert fks[0]["ref_table"] == "products"

    def test_detect_foreign_keys_with_code_suffix(self) -> None:
        """Test FK detection with '_code' suffix pattern."""
        df = pd.DataFrame({
            "oid": [1, 2, 3],
            "category_code": ["C1", "C2", "C3"],
        })

        fks = self.detector._detect_foreign_keys(df, "items")

        assert len(fks) == 1
        assert fks[0]["column"] == "category_code"
        assert fks[0]["ref_table"] == "categories"

    def test_detect_foreign_keys_requires_minimum_coverage(self) -> None:
        """Test that FK detection requires 50% minimum coverage."""
        df = pd.DataFrame({
            "oid": [1, 2, 3, 4, 5],
            "no_produit": [101, None, None, None, None],  # Only 20% coverage
        })

        fks = self.detector._detect_foreign_keys(df, "mouvements")

        # Should not detect FK due to low coverage
        assert len(fks) == 0

    def test_detect_foreign_keys_self_reference_skipped(self) -> None:
        """Test that self-referencing FKs are skipped."""
        df = pd.DataFrame({
            "no_produit": [1, 2, 3],
            "parent_no_produit": [None, 1, 2],
        })

        fks = self.detector._detect_foreign_keys(df, "produits")

        # parent_no_produit references produits, should be skipped
        # no_produit is PK
        assert len(fks) == 0

    def test_detect_foreign_keys_calculates_coverage(self) -> None:
        """Test that FK detection calculates coverage percentage."""
        df = pd.DataFrame({
            "oid": [1, 2, 3, 4],
            "no_produit": [101, 102, None, 104],  # 75% coverage
        })

        fks = self.detector._detect_foreign_keys(df, "mouvements")

        assert len(fks) == 1
        assert fks[0]["coverage"] == 75.0

    def test_detect_foreign_keys_no_patterns(self) -> None:
        """Test FK detection with no FK pattern columns."""
        df = pd.DataFrame({
            "oid": [1, 2, 3],
            "name": ["A", "B", "C"],
            "description": ["X", "Y", "Z"],
        })

        fks = self.detector._detect_foreign_keys(df, "items")

        assert len(fks) == 0

    # -------------------------------------------------------------------------
    # Tests for _detect_split_fields
    # -------------------------------------------------------------------------

    def test_detect_split_fields_mutually_exclusive(self) -> None:
        """Test split field detection with mutually exclusive statuses."""
        df = pd.DataFrame({
            "no_commande": [1, 2, 3],
            "etat_superieur": ["EN_COURS", None, None],
            "etat_inferieur": [None, "EN_ATTENTE", None],
            "etat": [None, None, "COMPLETE"],
        })

        split_fields = self.detector._detect_split_fields(df)

        assert split_fields is not None
        assert len(split_fields) == 3
        assert "etat_superieur" in split_fields
        assert "etat_inferieur" in split_fields
        assert "etat" in split_fields

    def test_detect_split_fields_with_status_pattern(self) -> None:
        """Test split field detection with 'status' pattern."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "status_high": ["A", None, None],
            "status_low": [None, "B", None],
        })

        split_fields = self.detector._detect_split_fields(df)

        assert split_fields is not None
        assert len(split_fields) == 2

    def test_detect_split_fields_with_state_pattern(self) -> None:
        """Test split field detection with 'state' pattern."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "state_1": ["X", None, None],
            "state_2": [None, "Y", None],
        })

        split_fields = self.detector._detect_split_fields(df)

        assert split_fields is not None
        assert len(split_fields) == 2

    def test_detect_split_fields_not_mutually_exclusive(self) -> None:
        """Test split field detection rejects non-mutually-exclusive fields."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "etat_superieur": ["A", None, "C"],
            "etat_inferieur": [None, "B", "D"],  # Both non-null in row 3
        })

        split_fields = self.detector._detect_split_fields(df)

        # Should not detect as split fields (not mutually exclusive)
        assert split_fields is None

    def test_detect_split_fields_less_than_two_columns(self) -> None:
        """Test split field detection requires at least 2 status columns."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "etat": ["A", "B", "C"],
        })

        split_fields = self.detector._detect_split_fields(df)

        assert split_fields is None

    def test_detect_split_fields_no_status_pattern(self) -> None:
        """Test split field detection with no status pattern columns."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", "B", "C"],
            "description": ["X", "Y", "Z"],
        })

        split_fields = self.detector._detect_split_fields(df)

        assert split_fields is None

    def test_detect_split_fields_allows_one_value_per_row(self) -> None:
        """Test split field detection allows exactly one non-null value per row."""
        df = pd.DataFrame({
            "id": [1, 2, 3, 4],
            "etat_1": ["A", None, None, None],
            "etat_2": [None, "B", None, None],
            "etat_3": [None, None, "C", None],
            "etat_4": [None, None, None, "D"],
        })

        split_fields = self.detector._detect_split_fields(df)

        assert split_fields is not None
        assert len(split_fields) == 4

    def test_detect_split_fields_allows_all_nulls(self) -> None:
        """Test split field detection allows rows with all null values."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "etat_1": ["A", None, None],
            "etat_2": [None, "B", None],
            "etat_3": [None, None, None],  # All nulls allowed
        })

        split_fields = self.detector._detect_split_fields(df)

        assert split_fields is not None

    # -------------------------------------------------------------------------
    # Edge cases and integration tests
    # -------------------------------------------------------------------------

    def test_empty_dataframe(self) -> None:
        """Test detection with empty DataFrame."""
        df = pd.DataFrame()

        result = self.detector.detect_patterns(df, "empty")

        assert result["primary_key"] is None
        assert result["confidence"] >= 0

    def test_dataframe_with_nulls(self) -> None:
        """Test detection with DataFrame containing null values."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", None, "C"],
            "value": [10.0, None, 30.0],
        })

        result = self.detector.detect_patterns(df, "test")

        assert result["primary_key"] == "id"

    def test_dataframe_with_single_row(self) -> None:
        """Test detection with single-row DataFrame."""
        df = pd.DataFrame({
            "id": [1],
            "name": ["Single"],
        })

        result = self.detector.detect_patterns(df, "single")

        assert result["primary_key"] == "id"

    def test_dataframe_with_numeric_column_names(self) -> None:
        """Test detection with numeric column names."""
        df = pd.DataFrame({
            1: [10, 20, 30],
            2: ["A", "B", "C"],
        })

        # Should handle numeric column names gracefully
        result = self.detector.detect_patterns(df, "test")
        assert result["confidence"] >= 0

    def test_confidence_never_exceeds_one(self) -> None:
        """Test that confidence score is capped at 1.0."""
        df = pd.DataFrame({
            "no_produit": [1, 2, 3],
            "etat": ["ACTIF", "INACTIF", "EN_ATTENTE"],
            "no_categorie": [10, 20, 30],
        })

        result = self.detector.detect_patterns(df, "produits")

        assert result["confidence"] <= 1.0
