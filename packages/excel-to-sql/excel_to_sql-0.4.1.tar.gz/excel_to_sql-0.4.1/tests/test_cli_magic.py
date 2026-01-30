"""
Integration tests for CLI magic command.

Tests use subprocess to invoke the actual CLI and verify output.
"""

import pytest
import subprocess
import sys
import json
from pathlib import Path
import tempfile
import os


class TestMagicCommand:
    """Integration tests for the magic command."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.fixtures_dir = Path(__file__).parent / "fixtures" / "auto_pilot"

    def _run_magic_command(self, args: list[str]) -> tuple[int, str, str]:
        """
        Run the magic command as a subprocess.

        Args:
            args: Command line arguments

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        cmd = ["uv", "run", "excel-to-sql", "magic"] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        return result.returncode, result.stdout, result.stderr

    def test_magic_command_help(self) -> None:
        """Test that magic command has help text."""
        exit_code, stdout, stderr = self._run_magic_command(["--help"])

        assert exit_code == 0
        assert "auto-pilot" in stdout.lower()
        assert "magic" in stdout.lower()

    def test_magic_command_no_files(self) -> None:
        """Test magic command with directory containing no Excel files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exit_code, stdout, stderr = self._run_magic_command(["--data", tmpdir, "--dry-run"])

            # Should exit with error
            assert exit_code == 1
            assert "No Excel files found" in stdout

    def test_magic_command_invalid_directory(self) -> None:
        """Test magic command with non-existent directory."""
        exit_code, stdout, stderr = self._run_magic_command(["--data", "/nonexistent/path", "--dry-run"])

        # Should exit with error
        assert exit_code == 1
        assert "not found" in stdout.lower()

    def test_magic_command_with_fixtures_dry_run(self) -> None:
        """Test magic command with fixture files in dry-run mode."""
        exit_code, stdout, stderr = self._run_magic_command([
            "--data", str(self.fixtures_dir),
            "--dry-run"
        ])

        assert exit_code == 0
        assert "auto-pilot" in stdout.lower()
        assert "Found 3 Excel file(s)" in stdout
        assert "commandes" in stdout
        assert "mouvements" in stdout
        assert "produits" in stdout
        assert "Dry-Run Mode" in stdout

    def test_magic_command_detects_primary_keys(self) -> None:
        """Test that magic command detects primary keys."""
        exit_code, stdout, stderr = self._run_magic_command([
            "--data", str(self.fixtures_dir),
            "--dry-run"
        ])

        assert exit_code == 0
        assert "PK: [bold green]commande[/bold green]" in stdout
        assert "PK: [bold green]oid[/bold green]" in stdout
        assert "PK: [bold green]no_produit[/bold green]" in stdout

    def test_magic_command_shows_summary_table(self) -> None:
        """Test that magic command displays detection summary table."""
        exit_code, stdout, stderr = self._run_magic_command([
            "--data", str(self.fixtures_dir),
            "--dry-run"
        ])

        assert exit_code == 0
        assert "DETECTION SUMMARY" in stdout
        assert "Table" in stdout
        assert "Rows" in stdout
        assert "PK" in stdout
        assert "Score" in stdout

    def test_magic_command_generates_config_file(self) -> None:
        """Test that magic command generates mappings.json file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            exit_code, stdout, stderr = self._run_magic_command([
                "--data", str(self.fixtures_dir),
                "--output", str(output_dir)
            ])

            assert exit_code == 0
            assert "Auto-Pilot Analysis Complete" in stdout

            # Verify mappings.json was created
            mappings_file = output_dir / "mappings.json"
            assert mappings_file.exists()

            # Verify it's valid JSON
            with open(mappings_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            assert "mappings" in config
            assert "commandes" in config["mappings"]
            assert "mouvements" in config["mappings"]
            assert "produits" in config["mappings"]

    def test_magic_command_config_structure(self) -> None:
        """Test that generated config has correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            exit_code, stdout, stderr = self._run_magic_command([
                "--data", str(self.fixtures_dir),
                "--output", str(output_dir)
            ])

            mappings_file = output_dir / "mappings.json"
            with open(mappings_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Verify produits table structure
            produits = config["mappings"]["produits"]
            assert produits["target_table"] == "produits"
            assert produits["primary_key"] == ["no_produit"]
            assert "column_mappings" in produits
            assert "value_mappings" in produits
            assert "validation_rules" in produits
            assert "metadata" in produits

            # Verify primary key validation
            pk_rules = [r for r in produits["validation_rules"] if r["type"] == "unique"]
            assert len(pk_rules) == 1
            assert pk_rules[0]["column"] == "no_produit"

    def test_magic_command_includes_value_mappings(self) -> None:
        """Test that generated config includes French code mappings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            self._run_magic_command([
                "--data", str(self.fixtures_dir),
                "--output", str(output_dir)
            ])

            mappings_file = output_dir / "mappings.json"
            with open(mappings_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Verify produits has value mappings
            produits = config["mappings"]["produits"]
            assert len(produits["value_mappings"]) > 0

            # Check for etat mapping
            etat_mapping = [m for m in produits["value_mappings"] if m["column"] == "etat"]
            assert len(etat_mapping) == 1
            assert "ACTIF" in etat_mapping[0]["mappings"]
            assert etat_mapping[0]["mappings"]["ACTIF"] == "active"

    def test_magic_command_includes_metadata(self) -> None:
        """Test that generated config includes metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            self._run_magic_command([
                "--data", str(self.fixtures_dir),
                "--output", str(output_dir)
            ])

            mappings_file = output_dir / "mappings.json"
            with open(mappings_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Verify metadata
            commandes = config["mappings"]["commandes"]
            metadata = commandes["metadata"]
            assert "row_count" in metadata
            assert "column_count" in metadata
            assert "detection_confidence" in metadata
            assert metadata["auto_generated"] is True
            assert metadata["primary_key_detected"] is True

    def test_magic_command_mouvements_config(self) -> None:
        """Test that mouvements config is generated correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "output"

            self._run_magic_command([
                "--data", str(self.fixtures_dir),
                "--output", str(output_dir)
            ])

            mappings_file = output_dir / "mappings.json"
            with open(mappings_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # Verify mouvements structure
            mouvements = config["mappings"]["mouvements"]
            assert mouvements["target_table"] == "mouvements"
            assert mouvements["primary_key"] == ["oid"]

            # Verify value mappings for type column
            type_mapping = [m for m in mouvements["value_mappings"] if m["column"] == "type"]
            assert len(type_mapping) == 1
            assert "ENTRÉE" in type_mapping[0]["mappings"]
