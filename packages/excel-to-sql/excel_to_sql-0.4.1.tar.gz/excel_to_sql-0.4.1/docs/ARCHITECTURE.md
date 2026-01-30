# Technical Architecture - Excel to SQLite

**Version:** 1.0
**Date:** January 19, 2026
**Status:** Architecture Documentation

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Pattern](#2-architecture-pattern)
3. [Component Architecture](#3-component-architecture)
4. [Data Flow](#4-data-flow)
5. [Database Schema](#5-database-schema)
6. [Entity Design](#6-entity-design)
7. [Error Handling](#7-error-handling)
8. [Testing Strategy](#8-testing-strategy)
9. [Technology Stack](#9-technology-stack)
10. [Deployment](#10-deployment)

---

## 1. System Overview

### 1.1 Purpose

Excel to SQLite is a command-line interface (CLI) application that provides bi-directional data transfer between Excel files and SQLite databases, with configurable column mappings and change tracking.

### 1.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                           │
│                      (Typer + Rich)                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Entity Layer                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐     │
│  │ Project  │ │ Database │ │ExcelFile │ │DataFrame │     │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘     │
│                      ┌──────────┐                           │
│                      │  Table   │                           │
│                      └──────────┘                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Model Layer                            │
│                   (Pydantic Models)                          │
│  ┌──────────┐ ┌──────────┐                                 │
│  │ Mappings │ │ Column   │                                 │
│  │          │ │ Mapping  │                                 │
│  └──────────┘ └──────────┘                                 │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Design Principles

1. **Separation of Concerns**: Clear boundaries between CLI, business logic, and data layers
2. **Entity-Oriented**: Domain objects encapsulate behavior and state
3. **Type Safety**: Pydantic models for configuration validation
4. **Testability**: Dependency injection and pure functions where possible
5. **Single Responsibility**: Each class has one clear purpose

---

## 2. Architecture Pattern

### 2.1 Pattern: Layered Architecture with Entities

The application follows a **layered architecture** with an **entity-oriented design**:

```
┌──────────────────────────────────────────────────────────┐
│ Presentation Layer                                       │
│ - CLI commands (cli.py)                                  │
│ - User interaction                                       │
│ - Output formatting (Rich)                               │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│ Business Logic Layer (Entities)                          │
│ - Project: Project coordination                           │
│ - Database: Database operations                          │
│ - ExcelFile: File handling                               │
│ - DataFrame: Data processing                             │
│ - Table: Table operations                                │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│ Data Access Layer                                        │
│ - SQLAlchemy ORM                                         │
│ - SQLite database                                        │
│ - File system operations                                 │
└──────────────────────────────────────────────────────────┘
```

### 2.2 Why This Pattern?

**Benefits:**
- **Maintainability**: Clear separation makes code easier to understand
- **Testability**: Each layer can be tested independently
- **Flexibility**: Can swap implementations (e.g., different databases)
- **Scalability**: Easy to add new features without affecting existing code

---

## 3. Component Architecture

### 3.1 CLI Layer (`cli.py`)

**Responsibility:** User interaction and command orchestration

**Components:**

```python
app = Typer(...)  # Main CLI application
console = Console()  # Rich console for output
```

**Commands:**
- `init()` - Initialize project
- `import_cmd()` - Import Excel file
- `export_cmd()` - Export to Excel (TODO)
- `status()` - Show import history (TODO)
- `config_cmd()` - Manage configuration (TODO)

**Key Design Decisions:**
- **Typer** for CLI: Declarative, type-safe commands
- **Rich** for output: Beautiful, readable terminal output
- **Exit codes**: Standard Unix exit codes (0 = success, 1 = error)

**Error Handling:**
- Try-catch blocks for validation
- User-friendly error messages
- Early exit on validation failure

---

### 3.2 Entity Layer

#### 3.2.1 Project Entity

**File:** `entities/project.py`

**Responsibilities:**
- Project structure management
- Configuration loading/saving
- Database lifecycle management
- Mapping management

**Key Properties:**
```python
root: Path           # Project root directory
imports_dir: Path    # Excel files to import
exports_dir: Path    # Exported Excel files
data_dir: Path       # Database files
logs_dir: Path       # Log files
config_dir: Path     # Configuration files
database: Database   # Lazy-loaded database
mappings: dict       # Loaded mappings
```

**Key Methods:**
```python
initialize()              # Create project structure
add_mapping()             # Add type mapping
get_mapping()             # Get specific mapping
list_types()              # List configured types
```

**Design Patterns:**
- **Lazy Loading**: Database loaded on first access
- **Auto-detection**: Project root found via markers (.git, pyproject.toml)
- **Caching**: Mappings loaded once and cached

---

#### 3.2.2 Database Entity

**File:** `entities/database.py`

**Responsibilities:**
- SQLite connection management
- Table creation/management
- Query execution
- Import history tracking

**Key Methods:**
```python
initialize()              # Create tables
get_table()              # Get Table entity
query()                  # Execute SELECT
execute()                # Execute INSERT/UPDATE/DELETE
record_import()          # Add import history
is_imported()            # Check if hash exists
get_import_history()     # Get all imports
```

**Design Patterns:**
- **Connection Pooling**: SQLAlchemy engine manages connections
- **Context Managers**: Proper resource cleanup

**Tables:**
```sql
-- User tables (created dynamically)
CREATE TABLE {table_name} (
    -- Auto-created from DataFrame schema
);

-- Import history
CREATE TABLE _import_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    file_type TEXT NOT NULL,
    rows_imported INTEGER NOT NULL,
    rows_skipped INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Export history (to be implemented)
CREATE TABLE _export_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT,
    query TEXT,
    output_path TEXT NOT NULL,
    rows_exported INTEGER NOT NULL,
    exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

#### 3.2.3 ExcelFile Entity

**File:** `entities/excel_file.py`

**Responsibilities:**
- Excel file reading
- Content hashing
- File validation

**Key Methods:**
```python
validate()               # Check if file is valid Excel
read()                   # Read Excel to DataFrame
compute_content_hash()   # Calculate SHA256 hash
```

**Design Decisions:**
- **pandas + openpyxl**: Standard Excel reading
- **SHA256 hash**: For reliable change detection
- **Hash of content**: Not just file metadata

---

#### 3.2.4 DataFrame Entity

**File:** `entities/dataframe.py`

**Responsibilities:**
- Data cleaning
- Type conversion
- Mapping application

**Key Methods:**
```python
clean()                  # Remove empty rows, strip whitespace
apply_mapping()          # Apply column mappings
to_pandas()              # Get underlying pandas DataFrame
```

**Type Conversions:**
```python
string    → str/TEXT
integer   → int/INTEGER
float     → float/REAL
boolean   → bool/INTEGER (0/1)
date      → datetime/TEXT (ISO-8601)
```

**Design Decisions:**
- **Wrapper pattern**: Encapsulates pandas DataFrame
- **Immutable operations**: Return new DataFrames
- **Error coercion**: Invalid values → NaN/None

---

#### 3.2.5 Table Entity

**File:** `entities/table.py`

**Responsibilities:**
- Table schema management
- UPSERT operations
- Data retrieval

**Key Methods:**
```python
create_if_not_exists()   # Create table from schema
upsert()                 # Insert or update rows
select_all()             # Get all data
row_count                # Get row count
exists                   # Check if table exists
```

**UPSERT Implementation:**
```python
# SQLite-specific UPSERT syntax
INSERT INTO table (columns...)
VALUES (values...)
ON CONFLICT(primary_key) DO UPDATE SET ...
```

**Known Issue:**
- Composite primary keys have a bug
- See: `tests/test_import.py:327`

---

### 3.3 Model Layer (`models/mapping.py`)

**Purpose:** Configuration validation using Pydantic

**Models:**

```python
class ColumnMapping(BaseModel):
    target: str                              # Target column name
    type: Literal["string", "integer",       # SQL type
                  "float", "boolean", "date"]
    required: bool = False                   # Reject nulls?
    default: Optional[Any] = None            # Default value

class TypeMapping(BaseModel):
    target_table: str                        # Destination table
    primary_key: List[str]                   # PK columns
    column_mappings: Dict[str, ColumnMapping]

class Mappings(BaseModel):
    mappings: Dict[str, TypeMapping]
```

**Benefits:**
- **Type Safety**: Compile-time type checking
- **Validation**: Automatic validation on load
- **Serialization**: Easy JSON conversion
- **Documentation**: Self-documenting schema

---

## 4. Data Flow

### 4.1 Import Workflow

```
┌────────────────┐
│ User executes  │
│  import cmd    │
└───────┬────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 1. Validate file exists & extension    │
└───────┬────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 2. Load project configuration          │
└───────┬────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 3. Validate mapping type exists        │
└───────┬────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 4. ExcelFile.read()                    │
│    - Load Excel file                   │
│    - Compute content hash              │
└───────┬────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 5. Check if already imported           │
│    - Query by hash                     │
│    - Skip if same and no --force       │
└───────┬────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 6. DataFrame.clean()                   │
│    - Remove empty rows                 │
│    - Strip whitespace                  │
└───────┬────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 7. DataFrame.apply_mapping()           │
│    - Rename columns                    │
│    - Convert types                     │
└───────┬────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 8. Table.upsert()                      │
│    - Create table if needed            │
│    - Insert/update rows                │
└───────┬────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 9. Database.record_import()            │
│    - Add to history                    │
└───────┬────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 10. Display summary                    │
│     - Rich table with metrics          │
└────────────────────────────────────────┘
```

### 4.2 Export Workflow (Planned)

```
┌────────────────┐
│ User executes  │
│  export cmd    │
└───────┬────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 1. Validate --table or --query         │
└───────┬────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 2. Load project                        │
└───────┬────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 3. Execute query                       │
│    - SELECT * FROM table               │
│    - Or custom query                   │
└───────┬────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 4. Convert to DataFrame                │
└───────┬────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 5. Generate Excel file                 │
│    - Write data                        │
│    - Apply formatting                  │
└───────┬────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 6. Record export history               │
└───────┬────────────────────────────────┘
        │
        ▼
┌────────────────────────────────────────┐
│ 7. Display summary                     │
└────────────────────────────────────────┘
```

---

## 5. Database Schema

### 5.1 User Tables

User tables are created dynamically based on the Excel file structure and mappings:

```sql
-- Example: products table
CREATE TABLE products (
    id INTEGER,
    name TEXT,
    price REAL,
    -- Primary key is NOT enforced at DB level
    -- Managed at application level
);
```

**Design Decision:**
- No foreign key constraints (implicit relationships)
- No explicit primary key constraints (flexible UPSERT)
- SQLite's flexible typing (type affinity)

### 5.2 System Tables

#### Import History
```sql
CREATE TABLE _import_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL UNIQUE,
    file_type TEXT NOT NULL,
    rows_imported INTEGER NOT NULL,
    rows_skipped INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_import_hash ON _import_history(content_hash);
CREATE INDEX idx_import_date ON _import_history(imported_at);
```

#### Export History
```sql
CREATE TABLE _export_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT,
    query TEXT,
    output_path TEXT NOT NULL,
    rows_exported INTEGER NOT NULL,
    exported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_export_date ON _export_history(exported_at);
```

---

## 6. Entity Design

### 6.1 Design Principles

**1. Single Responsibility**
- Each entity has one clear purpose
- Project coordinates, Database persists, etc.

**2. Encapsulation**
- Internal implementation hidden
- Public API through methods
- Properties for computed values

**3. Immutability where appropriate**
- DataFrame operations return new instances
- Configuration loaded once

**4. Dependency Injection**
- Project passes Database to entities
- Testable with mock dependencies

### 6.2 Entity Relationships

```
Project
  │
  ├─── Database
  │     │
  │     └─── Table (one per table)
  │
  ├─── ExcelFile (one per file)
  │
  └─── DataFrame (one per import)

Mappings (Pydantic models)
  │
  ├─── TypeMapping (one per type)
  │     │
  │     └─── ColumnMapping (one per column)
```

---

## 7. Error Handling

### 7.1 Error Categories

**1. User Errors**
- File not found
- Invalid file type
- Unknown mapping type
- Missing parameters

**2. System Errors**
- Database connection failure
- File read errors
- Disk full

**3. Data Errors**
- Invalid data types
- Missing required fields
- Constraint violations

### 7.2 Error Handling Strategy

```python
try:
    # Operation
except FileNotFoundError as e:
    console.print(f"[red]Error:[/red] File not found")
    raise Exit(1)
except ValueError as e:
    console.print(f"[red]Error:[/red] {e}")
    raise Exit(1)
except Exception as e:
    console.print(f"[red]Error:[/red] Operation failed")
    if debug:
        console.print(traceback.format_exc())
    raise Exit(1)
```

**Principles:**
- **Early validation**: Fail fast
- **Clear messages**: User-friendly errors
- **Exit codes**: Standard Unix conventions
- **Debug mode**: Optional stack traces

---

## 8. Testing Strategy

### 8.1 Test Structure

```
tests/
├── test_database.py      # Database entity tests
├── test_dataframe.py     # DataFrame entity tests
├── test_excel_file.py    # ExcelFile entity tests
├── test_import.py        # Integration tests
├── test_project.py       # Project entity tests
└── test_table.py         # Table entity tests
```

### 8.2 Test Categories

**Unit Tests:**
- Test individual entities in isolation
- Mock external dependencies
- Fast execution

**Integration Tests:**
- Test full workflows
- Real database operations
- Real file I/O

### 8.3 Test Fixtures

```python
@pytest.fixture
def temp_project():
    """Create temporary project with mappings"""
    temp = Path(tempfile.mkdtemp())
    (temp / ".git").mkdir()  # Project marker
    project = Project(root=temp)
    project.initialize()
    # Add mappings...
    yield project
    # Cleanup
    rmtree_with_retry(temp)
```

### 8.4 Test Coverage

**Current Coverage:**
- ✅ Project entity
- ✅ Database entity
- ✅ ExcelFile entity
- ✅ DataFrame entity
- ✅ Table entity
- ✅ Import workflow (14 integration tests)

**Known Gaps:**
- ❌ Export workflow (not implemented)
- ❌ Status display (not implemented)
- ❌ Config management (not implemented)

---

## 9. Technology Stack

### 9.1 Core Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| **typer** | ≥0.12.0 | CLI framework |
| **pydantic** | ≥2.0.0 | Data validation |
| **pandas** | ≥2.0.0 | Data manipulation |
| **openpyxl** | ≥3.0.0 | Excel file support |
| **sqlalchemy** | ≥2.0.0 | Database ORM |
| **rich** | ≥13.0.0 | Terminal UI |

### 9.2 Development Dependencies

| Dependency | Version | Purpose |
|------------|---------|---------|
| **pytest** | ≥8.0.0 | Testing framework |
| **pytest-cov** | ≥4.0.0 | Coverage reporting |

### 9.3 Technology Choices

**Why Typer?**
- Declarative CLI syntax
- Type-safe commands
- Auto-generated help
- Modern Python (3.7+)

**Why Pydantic?**
- Runtime validation
- Type hints
- JSON serialization
- Clear error messages

**Why pandas?**
- Standard for data manipulation
- Excel reading/writing
- Type conversion
- Wide adoption

**Why SQLAlchemy?**
- Database abstraction
- Connection pooling
- Type safety
- SQLite support

**Why Rich?**
- Beautiful terminal output
- Progress bars
- Tables
- Markdown rendering

---

## 10. Deployment

### 10.1 Installation Methods

**1. Development Installation**
```bash
git clone https://github.com/wareflowx/excel-to-sql
cd excel-to-sql
pip install -e .
```

**2. Production Installation (Future)**
```bash
pip install excel-to-sql
```

### 10.2 Project Structure After Initialization

```
my-project/
├── .git/                   # Git repository (marker)
├── pyproject.toml          # Python config (marker)
├── imports/                # Excel files to import
│   └── data.xlsx
├── exports/                # Exported Excel files
│   └── report.xlsx
├── data/                   # Database files
│   └── excel-to-sql.db
├── logs/                   # Application logs
│   └── app.log
└── config/                 # Configuration files
    └── mappings.json
```

### 10.3 Configuration File

`config/mappings.json`:
```json
{
  "products": {
    "target_table": "products",
    "primary_key": ["id"],
    "column_mappings": {
      "ID": {
        "target": "id",
        "type": "integer",
        "required": true
      },
      "Name": {
        "target": "name",
        "type": "string",
        "required": false
      },
      "Price": {
        "target": "price",
        "type": "float",
        "required": false
      }
    }
  }
}
```

### 10.4 Runtime Requirements

**Python:** 3.10 or higher

**Disk Space:**
- Application: ~50 MB (with dependencies)
- Database: Grows with data
- Logs: Rotating logs (to be implemented)

**Memory:**
- Base: ~100 MB
- Per import: ~2x file size

---

## 11. Missing Features (To Implement)

### 11.1 Export Command

**Status:** Placeholder only (`cli.py:211-226`)

**Required Implementation:**

```python
@app.command("export")
def export_cmd(
    output: str = Option(..., "--output", "-o"),
    table: str = Option(None, "--table"),
    query: str = Option(None, "--query"),
) -> None:
    """Export data from database to Excel."""
    # Validation
    if not table and not query:
        console.print("[red]Error:[/red] Must specify --table or --query")
        raise Exit(1)
    if table and query:
        console.print("[red]Error:[/red] Cannot specify both --table and --query")
        raise Exit(1)

    # Load project
    project = Project.from_current_directory()

    # Execute export
    if table:
        df = project.database.export_table(table)
    else:
        df = project.database.execute_query(query)

    # Write to Excel with formatting
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
        worksheet = writer.sheets['Sheet1']
        # Apply formatting (headers, column widths, etc.)

    # Record history
    project.database.record_export(table, query, output, len(df))

    # Display summary
    console.print(f"[green]OK[/green] Exported {len(df)} rows to {output}")
```

**Required Database Methods:**
- `Database.export_table(table_name: str) -> pd.DataFrame`
- `Database.record_export(table, query, output_path, row_count)`

---

### 11.2 Status Command

**Status:** Placeholder only (`cli.py:234-240`)

**Required Implementation:**

```python
@app.command()
def status() -> None:
    """Show import history."""
    project = Project.from_current_directory()
    history = project.database.get_import_history()

    if len(history) == 0:
        console.print("[dim]No imports yet[/dim]")
        return

    # Display table with Rich
    table = Table(title="Import History")
    table.add_column("Date", style="cyan")
    table.add_column("File", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Rows", style="magenta")
    table.add_column("Status", style="blue")

    for _, row in history.iterrows():
        table.add_row(
            row['imported_at'],
            row['file_name'],
            row['file_type'],
            str(row['rows_imported']),
            row['status']
        )

    console.print(table)

    # Statistics
    console.print(f"\nTotal imports: {len(history)}")
    console.print(f"Total rows: {history['rows_imported'].sum()}")
```

**Required Database Methods:**
- `Database.get_import_history() -> pd.DataFrame`

---

### 11.3 Config Command

**Status:** Partially implemented (`cli.py:248-259`)

**Required Subcommands:**

**1. Add Type (--add-type)**
```python
@app.command("config")
def config_cmd(
    add_type: Optional[str] = Option(None, "--add-type", help="New type name"),
    table: Optional[str] = Option(None, "--table", help="Target table name"),
    pk: Optional[str] = Option(None, "--pk", help="Primary key (comma-separated for composite)"),
    list: bool = Option(False, "--list", help="List all mappings"),
    show: Optional[str] = Option(None, "--show", help="Show specific mapping"),
    remove: Optional[str] = Option(None, "--remove", help="Remove mapping"),
) -> None:
    """Manage configuration mappings."""
    project = Project.from_current_directory()

    if add_type:
        # Add new mapping with auto-detected columns
        # TODO: Implement
        pass
    elif list:
        # List all mappings
        # TODO: Implement
        pass
    elif show:
        # Show specific mapping
        # TODO: Implement
        pass
    elif remove:
        # Remove mapping
        # TODO: Implement
        pass
```

**Required Features:**
- Auto-detect columns from Excel file
- Validate mapping syntax
- Interactive mapping creation (optional)

---

### 11.4 Bug: Composite Primary Key

**Location:** `entities/table.py`

**Issue:** UPSERT query generation doesn't properly handle composite primary keys

**Test:** `tests/test_import.py:327` (skipped)

**Current Problem:**
```python
# Current implementation generates:
INSERT INTO table (col1, col2, col3) VALUES (?, ?, ?)
ON CONFLICT(col1, col2) DO UPDATE SET col3 = excluded.col3  # May not work correctly
```

**Required Fix:**
- Properly format composite key in ON CONFLICT clause
- Test with 2+ column primary keys
- Ensure all existing tests still pass

---

## 12. Future Enhancements

### 12.1 Scalability

**Current limitations:**
- Single-file processing
- In-memory data loading
- SQLite only

**Future improvements:**
- Chunked processing for large files
- Streaming for very large datasets
- PostgreSQL/MySQL support

### 12.2 Performance

**Optimizations:**
- Batch UPSERT operations
- Index optimization
- Query caching
- Connection pooling tuning

### 12.3 Features

**Planned:**
- Export command implementation
- Status display implementation
- Config management CLI
- Composite primary key fix
- Data validation framework
- Custom transformations
- Multiple sheet support

---

## 13. Conclusion

The Excel to SQLite project follows a **clean, layered architecture** with:

- **Clear separation** between CLI, business logic, and data layers
- **Entity-oriented design** for maintainability
- **Type safety** through Pydantic models
- **Comprehensive testing** with unit and integration tests
- **Modern Python** practices and dependencies

The architecture is **solid and extensible**, providing a foundation for implementing the remaining MVP features (export, status, config management) and future enhancements.
