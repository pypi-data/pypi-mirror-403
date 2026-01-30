"""
Quality report generation.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import pandas as pd

from excel_to_sql.profiling.profiler import DataFrameProfile, DataProfiler


class QualityReport:
    """
    Generates and saves data quality reports.

    Example:
        report = QualityReport()
        report.generate(df, output_path="report.html")
    """

    def __init__(self) -> None:
        """Initialize quality report generator."""
        self.profiler = DataProfiler()

    def generate(self, df: pd.DataFrame, output_path: Optional[Path] = None) -> DataFrameProfile:
        """
        Generate quality report for DataFrame.

        Args:
            df: DataFrame to analyze
            output_path: Optional path to save report

        Returns:
            DataFrameProfile with analysis
        """
        profile = self.profiler.profile(df)

        if output_path:
            self.save_report(profile, output_path)

        return profile

    def save_report(self, profile: DataFrameProfile, output_path: Path) -> None:
        """
        Save report to file.

        Args:
            profile: Profile to save
            output_path: Path for output file (format determined by extension)
        """
        output_path = Path(output_path)

        if output_path.suffix == ".json":
            self.save_json(profile, output_path)
        elif output_path.suffix == ".md":
            self.save_markdown(profile, output_path)
        elif output_path.suffix == ".html":
            self.save_html(profile, output_path)
        else:
            # Default to JSON
            self.save_json(profile, output_path)

    def save_json(self, profile: DataFrameProfile, output_path: Path) -> None:
        """Save report as JSON."""
        with open(output_path, "w") as f:
            json.dump(profile.to_dict(), f, indent=2, default=str)

    def save_markdown(self, profile: DataFrameProfile, output_path: Path) -> None:
        """Save report as Markdown."""
        markdown = profile.to_markdown()
        output_path.write_text(markdown, encoding="utf-8")

    def save_html(self, profile: DataFrameProfile, output_path: Path) -> None:
        """Save report as HTML."""
        markdown = profile.to_markdown()

        # Simple markdown to HTML conversion
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Data Quality Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 1200px; margin: 40px auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #333; }}
        h2 {{ color: #555; margin-top: 30px; }}
        h3 {{ color: #777; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .error {{ color: #d32f2f; }}
        .warning {{ color: #f57c00; }}
        .info {{ color: #1976d2; }}
    </style>
</head>
<body>
{self._markdown_to_html(markdown)}
</body>
</html>
"""
        output_path.write_text(html, encoding="utf-8")

    def _markdown_to_html(self, markdown: str) -> str:
        """Convert markdown to HTML (simple implementation)."""
        html = markdown
        html = html.replace("# ", "<h1>").replace("\n", "</h1>\n", 1)
        html = html.replace("## ", "<h2>").replace("\n", "</h2>\n", 1)
        html = html.replace("### ", "<h3>").replace("\n", "</h3>\n", 1)
        html = html.replace("- **", "<strong>").replace("**:", "</strong>:")
        html = html.replace("\n\n", "</p><p>")
        html = f"<p>{html}</p>"
        return html
