"""
Database entity for excel-to-sql.

Represents a database connection and operations.
"""

from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, Engine, text
import pandas as pd

from excel_to_sql.entities.table import Table


class Database:
    """
    Represents a database connection and operations.

    Usage:
        db = Database("data/excel-to-sql.db")
        db.initialize()

        # Query
        results = db.query("SELECT * FROM movements")

        # Get table
        table = db.get_table("movements")
        table.upsert(data, primary_key=["id"])

        # Check import history
        if db.is_imported(content_hash):
            print("Already imported")
    """

    def __init__(self, path: Path):
        """
        Initialize Database entity.

        Args:
            path: Path to SQLite database file
        """
        self._path = Path(path)
        self._engine: Optional[Engine] = None

    # ──────────────────────────────────────────────────────────────
    # PROPERTIES
    # ──────────────────────────────────────────────────────────────

    @property
    def path(self) -> Path:
        """Database file path."""
        return self._path

    @property
    def exists(self) -> bool:
        """Check if database file exists."""
        return self._path.exists()

    @property
    def engine(self) -> Engine:
        """
        Get SQLAlchemy engine.
        Lazily created on first access.
        """
        if self._engine is None:
            self._path.parent.mkdir(parents=True, exist_ok=True)

            database_url = f"sqlite:///{self._path}"
            self._engine = create_engine(
                database_url, echo=False, connect_args={"check_same_thread": False}
            )

        return self._engine

    # ──────────────────────────────────────────────────────────────
    # PUBLIC METHODS
    # ──────────────────────────────────────────────────────────────

    def initialize(self) -> None:
        """Initialize database (create file and system tables)."""
        # Create database file by connecting
        with self.engine.connect() as conn:
            pass

        # Create system tables
        self._create_import_history_table()

    def query(self, sql: str, params: Optional[dict] = None) -> pd.DataFrame:
        """
        Execute a SQL query and return results as DataFrame.

        Args:
            sql: SQL query string
            params: Optional query parameters

        Returns:
            Pandas DataFrame with results
        """
        with self.engine.connect() as conn:
            df = pd.read_sql_query(text(sql), conn, params=params or {})
        return df

    def execute(self, sql: str, params: Optional[dict] = None) -> int:
        """
        Execute a SQL statement (INSERT, UPDATE, DELETE).

        Args:
            sql: SQL statement
            params: Optional parameters

        Returns:
            Number of rows affected
        """
        with self.engine.begin() as conn:
            result = conn.execute(text(sql), params or {})
            return result.rowcount

    def get_table(self, name: str) -> Table:
        """
        Get a Table entity for this database.

        Args:
            name: Table name

        Returns:
            Table entity for the specified table
        """
        return Table(self, name)

    def table_exists(self, name: str) -> bool:
        """Check if a table exists."""
        query = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name=:name
        """
        results = self.query(query, {"name": name})
        return len(results) > 0

    def is_imported(self, content_hash: str) -> bool:
        """
        Check if a file with this content hash has been imported.

        Args:
            content_hash: SHA-256 hash of file content

        Returns:
            True if already imported
        """
        query = """
            SELECT COUNT(*) as count FROM _import_history
            WHERE content_hash = :content_hash
        """
        results = self.query(query, {"content_hash": content_hash})
        return results.iloc[0]["count"] > 0

    def get_import_history(self) -> pd.DataFrame:
        """Get all import history records."""
        query = "SELECT * FROM _import_history ORDER BY imported_at DESC"
        return self.query(query)

    def export_table(self, table_name: str) -> pd.DataFrame:
        """
        Export all rows from a table to DataFrame.

        Args:
            table_name: Name of the table to export

        Returns:
            DataFrame with all table data

        Raises:
            ValueError: If table doesn't exist
        """
        if not self.table_exists(table_name):
            raise ValueError(f"Table '{table_name}' does not exist")

        return self.query(f"SELECT * FROM {table_name}")

    def record_export(
        self,
        table_name: Optional[str],
        query: Optional[str],
        output_path: str,
        row_count: int,
    ) -> int:
        """
        Record an export in a separate history tracking table.

        Args:
            table_name: Name of exported table (if applicable)
            query: SQL query used (if applicable)
            output_path: Path to exported Excel file
            row_count: Number of rows exported

        Returns:
            Row ID of inserted record
        """
        # Create export history table if it doesn't exist
        self._create_export_history_table()

        sql = """
            INSERT INTO _export_history (
                table_name, query, output_path, row_count
            ) VALUES (
                :table_name, :query, :output_path, :row_count
            )
        """
        self.execute(
            sql,
            {
                "table_name": table_name,
                "query": query,
                "output_path": output_path,
                "row_count": row_count,
            },
        )

        # Get last inserted ID
        result = self.query("SELECT last_insert_rowid() as id")
        return int(result.iloc[0]["id"])

    def record_import(
        self,
        file_name: str,
        file_path: str,
        content_hash: str,
        file_type: str,
        rows_imported: int,
        rows_skipped: int = 0,
        status: str = "success",
        import_duration_ms: Optional[int] = None,
        report_path: Optional[str] = None,
    ) -> int:
        """
        Record an import in the history table.

        Args:
            file_name: Original Excel filename
            file_path: Full path to file
            content_hash: Hash of content
            file_type: Type configuration used
            rows_imported: Number of rows imported
            rows_skipped: Number of rows skipped
            status: success/partial/failed
            import_duration_ms: Duration in milliseconds
            report_path: Path to detailed report

        Returns:
            Row ID of inserted record
        """
        sql = """
            INSERT INTO _import_history (
                file_name, file_path, content_hash, file_type,
                rows_imported, rows_skipped, status, import_duration_ms, report_path
            ) VALUES (
                :file_name, :file_path, :content_hash, :file_type,
                :rows_imported, :rows_skipped, :status, :import_duration_ms, :report_path
            )
        """
        self.execute(
            sql,
            {
                "file_name": file_name,
                "file_path": file_path,
                "content_hash": content_hash,
                "file_type": file_type,
                "rows_imported": rows_imported,
                "rows_skipped": rows_skipped,
                "status": status,
                "import_duration_ms": import_duration_ms,
                "report_path": report_path,
            },
        )

        # Get last inserted ID
        result = self.query("SELECT last_insert_rowid() as id")
        return int(result.iloc[0]["id"])

    # ──────────────────────────────────────────────────────────────
    # PRIVATE METHODS
    # ──────────────────────────────────────────────────────────────

    def _create_import_history_table(self) -> None:
        """Create the _import_history table if it doesn't exist."""
        create_sql = """
            CREATE TABLE IF NOT EXISTS _import_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_type TEXT NOT NULL,
                rows_imported INTEGER DEFAULT 0,
                rows_skipped INTEGER DEFAULT 0,
                status TEXT DEFAULT 'success',
                import_duration_ms INTEGER,
                report_path TEXT,
                UNIQUE(content_hash)
            )
        """
        self.execute(create_sql)

        # Create index for faster queries
        index_sql = """
            CREATE INDEX IF NOT EXISTS idx_import_history_type
            ON _import_history(file_type)
        """
        self.execute(index_sql)

    def _create_export_history_table(self) -> None:
        """Create the _export_history table if it doesn't exist."""
        create_sql = """
            CREATE TABLE IF NOT EXISTS _export_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT,
                query TEXT,
                output_path TEXT NOT NULL,
                row_count INTEGER DEFAULT 0,
                exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.execute(create_sql)

        # Create index for faster queries
        index_sql = """
            CREATE INDEX IF NOT EXISTS idx_export_history_table
            ON _export_history(table_name)
        """
        self.execute(index_sql)

    def dispose(self) -> None:
        """Dispose the database engine and close all connections."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None

