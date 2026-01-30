"""
Interactive Wizard for Auto-Pilot Mode.

Guides users step-by-step through the configuration process,
allowing them to review and accept detected transformations.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from excel_to_sql.auto_pilot.detector import PatternDetector


class InteractiveWizard:
    """
    Interactive wizard for guided configuration.

    Guides users through the Auto-Pilot configuration process,
    allowing them to review and accept each detected transformation.
    """

    def __init__(self, console: Optional[Console] = None) -> None:
        """
        Initialize the wizard.

        Args:
            console: Rich Console instance for output
        """
        self.console = console or Console()
        self.current_step = 0
        self.total_steps = 0
        self.files_data: List[Dict[str, Any]] = []

    def run_interactive_mode(
        self,
        excel_files: List[Path],
        patterns_dict: Dict[str, Dict[str, Any]],
        quality_dict: Dict[str, Dict[str, Any]],
        output_path: Path
    ) -> Dict[str, Any]:
        """
        Run interactive wizard for configuration.

        Args:
            excel_files: List of Excel file paths
            patterns_dict: Dictionary of detected patterns per file
            quality_dict: Dictionary of quality scores per file
            output_path: Where to save the configuration

        Returns:
            Dictionary with final configuration and user choices
        """
        self.files_data = []
        self.total_steps = len(excel_files)

        # Show welcome screen
        self._show_welcome()

        # Process each file
        for idx, file_path in enumerate(excel_files, 1):
            self.current_step = idx
            file_result = self._process_file(
                file_path,
                patterns_dict.get(file_path.stem, {}),
                quality_dict.get(file_path.stem, {})
            )

            self.files_data.append(file_result)

            if idx < len(excel_files):
                self._prompt_continue()

        # Show final summary
        return self._show_final_summary(output_path)

    def _show_welcome(self) -> None:
        """Display welcome screen."""
        welcome_text = Text.assemble(
            "[bold cyan]INTERACTIVE IMPORT MODE[/bold cyan]\n\n",
            "[dim]Guided setup with explanations[/dim]\n\n",
            "You will be guided step-by-step through the ",
            "configuration process for each Excel file.\n\n",
            "For each file, you can:\n",
            "  [bold green]1[/bold green] Accept all transformations\n",
            "  [bold yellow]3[/bold yellow] Skip this file\n",
            "  [bold cyan]4[/bold cyan] View sample data (10 rows)\n",
            "  [bold blue]5[/bold blue] View statistics\n\n",
            "Press [bold]ENTER[/bold] to begin..."
        )

        panel = Panel(
            welcome_text,
            title="excel-to-sql",
            border_style="cyan",
            padding=(1, 2),
        )
        self.console.print(panel)
        self.console.print("")
        input()  # Wait for user to press Enter

    def _process_file(
        self,
        file_path: Path,
        patterns: Dict[str, Any],
        quality: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a single file through the wizard.

        Args:
            file_path: Path to Excel file
            patterns: Detected patterns
            quality: Quality score info

        Returns:
            Result dictionary with user choices
        """
        result = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "accepted_transformations": [],
            "skipped": False,
            "customizations": {}
        }

        while True:
            # Clear screen (print newlines)
            self.console.print("\n")
            header = f"[bold cyan]Step {self.current_step}/{self.total_steps}: {file_path.stem}[/bold cyan]"
            self.console.print(header)
            self.console.print("")

            # Show file analysis
            self._show_file_analysis(file_path, patterns, quality)

            # Show transformations
            transformations = self._get_transformations(patterns)
            if not transformations:
                self.console.print("[yellow]No transformations detected[/yellow]")
                result["skipped"] = True
                break

            self._show_transformations(transformations)

            # Get user choice
            choice = self._get_user_choice()

            if choice == "1":  # Accept all
                result["accepted_transformations"] = transformations
                self.console.print("[green]OK[/green] All transformations accepted")
                break
            elif choice == "3":  # Skip
                result["skipped"] = True
                self.console.print("[yellow]Skipped[/yellow]")
                break
            elif choice == "4":  # View sample
                self._view_sample_data(file_path)
                # Continue the loop to show menu again
                continue
            elif choice == "5":  # View stats
                self._view_statistics(file_path)
                # Continue the loop
                continue
            elif choice == "h":  # Help
                self._show_help()
                input("Press ENTER to continue...")
                # Continue the loop
                continue
            else:
                # Invalid input, show menu again
                self.console.print("[red]Invalid choice. Please try again.[/red]")
                input("Press ENTER to continue...")
                continue

        return result

    def _show_file_analysis(
        self,
        file_path: Path,
        patterns: Dict[str, Any],
        quality: Dict[str, Any]
    ) -> None:
        """Display file analysis information."""
        table = Table(show_header=True, title="File Analysis")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        # Read file info
        try:
            df = pd.read_excel(file_path)
            rows = len(df)
            cols = len(df.columns)
        except Exception:
            rows, cols = 0, 0

        # Get primary key
        pk = patterns.get("primary_key") or "Not detected"
        pk_style = "bold green" if pk != "Not detected" else "yellow"

        # Get quality score
        score = quality.get("score", 0)
        grade = quality.get("grade", "N/A")
        score_style = "bold green" if score >= 90 else "yellow" if score >= 70 else "red"

        table.add_row("Rows", f"{rows:,}")
        table.add_row("Columns", str(cols))
        table.add_row("Primary Key", f"[{pk_style}]{pk}[/{pk_style}]")
        table.add_row("Quality Score", f"[{score_style}]{score}/100 ({grade})[/{score_style}]")

        # Add transformation count
        transformations = self._get_transformations(patterns)
        trans_count = len(transformations)
        table.add_row("Transformations", f"{trans_count}")

        self.console.print(table)
        self.console.print("")

    def _show_transformations(self, transformations: List[Dict[str, Any]]) -> None:
        """Display detected transformations."""
        self.console.print("[bold]Detected Transformations:[/bold]")
        self.console.print("")

        for idx, trans in enumerate(transformations, 1):
            trans_type = trans.get("type", "unknown")
            trans_style = "cyan"

            if trans_type == "value_mapping":
                col = trans.get("column", "")
                mappings = trans.get("mappings", {})
                self.console.print(f"  {idx}. [bold cyan]Value Mapping[/bold cyan]: {col}")
                for source, target in mappings.items():
                    self.console.print(f"     {source} -> {target}")
                self.console.print("")
            elif trans_type == "calculated_column":
                col = trans.get("column", "")
                expr = trans.get("expression", "")
                self.console.print(f"  {idx}. [bold cyan]Calculated Column[/bold cyan]: {col}")
                self.console.print(f"     Expression: {expr}")
                self.console.print("")

    def _get_transformations(self, patterns: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract transformations from patterns."""
        transformations = []

        if not patterns:
            return transformations

        # Value mappings
        value_mappings = patterns.get("value_mappings", {})
        for col, mappings in value_mappings.items():
            transformations.append({
                "type": "value_mapping",
                "column": col,
                "mappings": mappings
            })

        # Calculated columns
        split_fields = patterns.get("split_fields", [])
        if split_fields:
            transformations.append({
                "type": "calculated_column",
                "column": "status",
                "expression": f"COALESCE({', '.join(split_fields)})"
            })

        return transformations

    def _get_user_choice(self) -> str:
        """Get and validate user choice."""
        while True:
            try:
                choice = input("\nChoice [1/3/4/5/h] (or 'q' to cancel): ").strip().lower()

                if choice == 'q':
                    return "q"
                elif choice == '1':
                    return "1"
                elif choice == '3':
                    return "3"
                elif choice == '4':
                    return "4"
                elif choice == '5':
                    return "5"
                elif choice == 'h':
                    return "h"
                else:
                    self.console.print("[yellow]Invalid choice. Please enter 1, 3, 4, 5, or h[/yellow]")
            except (EOFError, KeyboardInterrupt):
                return "q"

    def _view_sample_data(self, file_path: Path) -> None:
        """Display sample data from file."""
        self.console.print("\n[bold]Sample Data (first 10 rows):[/bold]")
        self.console.print("")

        try:
            df = pd.read_excel(file_path)
            # Show first 10 rows
            sample_df = df.head(10)

            table = Table(show_header=True, title=f"Sample: {file_path.name}")
            for col in sample_df.columns:
                table.add_column(str(col))

            for _, row in sample_df.iterrows():
                table.add_row(*[str(v) if pd.notna(v) else "" for v in row])

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error reading file:[/red] {e}")

        self.console.print("")
        input("Press ENTER to return...")

    def _view_statistics(self, file_path: Path) -> None:
        """Display detailed statistics for the file."""
        self.console.print("\n[bold]File Statistics:[/bold]")
        self.console.print("")

        try:
            df = pd.read_excel(file_path)

            table = Table(show_header=True, title="Column Statistics")
            table.add_column("Column", style="cyan")
            table.add_column("Type", style="blue")
            table.add_column("Non-Null", style="green")
            table.add_column("Null %", style="yellow")

            for col in df.columns:
                dtype = str(df[col].dtype)
                non_null = df[col].notna().sum()
                null_count = df[col].isna().sum()
                null_pct = (null_count / len(df)) * 100

                table.add_row(
                    col,
                    dtype,
                    f"{non_null}",
                    f"{null_pct:.1f}%"
                )

            self.console.print(table)

        except Exception as e:
            self.console.print(f"[red]Error reading file:[/red] {e}")

        self.console.print("")
        input("Press ENTER to return...")

    def _show_help(self) -> None:
        """Display help information."""
        help_text = """
[bold cyan]Help - Interactive Mode[/bold cyan]

[bold]Menu Options:[/bold]

[1] Accept All Transformations
    → Accept all detected transformations for this file
    → Add them to the configuration

[3] Skip File
    → Skip this file, no configuration will be generated
    → File will not be imported

[4] View Sample Data
    → Display first 10 rows of the file
    → See the actual data to make informed decisions

[5] View Statistics
    → Show detailed statistics for each column
    → See data types, null percentages, value counts

[h] Help
    → Show this help screen

[q] Cancel
    → Cancel the wizard and return to CLI
"""
        self.console.print(help_text)

    def _prompt_continue(self) -> None:
        """Prompt user to continue to next file."""
        self.console.print("\n[dim]Press ENTER to continue to next file...[/dim]")
        try:
            input()
        except (EOFError, KeyboardInterrupt):
            pass

    def _show_final_summary(self, output_path: Path) -> Dict[str, Any]:
        """
        Show final summary and get final action.

        Args:
            output_path: Where to save configuration

        Returns:
            Final result dictionary
        """
        self.console.print("\n")
        summary_panel = Panel(
            "[bold cyan]Configuration Complete![/bold cyan]\n\n"
            "All files have been processed. Here's the summary:",
            title="excel-to-sql",
            border_style="green",
            padding=(1, 2),
        )
        self.console.print(summary_panel)
        self.console.print("")

        # Show summary table
        table = Table(show_header=True, title="Files Processed")
        table.add_column("File", style="cyan")
        table.add_column("Transformations", style="green")
        table.add_column("Status", style="yellow")

        accepted_count = 0
        skipped_count = 0

        for file_data in self.files_data:
            if file_data.get("skipped"):
                status = "[yellow]Skipped[/yellow]"
                skipped_count += 1
                trans_count = 0
            else:
                status = "[green]Accepted[/green]"
                accepted_count += 1
                trans_count = len(file_data.get("accepted_transformations", []))

            table.add_row(file_data["file_name"], f"{trans_count}", status)

        self.console.print(table)
        self.console.print("")
        self.console.print(f"Files accepted: [green]{accepted_count}[/green]")
        self.console.print(f"Files skipped: [yellow]{skipped_count}[/yellow]")
        self.console.print("")

        # Get final action
        while True:
            try:
                action = input("Final action: [s]ave config, [q]uit: ").strip().lower()

                if action == 's' or action == 'i':
                    # Save configuration
                    return {
                        "action": "save",
                        "files_data": self.files_data
                    }
                elif action == 'q':
                    # Cancel
                    self.console.print("[yellow]Wizard cancelled[/yellow]")
                    return {
                        "action": "cancel"
                    }
                else:
                    self.console.print("[yellow]Invalid choice. Please enter 's' or 'q'[/yellow]")
            except (EOFError, KeyboardInterrupt):
                self.console.print("\n[yellow]Wizard cancelled[/yellow]")
                return {
                    "action": "cancel"
                }
