"""
Create test fixtures including sample Excel files.
"""

import pandas as pd
from pathlib import Path


def create_sample_excel():
    """Create a comprehensive sample Excel file for testing."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)

    # Create comprehensive test data with various types and edge cases
    data = {
        "id": list(range(1, 101)),
        "name": [f"Product {chr(65 + (i % 26))}{i}" for i in range(1, 101)],
        "quantity": [100 + i * 10 for i in range(100)],
        "price": [10.50 + i * 0.99 for i in range(100)],
        "date": pd.date_range("2024-01-01", periods=100, freq="D"),
        "active": [True if i % 2 == 0 else False for i in range(100)],
    }

    df = pd.DataFrame(data)

    # Add edge cases
    # Rows 30-31 will be empty (test empty row handling)
    df.loc[30:31, :] = None

    # Row 50 will have null quantity (test null handling)
    df.loc[50, "quantity"] = None

    # Row 60 will have extra spaces (test stripping)
    df.loc[60, "name"] = "  Product with spaces  "

    # Row 70 will have invalid date (test date parsing)
    df.loc[70, "date"] = "N/A"

    # Row 80 will have zero values (test handling of edge values)
    df.loc[80, "quantity"] = 0
    df.loc[80, "price"] = 0.0

    # Row 90 will have very long decimal (test float precision)
    df.loc[90, "price"] = 99.999999

    # Write to Excel
    output_path = fixtures_dir / "sample_data.xlsx"
    df.to_excel(output_path, index=False, sheet_name="Data")

    print(f"Created sample Excel file: {output_path}")
    print(f"  Rows: {len(df)}")
    print(f"  Columns: {len(df.columns)}")

    return output_path


if __name__ == "__main__":
    create_sample_excel()
