# Functional Specifications - Excel to SQLite

**Version:** 1.0
**Date:** January 19, 2026
**Status:** Functional Specification Document

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Target Users](#2-target-users)
3. [Use Cases](#3-use-cases)
4. [Functional Specifications](#4-functional-specifications)
5. [Non-Functional Specifications](#5-non-functional-specifications)
6. [Constraints](#6-constraints)
7. [Data Requirements](#7-data-requirements)

---

## 1. Introduction

### 1.1 Project Objective

Excel to SQLite is a command-line tool that enables:
- Importing Excel files into SQLite database
- Exporting SQLite data to Excel
- Configurable column mapping management
- Import/export history tracking

### 1.2 MVP Scope

The Minimum Viable Product (MVP) includes:
1. ✅ Import Excel files to SQLite
2. ✅ Column mapping configuration
3. ✅ File change detection
4. ✅ Import history
5. ❌ Export SQLite to Excel (to be implemented)
6. ❌ Display import status (to be implemented)
7. ❌ Configuration management via CLI (to be implemented)

---

## 2. Target Users

### 2.1 User Profiles

**Developers and Data Analysts**
- Regularly manipulate Excel files
- Need to centralize data in SQL database
- Comfortable with command line

**Development Teams**
- Share data via Excel files
- Need to synchronize data
- Want import versioning

### 2.2 Usage Context

- Local development environment
- Integration in data pipelines
- Import/export task automation

---

## 3. Use Cases

### UC-01: Initialize a Project

**Actor:** Developer

**Preconditions:**
- No project initialized

**Description:**
1. User runs `excel-to-sql init`
2. System creates directory structure
3. System initializes database
4. System creates default configuration file

**Postconditions:**
- Project initialized
- Configuration ready to use

**Priority:** ✅ Implemented

---

### UC-02: Import an Excel File

**Actor:** Developer

**Preconditions:**
- Project initialized
- Mapping configured for file type
- Valid Excel file

**Description:**
1. User runs `excel-to-sql import --file data.xlsx --type products`
2. System validates file
3. System calculates content hash
4. If already imported (same hash), system informs user
5. Otherwise, system reads data
6. System cleans data
7. System applies mappings
8. System imports to database (UPSERT)
9. System records import in history
10. System displays summary

**Postconditions:**
- Data imported/updated in database
- History updated

**Priority:** ✅ Implemented

---

### UC-03: Reimport a Modified File

**Actor:** Developer

**Preconditions:**
- File already imported
- File modified

**Description:**
1. User modifies Excel file
2. User runs `excel-to-sql import --file data.xlsx --type products`
3. System detects hash change
4. System reimports data
5. Existing rows updated (UPSERT)
6. New rows inserted

**Postconditions:**
- Database synchronized with file

**Priority:** ✅ Implemented

---

### UC-04: Force Reimport

**Actor:** Developer

**Preconditions:**
- File already imported
- File not modified

**Description:**
1. User runs `excel-to-sql import --file data.xlsx --type products --force`
2. System ignores hash
3. System reimports all data

**Postconditions:**
- Data reimported

**Priority:** ✅ Implemented

---

### UC-05: Export Table to Excel

**Actor:** Developer

**Preconditions:**
- Project initialized
- Data in database

**Description:**
1. User runs `excel-to-sql export --table products --output report.xlsx`
2. System reads table data
3. System generates Excel file
4. System applies formatting

**Postconditions:**
- Excel file generated

**Priority:** ⏳ To be implemented

---

### UC-06: Export with Custom Query

**Actor:** Developer

**Preconditions:**
- Project initialized
- Data in database

**Description:**
1. User runs `excel-to-sql export --query "SELECT * FROM products WHERE price > 100" --output report.xlsx`
2. System executes query
3. System exports results to Excel

**Postconditions:**
- Excel file with results

**Priority:** ⏳ To be implemented

---

### UC-07: View Import History

**Actor:** Developer

**Preconditions:**
- Project initialized
- Imports performed

**Description:**
1. User runs `excel-to-sql status`
2. System displays import list
3. For each import: file, type, date, row count, status

**Postconditions:**
- History displayed

**Priority:** ⏳ To be implemented

---

### UC-08: Configure New Mapping

**Actor:** Developer

**Preconditions:**
- Project initialized

**Description:**
1. User runs `excel-to-sql config --add-type orders --table orders --pk id`
2. System adds mapping to configuration file
3. System validates configuration

**Postconditions:**
- New mapping created

**Priority:** ⏳ To be implemented

---

### UC-09: List Available Mappings

**Actor:** Developer

**Preconditions:**
- Project initialized
- Mappings configured

**Description:**
1. User runs `excel-to-sql config --list`
2. System displays configured types
3. For each type: target table, primary key, columns

**Postconditions:**
- Mapping list displayed

**Priority:** ⏳ To be implemented

---

## 4. Functional Specifications

### 4.1 Command `init`

**Signature:**
```bash
excel-to-sql init [--db-path PATH]
```

**Parameters:**
- `--db-path`: Database path (default: `data/excel-to-sql.db`)

**Behavior:**
1. Creates directories:
   - `imports/`: Excel files to import
   - `exports/`: Exported Excel files
   - `data/`: SQLite database
   - `logs/`: Application logs
   - `config/`: Configuration files

2. Initializes database with tables:
   - `_import_history`: Import history
   - `_export_history`: Export history

3. Creates `config/mappings.json` with example

**Output messages:**
- Success: Display project path, database, directories
- Error: If directories cannot be created

**Current status:** ✅ Implemented

---

### 4.2 Command `import`

**Signature:**
```bash
excel-to-sql import --file FILE --type TYPE [--force]
```

**Parameters:**
- `--file`, `-f`: Excel file path (required)
- `--type`, `-t`: Mapping type to use (required)
- `--force`: Force reimport even if content unchanged

**Detailed behavior:**

**1. File validation**
- Checks file exists
- Checks extension is `.xlsx` or `.xls`
- Error if invalid

**2. Project validation**
- Checks project is initialized
- Error "Not an excel-to-sql project" if not

**3. Type validation**
- Checks type exists in mappings
- Displays available types if unknown
- Error if unknown type

**4. Hash calculation**
- Calculates SHA256 content hash
- Displays first 16 characters

**5. History check**
- If already imported and no `--force`: inform and exit
- If already imported and `--force`: delete old record

**6. Data reading**
- Reads Excel file with pandas
- Displays loaded row count

**7. Data cleaning**
- Removes completely empty rows
- Strips whitespace in cells
- Displays removed row count

**8. Mapping application**
- Renames columns per mappings
- Converts types per mappings
- Displays column and row counts

**9. Database import**
- Performs UPSERT (insert or update)
- Uses primary key from mapping
- Displays inserted/updated row counts

**10. History recording**
- Adds entry in `_import_history`
- Records: filename, path, hash, type, row count, status

**11. Summary display**
- Table with: file, type, table, inserted/updated rows, total, hash

**Return codes:**
- 0: Success
- 1: Error (file not found, unknown type, etc.)

**Current status:** ✅ Implemented

---

### 4.3 Command `export`

**Signature:**
```bash
excel-to-sql export --output OUTPUT [--table TABLE] [--query QUERY]
```

**Parameters:**
- `--output`, `-o`: Output Excel file path (required)
- `--table`: Table name to export (optional)
- `--query`: Custom SQL query (optional)

**Expected behavior:**

**1. Validation**
- Checks that `--table` or `--query` is provided
- Error if both missing: "Error: Must specify either --table or --query"
- Error if both provided: "Error: Cannot specify both --table and --query"
- Validates output directory exists

**2. Export by table**
- If `--table`: executes `SELECT * FROM table`
- Fetches all rows
- Displays row count

**3. Export by query**
- If `--query`: executes SQL query
- Validates query starts with SELECT
- Fetches result set
- Displays row count

**4. Excel file generation**
- Creates file with data using pandas + openpyxl
- Applies formatting:
  - Bold headers with gray background
  - Auto column width based on content
  - Formatted dates (YYYY-MM-DD)
  - Appropriate number formatting (2 decimal places for floats)
  - Freeze header row

**5. History recording**
- Adds entry in `_export_history` table
- Records: table name, query, output path, row count, timestamp

**6. Summary display**
- Rich table with export details
- Shows: source, output file, rows exported, file size
- Success message in green

**Error handling:**
- Table doesn't exist: "Error: Table 'xyz' not found"
- Invalid SQL: "Error: Invalid SQL query"
- Permission denied: "Error: Cannot write to output file"
- Empty result: Warning "Warning: No data to export"

**Return codes:**
- 0: Success
- 1: Error (validation failed, table not found, etc.)

**Current status:** ❌ Placeholder only

**Required Database methods:**
- `Database.export_table(table_name: str) -> pd.DataFrame`
- `Database.execute_query(query: str) -> pd.DataFrame`
- `Database.record_export(table, query, output_path, row_count)`

---

### 4.4 Command `status`

**Signature:**
```bash
excel-to-sql status
```

**Parameters:**
None

**Expected behavior:**

**1. History retrieval**
- Reads `_import_history` table
- Sorts by date descending (newest first)
- Limits to last 50 entries (configurable)

**2. Display**
- Rich table with title "Import History"
- Columns:
  - Date (cyan style, formatted: YYYY-MM-DD HH:MM:SS)
  - Filename (green style)
  - Type (yellow style)
  - Target Table (blue style)
  - Rows (magenta style, right-aligned)
  - Status (style based on status: success=green, failed=red)
  - Hash (dim style, first 12 characters only)

**3. Global statistics**
- Total import count (below table)
- Total imported rows (below table)
- Last import date and time (below table)
- Success rate percentage (below table)

**4. Empty state**
- If no imports: display "No imports yet" in dim text
- Suggest running `excel-to-sql import --help`

**Output example:**
```
╭─────────────────────────────────────────────────────────────────╮
│                        Import History                           │
├────────────┬────────────┬──────┬──────────────┬──────┬──────────┤
│ Date       │ File       │ Type │ Table        │ Rows │ Status   │
├────────────┼────────────┼──────┼──────────────┼──────┼──────────┤
│ 2026-01-19 │ data.xlsx  │ prod │ products     │ 150  │ success  │
│ 2026-01-18 │ orders.xlsx│ ord  │ orders       │  75  │ success  │
╰────────────┴────────────┴──────┴──────────────┴──────┴──────────╯

Total imports: 2 | Total rows: 225 | Last: 2026-01-19 14:30:00 | Success rate: 100%
```

**Error handling:**
- Project not initialized: "Error: Not an excel-to-sql project"
- History table doesn't exist: "Error: Import history not found"

**Return codes:**
- 0: Success
- 1: Error (project not found, database error, etc.)

**Current status:** ❌ Placeholder only (hardcoded "No imports yet")

**Required Database methods:**
- `Database.get_import_history(limit: int = 50) -> pd.DataFrame`

---

### 4.5 Command `config`

**Signature:**
```bash
excel-to-sql config [OPTIONS]

Options:
  --add-type TYPE     Add new mapping type
  --table TABLE       Target table name (required with --add-type)
  --pk PK             Primary key column(s), comma-separated for composite (required with --add-type)
  --file FILE         Excel file to auto-detect columns (optional with --add-type)
  --list              List all configured mappings
  --show TYPE         Show details for a specific mapping type
  --remove TYPE       Remove a mapping type
  --validate          Validate all mappings
```

**Expected behavior:**

#### Subcommand: --add-type (Create new mapping)

**Parameters:**
- `--add-type`: New type name (required)
- `--table`: Target table name (required)
- `--pk`: Primary key column(s) (required, comma-separated for composite keys)
- `--file`: Excel file path (optional, for auto-detecting columns)

**Workflow:**
1. Validates type doesn't already exist (error if duplicate)
2. Validates table name is valid SQL identifier
3. Validates primary key column(s) are provided
4. If `--file` provided:
   - Reads Excel file
   - Auto-detects columns from first row
   - Infers types from data (string, integer, float, boolean, date)
   - Creates mapping with detected columns
5. If no `--file`:
   - Creates empty mapping with just table and PK
   - User must edit `mappings.json` manually to add columns
6. Adds to `mappings.json`
7. Displays created mapping in table format

**Output example:**
```
Created mapping for type 'products':
  Table: products
  Primary Key: id
  Columns:
    - ID → id (integer)
    - Name → name (string)
    - Price → price (float)
```

**Error handling:**
- Type already exists: "Error: Type 'products' already exists"
- Invalid table name: "Error: Invalid table name"
- Missing primary key: "Error: Primary key is required"
- File not found: "Error: Excel file not found"

---

#### Subcommand: --list (List all mappings)

**Parameters:**
- `--list`: Flag to list all mappings

**Workflow:**
1. Reads `mappings.json`
2. Displays Rich table with all mappings
3. Columns: Type, Table, Primary Key, Column Count, Created Date (if tracked)

**Output example:**
```
╭──────────┬──────────────┬────────────┬──────────────╮
│ Type     │ Table        │ Primary Key│ Columns      │
├──────────┼──────────────┼────────────┼──────────────┤
│ products │ products     │ id         │ 3 columns    │
│ orders   │ orders       │ order_id   │ 5 columns    │
│ customers│ customers    │ id         │ 8 columns    │
╰──────────┴──────────────┴────────────┴──────────────╯
```

**Error handling:**
- No mappings found: "No mappings configured"
- Invalid JSON: "Error: Corrupted mapping file"

---

#### Subcommand: --show TYPE (Display specific mapping)

**Parameters:**
- `--show TYPE`: Type name to display

**Workflow:**
1. Validates type exists
2. Reads mapping from `mappings.json`
3. Displays detailed information in formatted table
4. Shows: target table, primary key, all column mappings

**Output example:**
```
Mapping: products
─────────────────────────────────────────
Target Table: products
Primary Key: id

Column Mappings:
┌─────────────┬──────────────┬──────────┬──────────┐
│ Source      │ Target       │ Type     │ Required │
├─────────────┼──────────────┼──────────┼──────────┤
│ ID          │ id           │ integer  │ Yes      │
│ Name        │ name         │ string   │ No       │
│ Price       │ price        │ float    │ No       │
│ Created At  │ created_at   │ date     │ No       │
└─────────────┴──────────────┴──────────┴──────────┘
```

**Error handling:**
- Type not found: "Error: Type 'xyz' not found"

---

#### Subcommand: --remove TYPE (Delete mapping)

**Parameters:**
- `--remove TYPE`: Type name to remove

**Workflow:**
1. Validates type exists
2. Asks for confirmation: "Are you sure you want to delete type 'xyz'? (y/N)"
3. If confirmed:
   - Removes from `mappings.json`
   - Displays success message
4. If not confirmed:
   - Displays "Cancelled"

**Error handling:**
- Type not found: "Error: Type 'xyz' not found"

---

#### Subcommand: --validate (Validate all mappings)

**Parameters:**
- `--validate`: Flag to validate mappings

**Workflow:**
1. Reads `mappings.json`
2. Validates each mapping:
   - Required fields present (target_table, primary_key, column_mappings)
   - Primary key columns exist in column_mappings
   - Column types are valid
   - No duplicate source columns
   - No duplicate target columns
3. Displays results:
   - Total mappings checked
   - Valid mappings count
   - Invalid mappings with errors

**Output example:**
```
Validating 3 mappings...
✅ products: Valid
✅ orders: Valid
❌ customers: Error - Primary key 'customer_id' not found in column mappings

2/3 mappings valid
```

**Return codes:**
- 0: Success (or --validate with no errors)
- 1: Error (validation failed, file not found, etc.)

**Current status:** ❌ Placeholder only (only signature defined)

**Required Project methods:**
- `Project.remove_mapping(type_name: str)`
- `Project.validate_mappings() -> List[ValidationError]`
- `Project.auto_detect_columns(file_path: str) -> Dict`

---

## 5. Non-Functional Specifications

### 5.1 Performance

**Import:**
- Must process 10,000 rows in less than 10 seconds
- Must process 100,000 rows in less than 2 minutes

**Export:**
- Must export 10,000 rows in less than 5 seconds
- Must export 100,000 rows in less than 1 minute

**Memory:**
- Must not consume more than 2x file size in memory

### 5.2 Reliability

**Change detection:**
- SHA256 hash for modification detection
- 100% detection accuracy

**Data integrity:**
- SQL transaction for import (all or nothing)
- Rollback on error

**Error handling:**
- Clear error messages
- Appropriate return codes
- No data loss

### 5.3 Usability

**Command-line interface:**
- Intuitive commands
- Consistent options
- Built-in help (`--help`)

**User feedback:**
- Progress during long operations
- Clear success/failure messages
- Readable summary tables

**Documentation:**
- README with examples
- Help page for each command
- Explicit error messages

### 5.4 Maintainability

**Code:**
- Modular architecture
- Separation of concerns
- Unit and integration tests

**Configuration:**
- JSON configuration files
- Editable mappings without code changes

### 5.5 Security

**Input validation:**
- File type validation
- SQL query escaping
- Mapping validation

**Data:**
- No password storage
- No network connections

---

## 6. Constraints

### 6.1 Technical Constraints

**Language:** Python 3.10+

**Database:** SQLite only (for MVP)

**Excel files:** .xlsx and .xls (via openpyxl)

**Supported systems:** Windows, Linux, macOS

### 6.2 Functional Constraints

**Manual mapping:**
- User must configure mappings manually
- No automatic detection for MVP

**Primary key:**
- Must be defined for each mapping
- Used for UPSERT

**Flat files:**
- Import single sheet per file
- No table relationships for MVP

### 6.3 Time Constraints

**MVP:**
- Phase 1: Initialization and configuration ✅
- Phase 2: Excel file import ✅
- Phase 3: Import history ✅
- Phase 4: Excel export ⏳
- Phase 5: Configuration management ⏳

---

## 7. Data Requirements

### 7.1 Excel File Structure

**Default sheet:**
- First sheet is used by default
- Line 1: Headers (column names)
- Line 2+: Data

**Columns:**
- Excel column names must match mappings
- Case-insensitive matching
- Spaces are preserved

**Data types:**
- Text: Converted to string
- Numbers: Converted to integer or float
- Dates: Converted to date (ISO format)
- Booleans: Converted to boolean (true/false, 1/0)

### 7.2 Data Cleaning

**Empty rows:**
- Automatically removed
- Row is empty if all cells are empty

**Whitespace:**
- Leading/trailing spaces in cells are trimmed
- Multiple spaces reduced to single

**Missing values:**
- Converted to NULL in database
- Required columns reject NULLs

### 7.3 Column Mapping

**Structure:**
```json
{
  "ExcelColumnName": {
    "target": "db_column_name",
    "type": "string|integer|float|boolean|date",
    "required": false,
    "default": null
  }
}
```

**Supported types:**
- `string`: Text (VARCHAR)
- `integer`: Integer (INTEGER)
- `float`: Decimal (REAL)
- `boolean`: Boolean (INTEGER 0/1)
- `date`: Date (TEXT ISO-8601)

**Primary key:**
- Can be composite (multiple columns)
- Must be unique
- Used for UPSERT

### 7.4 Import History

**Table `_import_history`:**
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
```

**Export history (to be implemented):**
```sql
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

## 8. Development Priorities

### 8.1 Critical Priority (Bug Fix)

1. ⚠️ **Fix composite primary key UPSERT bug**
   - Location: `entities/table.py`
   - Test: `tests/test_import.py:327`
   - Impact: Core functionality broken

### 8.2 High Priority (MVP Completion)

2. ❌ **Implement `status` command**
   - Effort: ~3 hours
   - Why: Quick win, provides visibility into imports
   - Status: Placeholder only

3. ❌ **Implement `export` command**
   - Effort: ~8 hours
   - Why: Essential for bidirectional workflow
   - Status: Placeholder only

4. ❌ **Implement `config` command**
   - Effort: ~6 hours
   - Scope: --add-type, --list, --show, --remove, --validate
   - Status: Partially implemented (signature only)

### 8.3 Medium Priority (Enhancements)

5. ⏸️ **Export formatting** - Enhanced Excel formatting
6. ⏸️ **Progress bars** - Visual feedback during operations
7. ⏸️ **Validation framework** - Pre-import data validation
8. ⏸️ **Data transformations** - Custom column transformations
9. ⏸️ **Multiple sheet support** - Import/export multiple sheets

### 8.4 Low Priority (Post-MVP)

10. ⏸️ **Other database support** - PostgreSQL, MySQL
11. ⏸️ **Performance optimization** - Chunked processing, batch operations
12. ⏸️ **Advanced query features** - Saved queries, templates

---

## 9. Acceptance Criteria

### 9.1 General Criteria

- ✅ All MVP commands implemented
- ✅ Tests pass
- ✅ Documentation complete
- ✅ Error messages clear
- ✅ Known bugs fixed

### 9.2 Command-Specific Criteria

**`init`:**
- ✅ Creates all directories
- ✅ Initializes database
- ✅ Creates configuration file

**`import`:**
- ✅ Imports data correctly
- ✅ Detects file changes
- ✅ Performs UPSERT correctly
- ✅ Records history
- ⚠️ Composite primary key UPSERT (bug to fix)

**`export` (to implement):**
- ❌ Exports complete table to Excel
- ❌ Exports custom SQL query to Excel
- ❌ Applies Excel formatting (headers, column widths)
- ❌ Records export history
- ❌ Displays export summary
- ❌ Handles errors (table not found, invalid SQL)

**`status` (to implement):**
- ❌ Displays complete import history
- ❌ Shows statistics (total imports, rows, success rate)
- ❌ Handles empty history gracefully
- ❌ Rich table formatting

**`config` (to implement):**
- ❌ Adds new mapping with auto-detection
- ❌ Lists all mappings
- ❌ Shows specific mapping details
- ❌ Removes mapping with confirmation
- ❌ Validates all mappings
- ❌ Handles errors (duplicate type, not found, invalid JSON)

---

## 10. Conclusion

This document defines the complete functional specifications for the Excel to SQLite project. The MVP covers essential import/export functionality between Excel and SQLite, with flexible mapping management and history tracking.

**Current Implementation Status:**
- ✅ `init` command: Complete
- ✅ `import` command: Complete (with composite key bug)
- ❌ `export` command: Not implemented (placeholder only)
- ❌ `status` command: Not implemented (placeholder only)
- ❌ `config` command: Not implemented (signature only)

**Known Issues:**
- ⚠️ Composite primary key UPSERT has a bug (test skipped in `tests/test_import.py:327`)

**Next Steps (Priority Order):**
1. **Fix composite primary key bug** - Critical for MVP completion
2. **Implement `status` command** - Quick win, provides visibility
3. **Implement `export` command** - Core feature for bidirectional workflow
4. **Implement `config` command** - Essential for user productivity
5. **Improve documentation** - README, user guide, examples
6. **Add tests** - Integration tests for new features

**MVP Completion Estimate:**
- Remaining work: ~21 hours (4 hours bug fix + 17 hours implementation)
- Target date: End of January 2026
- Version: v0.1.0-alpha → v0.1.0
