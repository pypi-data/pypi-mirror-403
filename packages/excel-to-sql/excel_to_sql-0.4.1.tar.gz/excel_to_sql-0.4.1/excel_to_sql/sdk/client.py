"""
High-level SDK client for excel-to-sqlite.

Provides a simple, programmatic interface for all operations.
"""

from pathlib import Path
from typing import Optional, List, Dict, Any

from excel_to_sql.entities.project import Project
from excel_to_sql.entities.database import Database
from excel_to_sql.entities.excel_file import ExcelFile
from excel_to_sql.entities.dataframe import DataFrame
from excel_to_sql.validators.rules import RuleSet, ValidationRule
from excel_to_sql.validators.reference import ReferenceValidator
from excel_to_sql.profiling.report import QualityReport
from excel_to_sql.metadata.store import MetadataStore
from excel_to_sql.metadata.models import ImportMetadata


class ExcelToSqlite:
    """
    High-level SDK client for excel-to-sqlite.

    This is the main entry point for programmatic access.

    Example:
        # Initialize SDK
        sdk = ExcelToSqlite(project_path="/path/to/project")

        # Import data
        result = sdk.import_excel(
            file_path="data.xlsx",
            type_name="products"
        )

        # Export data
        sdk.export_to_excel(
            output="output.xlsx",
            table="products"
        )

        # Query data
        data = sdk.query("SELECT * FROM products")

        # Profile data
        profile = sdk.profile_table("products")
    """

    def __init__(self, project_path: Optional[Path] = None) -> None:
        """
        Initialize SDK client.

        Args:
            project_path: Path to project directory (default: current directory)
        """
        if project_path is None:
            project_path = Path.cwd()

        self._project_path = Path(project_path)
        self._project: Optional[Project] = None
        self._database: Optional[Database] = None
        self._metadata_store: Optional[MetadataStore] = None

    # ──────────────────────────────────────────────────────────────
    # PROJECT MANAGEMENT
    # ──────────────────────────────────────────────────────────────

    def initialize_project(self) -> None:
        """Initialize a new project in the current directory."""
        self._project = Project(root=self._project_path)
        self._project.initialize()
        self._database = self._project.database
        self._metadata_store = MetadataStore(self._project_path)

    @property
    def project(self) -> Project:
        """Get project instance."""
        if self._project is None:
            self._project = Project(root=self._project_path)
        return self._project

    @property
    def database(self) -> Database:
        """Get database instance."""
        if self._database is None:
            self._database = self.project.database
        return self._database

    @property
    def metadata_store(self) -> MetadataStore:
        """Get metadata store instance."""
        if self._metadata_store is None:
            self._metadata_store = MetadataStore(self._project_path)
        return self._metadata_store

    # ──────────────────────────────────────────────────────────────
    # IMPORT OPERATIONS
    # ──────────────────────────────────────────────────────────────

    def import_excel(
        self,
        file_path: Path | str,
        type_name: str,
        sheet_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
        validate: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Import Excel file into database.

        Args:
            file_path: Path to Excel file
            type_name: Mapping type name from mappings.json
            sheet_name: Sheet name (for multi-sheet files)
            tags: Tags for this import
            validate: Whether to validate data before import
            metadata: Custom metadata to store

        Returns:
            Import result with statistics

        Raises:
            ValueError: If validation fails or file is invalid
        """
        file_path = Path(file_path)

        # Load mapping
        mapping = self.project.get_mapping(type_name)
        if mapping is None:
            raise ValueError(f"Mapping type '{type_name}' not found")

        # Read Excel file
        excel_file = ExcelFile(file_path)
        raw_df = excel_file.read(sheet_name)

        # Create DataFrame wrapper
        df = DataFrame(raw_df)

        # Clean data
        df.clean()

        # Apply transformations
        if hasattr(mapping, "model_dump"):
            mapping_dict = mapping.model_dump()
        else:
            mapping_dict = mapping

        df.apply_transformations(mapping_dict)

        # Apply column mapping
        df.apply_mapping(mapping_dict)

        # Validate if requested
        if validate:
            # TODO: Implement validation from mapping config
            pass

        # Get database table
        table = self.database.get_table(mapping_dict["target_table"])

        # Create table if needed
        if not table.exists():
            table.create(df.to_pandas())

        # Upsert data
        table.upsert(df.to_pandas(), mapping_dict["primary_key"])

        # Record import
        content_hash = excel_file.get_content_hash(sheet_name)
        self.database.record_import(
            file_name=file_path.name,
            file_type=type_name,
            table_name=mapping_dict["target_table"],
            row_count=len(df.to_pandas()),
            column_count=len(df.columns),
            content_hash=content_hash,
        )

        # Store metadata
        import_metadata = ImportMetadata(
            file_name=file_path.name,
            file_type=type_name,
            table_name=mapping_dict["target_table"],
            row_count=len(df.to_pandas()),
            column_count=len(df.columns),
            content_hash=content_hash,
            tags=tags or [],
            custom_metadata=metadata or {},
        )
        self.metadata_store.save(import_metadata)

        return {
            "table": mapping_dict["target_table"],
            "rows": len(df.to_pandas()),
            "columns": len(df.columns),
            "hash": content_hash,
        }

    def import_all_sheets(
        self,
        file_path: Path | str,
        mapping_config: Dict[str, str],
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        Import all sheets from Excel file.

        Args:
            file_path: Path to Excel file
            mapping_config: Mapping of sheet names to type names
                           Example: {"Products": "products", "Categories": "categories"}
            tags: Tags for these imports

        Returns:
            Dictionary mapping sheet names to import results
        """
        file_path = Path(file_path)
        excel_file = ExcelFile(file_path)

        all_sheets = excel_file.read_all_sheets()
        results = {}

        for sheet_name, raw_df in all_sheets.items():
            if sheet_name not in mapping_config:
                continue

            type_name = mapping_config[sheet_name]

            # Import this sheet
            result = self.import_excel(
                file_path=file_path,
                type_name=type_name,
                sheet_name=sheet_name,
                tags=tags,
            )

            results[sheet_name] = result

        return results

    # ──────────────────────────────────────────────────────────────
    # EXPORT OPERATIONS
    # ──────────────────────────────────────────────────────────────

    def export_to_excel(
        self,
        output: Path | str,
        table: Optional[str] = None,
        query: Optional[str] = None,
        sheet_mapping: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Export database data to Excel file.

        Args:
            output: Output Excel file path
            table: Table name to export
            query: Custom SQL query
            sheet_mapping: For multi-sheet export, maps sheet names to tables/queries
                          Example: {"Sheet1": "products", "Sheet2": "SELECT * FROM categories"}

        Note:
            Either table, query, or sheet_mapping must be provided.
            If sheet_mapping is provided, table and query are ignored.
        """
        import pandas as pd

        output = Path(output)

        if sheet_mapping:
            # Multi-sheet export
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                for sheet_name, source in sheet_mapping.items():
                    if source.startswith("SELECT"):
                        # It's a query
                        df = self.database.query(source)
                    else:
                        # It's a table name
                        df = self.database.query(f"SELECT * FROM {source}")

                    df.to_excel(writer, sheet_name=sheet_name, index=False)

        elif query:
            # Single query export
            df = self.database.query(query)
            df.to_excel(output, index=False)

        elif table:
            # Single table export
            df = self.database.query(f"SELECT * FROM {table}")
            df.to_excel(output, index=False)

        else:
            raise ValueError("Either table, query, or sheet_mapping must be provided")

    # ──────────────────────────────────────────────────────────────
    # QUERY OPERATIONS
    # ──────────────────────────────────────────────────────────────

    def query(self, sql: str) -> Any:
        """
        Execute SQL query and return results.

        Args:
            sql: SQL query string

        Returns:
            Query results (format depends on query)
        """
        return self.database.query(sql)

    def get_table(self, table_name: str) -> Any:
        """
        Get table entity.

        Args:
            table_name: Table name

        Returns:
            Table entity
        """
        return self.database.get_table(table_name)

    # ──────────────────────────────────────────────────────────────
    # VALIDATION OPERATIONS
    # ──────────────────────────────────────────────────────────────

    def validate_data(
        self,
        data: Any,
        rules: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate data against rules.

        Args:
            data: DataFrame or data to validate
            rules: Validation rules configuration

        Returns:
            Validation result with errors and warnings
        """
        # Convert to DataFrame if needed
        if not isinstance(data, DataFrame):
            df = DataFrame(data)
        else:
            df = data

        # Build ruleset
        rule_objects = []
        for rule_config in rules:
            rule = ValidationRule(
                column=rule_config["column"],
                rule_type=rule_config["type"],
                params=rule_config.get("params", {}),
                message=rule_config.get("message"),
                severity=rule_config.get("severity", "error"),
            )
            rule_objects.append(rule)

        ruleset = RuleSet(rule_objects)
        result = df.validate(ruleset)

        return result.to_dict()

    # ──────────────────────────────────────────────────────────────
    # PROFILING OPERATIONS
    # ──────────────────────────────────────────────────────────────

    def profile_table(self, table_name: str) -> Dict[str, Any]:
        """
        Profile a database table.

        Args:
            table_name: Table name to profile

        Returns:
            Data profile with quality metrics
        """
        df_data = self.database.query(f"SELECT * FROM {table_name}")
        df = DataFrame(df_data)

        profiler = QualityReport()
        profile = profiler.generate(df.to_pandas())

        return profile.to_dict()

    def profile_excel(self, file_path: Path | str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Profile an Excel file.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name (default: first sheet)

        Returns:
            Data profile with quality metrics
        """
        file_path = Path(file_path)
        excel_file = ExcelFile(file_path)
        df_data = excel_file.read(sheet_name)

        df = DataFrame(df_data)
        df.clean()

        profiler = QualityReport()
        profile = profiler.generate(df.to_pandas())

        return profile.to_dict()

    # ──────────────────────────────────────────────────────────────
    # METADATA OPERATIONS
    # ──────────────────────────────────────────────────────────────

    def get_import_metadata(
        self,
        content_hash: Optional[str] = None,
        tag: Optional[str] = None,
        table_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get import metadata.

        Args:
            content_hash: Filter by content hash
            tag: Filter by tag
            table_name: Filter by table name

        Returns:
            List of import metadata
        """
        if content_hash:
            metadata = self.metadata_store.get_by_hash(content_hash)
            return [metadata.to_dict()] if metadata else []

        elif tag:
            metadata_list = self.metadata_store.get_by_tag(tag)
            return [m.to_dict() for m in metadata_list]

        elif table_name:
            metadata_list = self.metadata_store.get_by_table(table_name)
            return [m.to_dict() for m in metadata_list]

        else:
            metadata_list = self.metadata_store.list_all()
            return [m.to_dict() for m in metadata_list]

    # ──────────────────────────────────────────────────────────────
    # MAPPING MANAGEMENT
    # ──────────────────────────────────────────────────────────────

    def list_mappings(self) -> List[str]:
        """List all available mapping types."""
        return self.project.list_types()

    def get_mapping(self, type_name: str) -> Dict[str, Any]:
        """
        Get mapping configuration.

        Args:
            type_name: Mapping type name

        Returns:
            Mapping configuration
        """
        mapping = self.project.get_mapping(type_name)
        if mapping is None:
            raise ValueError(f"Mapping type '{type_name}' not found")

        if hasattr(mapping, "model_dump"):
            return mapping.model_dump()
        return mapping

    def add_mapping(self, type_name: str, config: Dict[str, Any]) -> None:
        """
        Add a new mapping configuration.

        Args:
            type_name: Mapping type name
            config: Mapping configuration
        """
        self.project.add_mapping(type_name, config)
