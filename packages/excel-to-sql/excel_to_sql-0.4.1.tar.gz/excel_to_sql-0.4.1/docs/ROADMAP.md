# Development Roadmap - Excel to SQLite

**Version:** 1.0
**Date:** January 19, 2026
**Status:** Active Development

---

## Table of Contents

1. [Project Status](#1-project-status)
2. [Development Phases](#2-development-phases)
3. [Current Sprint](#3-current-sprint)
4. [Backlog](#4-backlog)
5. [Technical Debt](#5-technical-debt)
6. [Milestones](#6-milestones)

---

## 1. Project Status

### 1.1 Current State

**Version:** 0.1.0-alpha

**Completion:**
```
███████████████████████░░░░░░░░░░░  60% Complete
```

**Implemented Features:**
- ✅ Project initialization (`init`)
- ✅ Excel import (`import`)
- ✅ Column mapping configuration
- ✅ Change detection (hash-based)
- ✅ Data cleaning and type conversion
- ✅ UPSERT operations
- ✅ Import history tracking
- ✅ Comprehensive test suite

**Missing Features:**
- ❌ Export to Excel (`export`)
- ❌ Status display (`status`)
- ❌ Configuration management (`config`)
- ⚠️ Composite primary key support (buggy)

### 1.2 Blockers

**Known Issues:**
1. Composite primary key UPSERT has a bug (see `test_import.py:327`)
2. No export functionality
3. No interactive status display
4. No CLI for configuration management

---

## 2. Development Phases

### Phase 1: Foundation ✅ **COMPLETE**

**Objective:** Establish project structure and core entities

**Deliverables:**
- ✅ Project structure with Typer CLI
- ✅ Entity layer (Project, Database, ExcelFile, DataFrame, Table)
- ✅ Model layer with Pydantic validation
- ✅ Basic test framework

**Completed:** December 2025

---

### Phase 2: Import Implementation ✅ **COMPLETE**

**Objective:** Implement full Excel to SQLite import workflow

**Deliverables:**
- ✅ File validation and reading
- ✅ Content hashing for change detection
- ✅ Data cleaning pipeline
- ✅ Column mapping and type conversion
- ✅ UPSERT operations
- ✅ Import history tracking
- ✅ Integration tests (14 test cases)

**Completed:** January 2026

**Commits:**
- `24680d1` feat: implement complete import command with integration tests
- `aa8dd84` feat: implement full import command with complete workflow
- `4a54923` test: update Database.get_table test for Phase 2 implementation
- `b48ce49` test: add Table entity tests with UPSERT operations
- `5763ec9` test: add DataFrame wrapper tests with type conversion

---

### Phase 3: Bug Fixes 🔄 **IN PROGRESS**

**Objective:** Fix known bugs before adding new features

**Deliverables:**
- ⚠️ Fix composite primary key UPSERT
- ⏳ Improve error messages
- ⏳ Add edge case handling

**Estimated:** 1-2 days

---

### Phase 4: Export Implementation ⏳ **TODO**

**Objective:** Implement SQLite to Excel export functionality

**Deliverables:**
- ⏳ Export entire table to Excel
- ⏳ Export custom SQL query to Excel
- ⏳ Apply Excel formatting (headers, column widths, number formats)
- ⏳ Export history tracking
- ⏳ Export tests

**Estimated:** 3-5 days

---

### Phase 5: Management Features ⏳ **TODO**

**Objective:** Implement status and configuration management

**Deliverables:**
- ⏳ Status display with import history
- ⏳ Configuration management CLI
  - Add new mapping
  - List mappings
  - Remove mapping
  - Validate mapping
- ⏳ Interactive configuration editor
- ⏳ Management feature tests

**Estimated:** 2-3 days

---

### Phase 6: Polish & Documentation ⏳ **TODO**

**Objective:** Finalize MVP and prepare for release

**Deliverables:**
- ⏳ Complete user documentation
- ⏳ API documentation
- ⏳ Usage examples
- ⏳ README improvements
- ⏳ Changelog
- ⏳ Release notes

**Estimated:** 2-3 days

---

## 3. Current Sprint

### Sprint: Complete MVP Features

**Duration:** 5 days
**Start:** January 19, 2026
**End:** January 24, 2026

### Sprint Goals

1. **Fix composite primary key bug** (CRITICAL)
   - Priority: HIGH
   - Effort: 4 hours
   - Status: 🔴 Not started
   - Blocker: Must be fixed before MVP release

2. **Implement `status` command** (HIGH VALUE, LOW EFFORT)
   - Priority: HIGH
   - Effort: 3 hours
   - Status: 🔴 Not started
   - Why: Quick win, provides visibility into imports

3. **Implement `export` command** (CORE FEATURE)
   - Priority: HIGH
   - Effort: 8 hours
   - Status: 🔴 Not started
   - Why: Essential for bidirectional workflow

4. **Implement basic `config` command** (CORE FEATURE)
   - Priority: MEDIUM
   - Effort: 6 hours
   - Status: 🔴 Not started
   - Scope: --add-type, --list, --show, --remove

### Tasks

#### Task 1: Fix Composite Primary Key

**Issue:** Table.upsert() doesn't properly handle composite primary keys

**Location:** `entities/table.py`

**Test:** `tests/test_import.py:325-329`

**Acceptance Criteria:**
- [ ] Test passes: `test_import_with_composite_primary_key`
- [ ] UPSERT works with 2+ column primary keys
- [ ] All existing tests still pass

**Implementation Notes:**
```python
# Current implementation issue
# UPSERT query generation doesn't properly handle composite keys

# Expected behavior
# INSERT INTO table (col1, col2, col3) VALUES (?, ?, ?)
# ON CONFLICT(col1, col2) DO UPDATE SET col3 = excluded.col3
```

---

#### Task 2: Implement Export Command

**Location:** `cli.py:211-226`

**Acceptance Criteria:**
- [ ] `--table` exports entire table
- [ ] `--query` exports query results
- [ ] Generates valid Excel file
- [ ] Records export history
- [ ] Displays export summary

**Subtasks:**
1. [ ] Add export logic to Database entity
2. [ ] Implement Excel writing with formatting
3. [ ] Add export history table
4. [ ] Update CLI command
5. [ ] Add integration tests

**Code Structure:**
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

    # Load project
    project = Project.from_current_directory()

    # Execute export
    if table:
        df = project.database.export_table(table)
    else:
        df = project.database.execute_query(query)

    # Write to Excel
    df.to_excel(output, index=True)

    # Record history
    project.database.record_export(table, query, output, len(df))

    # Display summary
    console.print(f"[green]OK[/green] Exported {len(df)} rows to {output}")
```

---

#### Task 3: Implement Status Command

**Location:** `cli.py:234-240`

**Acceptance Criteria:**
- [ ] Displays all imports from history
- [ ] Shows import date, filename, type, rows, status
- [ ] Sorted by date (newest first)
- [ ] Shows statistics (total imports, total rows)
- [ ] Handles empty history gracefully

**Implementation:**
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

---

## 4. Backlog

### High Priority (MVP Completion)

**Story: Export Command Implementation**

**Description:** Implement SQLite to Excel export functionality

**Tasks:**
- [ ] `export --table <name> --output <file>` - Export entire table
- [ ] `export --query <sql> --output <file>` - Export query results
- [ ] Add Database.export_table() method
- [ ] Add Database.record_export() method
- [ ] Create export history tracking
- [ ] Add integration tests for export
- [ ] Apply basic Excel formatting (headers, column widths)

**Story: Status Command Implementation**

**Description:** Display import history and statistics

**Tasks:**
- [ ] Implement Database.get_import_history() method
- [ ] Display Rich table with import history
- [ ] Show statistics (total imports, total rows)
- [ ] Handle empty history gracefully
- [ ] Add integration tests

**Story: Configuration Management CLI**

**Description:** Add CLI commands to manage mappings without editing JSON

**Tasks:**
- [ ] `config --add-type <name> --table <table> --pk <columns>` - Create new mapping
- [ ] `config --list` - Show all mappings in table format
- [ ] `config --show <type>` - Display specific mapping details
- [ ] `config --remove <type>` - Delete a mapping
- [ ] `config --validate` - Validate all mappings
- [ ] Auto-detect columns from Excel file for --add-type
- [ ] Add integration tests for config

**Story: Fix Composite Primary Key Bug**

**Description:** Fix UPSERT with composite primary keys

**Tasks:**
- [ ] Debug current UPSERT implementation
- [ ] Fix ON CONFLICT clause for composite keys
- [ ] Enable skipped test in test_import.py:327
- [ ] Add additional tests for edge cases
- [ ] Verify all existing tests still pass

### Medium Priority (Enhancements)

**Story: Export Formatting**

**Description:** Apply advanced formatting to exported Excel files

**Tasks:**
- [ ] Bold headers
- [ ] Auto column width
- [ ] Number formatting (decimal places)
- [ ] Date formatting
- [ ] Conditional formatting (optional)

**Story: Progress Bars**

**Description:** Show progress during long operations

**Tasks:**
- [ ] Import progress bar
- [ ] Export progress bar
- [ ] File reading progress

**Story: Validation Framework**

**Description:** Validate data before import

**Tasks:**
- [ ] Define validation rules in mapping
- [ ] Validate data types
- [ ] Validate required fields
- [ ] Validate value ranges
- [ ] Custom validation functions

**Story: Data Transformations**

**Description:** Apply transformations during import

**Tasks:**
- [ ] Column concatenation
- [ ] Date parsing (multiple formats)
- [ ] Value mapping (lookup tables)
- [ ] Custom Python expressions

**Story: Multiple Sheet Support**

**Description:** Import from multiple sheets in one file

**Tasks:**
- [ ] Specify sheet name or index
- [ ] Import multiple sheets at once
- [ ] Sheet-specific mappings

### Low Priority (Post-MVP)

**Story: Advanced Query Features**

**Description:** More powerful query options

**Tasks:**
- [ ] Saved queries
- [ ] Query templates
- [ ] Join multiple tables

**Story: Performance Optimization**

**Description:** Handle larger datasets

**Tasks:**
- [ ] Chunked processing
- [ ] Batch UPSERT
- [ ] Index optimization
- [ ] Connection pooling tuning

**Story: Alternative Databases**

**Description:** Support more than SQLite

**Tasks:**
- [ ] PostgreSQL support
- [ ] MySQL support
- [ ] Database abstraction layer

---

## 5. Technical Debt

### Critical Priority Debt

**1. Composite Primary Key Bug**
- **Impact:** CRITICAL - Core functionality broken
- **Effort:** 4 hours
- **Location:** `entities/table.py`
- **Action:** Fix UPSERT query generation for composite keys
- **Test:** `tests/test_import.py:327`

### High Priority Debt

**2. Missing Export, Status, Config Implementations**
- **Impact:** HIGH - MVP incomplete
- **Effort:** 17 hours total
- **Location:** `cli.py`, `entities/database.py`
- **Action:** Implement three missing core commands

**3. Hardcoded Error Messages**
- **Impact:** MEDIUM - User experience
- **Effort:** 2 hours
- **Location:** Throughout CLI
- **Action:** Centralize error messages

**4. No Logging Framework**
- **Impact:** MEDIUM - Debugging difficulty
- **Effort:** 4 hours
- **Action:** Add Python logging module

### Medium Priority Debt

**5. Test Coverage Gaps**
- **Impact:** MEDIUM - Quality assurance
- **Effort:** 6 hours
- **Action:** Add tests for export, status, config commands

**6. No Configuration Validation**
- **Impact:** MEDIUM - Runtime errors
- **Effort:** 2 hours
- **Action:** Validate mappings on load

**7. Missing Type Hints in Some Methods**
- **Impact:** LOW - Maintainability
- **Effort:** 2 hours
- **Location:** Various entities
- **Action:** Add complete type hints

### Low Priority Debt

**8. Code Duplication**
- **Impact:** LOW - Maintainability
- **Effort:** 4 hours
- **Action:** Extract common patterns

**9. Missing Docstrings**
- **Impact:** LOW - Documentation
- **Effort:** 2 hours
- **Action:** Complete docstrings

---

## 6. Milestones

### v0.1.0 - MVP Release 🎯

**Target:** End of January 2026

**Features:**
- ✅ Import Excel to SQLite
- ✅ Column mapping
- ✅ Change detection
- ✅ Import history
- ⏳ Export SQLite to Excel
- ⏳ Status display
- ⏳ Configuration CLI

**Release Criteria:**
- [ ] All MVP features implemented
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Known bugs fixed
- [ ] Code coverage > 80%

---

### v0.2.0 - Enhancement Release

**Target:** March 2026

**Features:**
- Export formatting
- Progress bars
- Validation framework
- Data transformations
- Performance improvements

---

### v0.3.0 - Advanced Features

**Target:** May 2026

**Features:**
- Multiple sheet support
- Advanced queries
- PostgreSQL support
- Web UI (optional)

---

### v1.0.0 - Stable Release

**Target:** Q3 2026

**Features:**
- All v0.x features stable
- Complete documentation
- API stability
- Production-ready
- Community feedback incorporated

---

## 7. Definition of Done

### Feature Completion Checklist

For each feature to be considered "done":

- [ ] Code implemented
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] Documentation updated
- [ ] README updated
- [ ] All tests passing
- [ ] Code reviewed
- [ ] No known bugs
- [ ] Performance acceptable

### Sprint Completion Checklist

For each sprint to be considered "done":

- [ ] All sprint tasks completed
- [ ] All acceptance criteria met
- [ ] Tests passing
- [ ] Documentation updated
- [ ] Demo prepared
- [ ] Retrospective conducted

---

## 8. Risk Management

### Technical Risks

**Risk: Composite Primary Key Complexity**
- **Impact:** HIGH
- **Mitigation:** Prioritize fix, simplify implementation if needed
- **Contingency:** Document limitation, require single column keys

**Risk: Large File Performance**
- **Impact:** MEDIUM
- **Mitigation:** Implement chunked processing early
- **Contingency:** Document file size limits

**Risk: SQLite Limitations**
- **Impact:** LOW (for MVP)
- **Mitigation:** Design abstraction layer
- **Contingency:** Postpone alternative DB support

### Project Risks

**Risk: Scope Creep**
- **Impact:** HIGH
- **Mitigation:** Strict MVP definition
- **Contingency:** Move features to backlog

**Risk: Resource Constraints**
- **Impact:** MEDIUM
- **Mitigation:** Realistic sprint planning
- **Contingency:** Adjust timeline

---

## 9. Communication

### Update Cadence

- **Daily:** Standup (async or sync)
- **Weekly:** Sprint review
- **Sprint End:** Retrospective
- **Release:** Announcement notes

### Reporting

- **Progress:** GitHub Projects
- **Issues:** GitHub Issues
- **Documentation:** docs/ folder
- **Discussions:** GitHub Discussions

---

## 10. Next Steps

### Immediate Actions (This Week)

1. ✅ Create specification documents
2. 🔴 Fix composite primary key bug (CRITICAL)
3. 🔴 Implement `status` command (QUICK WIN)
4. 🔴 Implement `export` command (CORE)
5. 🔴 Implement `config` command (CORE)

### Short-term Actions (This Month)

1. Complete all MVP features
2. Write comprehensive tests for new features
3. Improve documentation (README, user guide)
4. Fix any remaining bugs
5. Prepare v0.1.0 release

### Long-term Actions (Next Quarter)

1. Gather user feedback on MVP
2. Plan v0.2.0 features (enhancements)
3. Performance optimization for large files
4. Community building and contributions

---

## 11. Appendix

### Related Documents

- [ANALYSIS.md](ANALYSIS.md) - Current state analysis
- [SPECIFICATIONS.md](SPECIFICATIONS.md) - Functional specifications
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical architecture
- [README.md](../README.md) - Project overview

### Resources

- **Repository:** https://github.com/wareflowx/excel-to-sql
- **Issues:** https://github.com/wareflowx/excel-to-sql/issues
- **Documentation:** https://github.com/wareflowx/excel-to-sql/wiki

---

**Last Updated:** January 19, 2026
**Next Review:** January 26, 2026
