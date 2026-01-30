"""
Table entity for schema management and UPSERT operations.

Handles table creation, schema inference, and insert/update logic.
"""

from typing import Optional, TYPE_CHECKING

import pandas as pd
import pandas.api.types as ptypes

if TYPE_CHECKING:
    from excel_to_sql.entities.database import Database


class Table:
    """
    Represents a database table with schema and upsert capability.

    Usage:
        table = db.get_table("products")
        table.upsert(dataframe, primary_key=["id"])
        table.exists()  # True
    """

    def __init__(self, database: "Database", name: str) -> None:
        """
        Initialize table reference.

        Args:
            database: Database entity
            name: Table name
        """
        self._database = database
        self._name = name

    # ──────────────────────────────────────────────────────────────
    # PROPERTIES
    # ──────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        """Table name."""
        return self._name

    @property
    def exists(self) -> bool:
        """Check if table exists in database."""
        return self._database.table_exists(self._name)

    @property
    def row_count(self) -> int:
        """Number of rows in table."""
        if not self.exists:
            return 0
        result = self._database.query(f"SELECT COUNT(*) as count FROM {self._name}")
        return int(result.iloc[0]["count"])

    @property
    def columns(self) -> list[str]:
        """List of column names."""
        if not self.exists:
            return []
        result = self._database.query(f"PRAGMA table_info({self._name})")
        return result["name"].tolist()

    # ──────────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ──────────────────────────────────────────────────────────────

    def create(self, df: pd.DataFrame, primary_key: list[str]) -> None:
        """
        Create table from DataFrame schema.

        Args:
            df: DataFrame to infer schema from
            primary_key: List of primary key columns

        Table creation strategy:
        - Infers types from DataFrame dtypes
        - Creates PRIMARY KEY constraint
        - Does NOT create foreign keys (implicit constraints)

        Type mapping (pandas -> SQL):
        - int64 -> INTEGER
        - float64 -> REAL
        - bool -> BOOLEAN
        - datetime64 -> TIMESTAMP
        - object -> TEXT
        """
        # Infer SQL types from pandas dtypes
        type_mappings = {
            col: self._infer_sql_type(dtype) for col, dtype in df.dtypes.items()
        }

        # Build column definitions
        column_defs = [f"{col} {sql_type}" for col, sql_type in type_mappings.items()]

        # Add primary key constraint
        pk_constraint = f", PRIMARY KEY ({', '.join(primary_key)})"

        # Create table SQL
        columns_sql = ", ".join(column_defs)
        create_sql = f"""
            CREATE TABLE IF NOT EXISTS {self._name} (
                {columns_sql}{pk_constraint}
            )
        """

        self._database.execute(create_sql)

    def upsert(self, df: pd.DataFrame, primary_key: list[str]) -> dict:
        """
        Insert or update rows (UPSERT).

        Args:
            df: DataFrame to insert/update
            primary_key: Columns that uniquely identify a row

        Returns:
            Dict with statistics:
            {
                "inserted": 10,
                "updated": 5,
                "failed": 0
            }

        UPSERT logic (SQLite):
        - INSERT new rows
        - On CONFLICT (primary key) -> UPDATE

        Example:
            df = pd.DataFrame({"id": [1, 2], "name": ["A", "B"]})
            table.upsert(df, primary_key=["id"])

            If table already has id=1 with name="Old":
            -> id=1 gets updated to name="A"
            -> id=2 gets inserted
        """
        if not self.exists:
            self.create(df, primary_key)

        inserted = 0
        updated = 0

        for _, row in df.iterrows():
            # Convert row to dict, handling NaN values
            row_dict = row.to_dict()
            row_dict_clean = {
                k: (None if pd.isna(v) else v) for k, v in row_dict.items()
            }

            # Check if row exists
            pk_conditions = [f"{col} = :{col}" for col in primary_key]
            where_clause = " AND ".join(pk_conditions)

            check_sql = f"SELECT COUNT(*) as count FROM {self._name} WHERE {where_clause}"
            result = self._database.query(check_sql, row_dict_clean)
            exists = result.iloc[0]["count"] > 0

            if exists:
                # Update existing row
                set_clauses = [
                    f"{col} = :{col}"
                    for col in df.columns
                    if col not in primary_key
                ]
                update_sql = f"""
                    UPDATE {self._name}
                    SET {', '.join(set_clauses)}
                    WHERE {where_clause}
                """
                self._database.execute(update_sql, row_dict_clean)
                updated += 1
            else:
                # Insert new row
                columns = df.columns.tolist()
                placeholders = ", ".join([f":{col}" for col in columns])
                insert_sql = f"""
                    INSERT INTO {self._name} ({', '.join(columns)})
                    VALUES ({placeholders})
                """
                self._database.execute(insert_sql, row_dict_clean)
                inserted += 1

        return {"inserted": inserted, "updated": updated, "failed": 0}

    def select_all(self) -> pd.DataFrame:
        """Select all rows from table."""
        return self._database.query(f"SELECT * FROM {self._name}")

    def truncate(self) -> None:
        """Delete all rows (keep schema)."""
        if self.exists:
            self._database.execute(f"DELETE FROM {self._name}")

    def drop(self) -> None:
        """Drop table completely."""
        if self.exists:
            self._database.execute(f"DROP TABLE {self._name}")

    # ──────────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ──────────────────────────────────────────────────────────────

    def _infer_sql_type(self, dtype: pd.dtype) -> str:
        """
        Map pandas dtype to SQL type.

        Args:
            dtype: Pandas dtype

        Returns:
            SQL type string
        """
        if ptypes.is_integer_dtype(dtype):
            return "INTEGER"
        elif ptypes.is_float_dtype(dtype):
            return "REAL"
        elif ptypes.is_bool_dtype(dtype):
            return "BOOLEAN"
        elif ptypes.is_datetime64_any_dtype(dtype):
            return "TIMESTAMP"
        else:
            return "TEXT"
