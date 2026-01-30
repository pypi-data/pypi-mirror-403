# Refactor: Fix Code Duplication and Project Hygiene Issues

## Problem Description

The codebase contains duplicated code logic and project hygiene issues that impact maintainability and leave temporary files behind.

## 1. Code Duplication

### 1.1 Error Handling Patterns

**Locations:** Throughout `cli.py`

**Duplicated Code:**
```python
# Pattern repeated 10+ times
try:
    # operation
except FileNotFoundError:
    console.print(f"[red]Error:[/red] File not found: {excel_path}")
    raise Exit(1)
except PermissionError:
    console.print(f"[red]Error:[/red] Permission denied: {excel_path}")
    raise Exit(1)
```

**Impact:**
- Violates DRY principle
- Changes require updates in multiple places
- Inconsistent error handling

### 1.2 Primary Key Detection Logic

**Locations:**
- `cli.py` - Magic command
- `auto_pilot/detector.py` - PatternDetector
- Potentially other locations

**Duplicated Code:**
- PK detection logic appears in multiple places
- No single source of truth for PK detection
- Inconsistent implementations

**Impact:**
- Different PK detection in different contexts
- Maintenance burden (fix in multiple places)
- Potential for bugs

### 1.3 Column Mapping Logic

**Locations:**
- `cli.py` - Magic command configuration generation
- CLI configuration management

**Impact:**
- Configuration generation duplicated
- Maintenance burden

## 2. Project Hygiene Issues

### 2.1 Temporary Files Not Cleaned Up

**Issue:** `.excel-to-sql/backups/` directory accumulates backup files

**Current State:**
- Backup files created but never automatically cleaned
- MAX_BACKUPS = 5 but old files may not be cleaned properly
- User must manually delete backup files

**Impact:**
- Disk space usage
- Accumulation of junk files
- Poor user experience

**Example:**
```
.excel-to-sql/backups/
├── test_20260122_113511.xlsx.bak
├── test_20260122_123142.xlsx.bak
├── test_20260122_123227.xlsx.bak
└── test_20260122_123308.xlsx.bak
```

### 2.2 Gitignore Gaps

**Current State:**
- Backups Excel files are gitignored (correct)
- But other temporary files may not be
- Python cache directories (`__pycache__/`)
- Coverage HTML reports (`htmlcov/`)

**Impact:**
- Repository cluttered with temporary files
- Larger repository size
- Noise in git status

### 2.3 Inconsistent File Organization

**Issues:**
- Empty `config/__init__.py`
- No clear organization of utility modules
- Mixed concerns in directories

## Acceptance Criteria

### Code Deduplication (P0)
- [ ] Extract error handling patterns into utility functions
- [ ] Create single source of truth for PK detection
- [ ] Extract column mapping logic into reusable function
- [ ] Create validation utility module
- [ ] Add tests for utility functions

### Project Hygiene (P0)
- [ ] Implement automatic backup cleanup (max 5 files)
- [ ] Add cleanup command for temporary files
- [ ] Update .gitignore with Python cache directories
- [ ] Add .gitignore for coverage reports
- [ ] Clean up empty `__init__.py` files
- [ ] Remove orphaned temporary files

### Code Organization (P1)
- [ ] Create `excel_to_sql/utils/` for utilities
- [ ] Organize modules by responsibility
- [ ] Remove empty or redundant files
- [ ] Add module docstrings

## Proposed Solutions

### 1. Error Handling Utilities

Create `excel_to_sql/utils/errors.py`:

```python
"""Error handling utilities."""

from pathlib import Path
from typing import Optional
from rich.console import Console

console = Console()

def handle_file_error(
    error: Exception,
    file_path: Path,
    context: str = "operation"
) -> None:
    """Handle file-related errors consistently.

    Args:
        error: The exception that occurred
        file_path: Path to the file being processed
        context: Description of the operation
    """
    if isinstance(error, FileNotFoundError):
        console.print(f"[red]Error:[/red] File not found: {file_path}")
        console.print(f"[dim]Context: {context}[/dim]")
        raise SystemExit(1)
    elif isinstance(error, PermissionError):
        console.print(f"[red]Error:[/red] Permission denied: {file_path}")
        console.print("[dim]Tip: Check file permissions[/dim]")
        raise SystemExit(1)
    else:
        console.print(f"[red]Error:[/red] {error}")
        raise SystemExit(1)
```

### 2. Backup Cleanup

**Option A: Automatic Cleanup**
```python
# In AutoFixer or backup creation
def _cleanup_old_backups(backup_dir: Path, max_backups: int = 5) -> None:
    """Remove old backup files, keeping only the most recent max_backups."""
    backups = sorted(backup_dir.glob("*.xlsx.bak"),
                   key=lambda p: p.stat().st_mtime,
                   reverse=True)

    for old_backup in backups[max_backups:]:
        old_backup.unlink()
```

**Option B: Cleanup Command**
```bash
excel-to-sql cleanup --backups
excel-to-sql cleanup --cache
excel-to-sql cleanup --all
```

### 3. Gitignore Improvements

Add to `.gitignore`:
```
# Python cache
__pycache__/
*.py[cod]
*$py.class

# Coverage reports
htmlcov/
.coverage
.coverage.*
*.cover

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
```

### 4. Service Layer Architecture

Create `excel_to_sql/services/`:
- `import_service.py` - Import business logic
- `export_service.py` - Export business logic
- `validation_service.py` - Validation utilities

**Benefits:**
- Eliminates duplication
- Centralizes business logic
- Easier testing
- Better separation of concerns

## Implementation Plan

### Phase 1: Extract Utilities (P0)
1. Create `excel_to_sql/utils/` directory
2. Extract error handling patterns
3. Extract common validation logic
4. Add utility tests

### Phase 2: Refactor CLI (P0)
1. Replace duplicated code with utility calls
2. Simplify error handling
3. Reduce CLI code by 30-40%

### Phase 3: Project Hygiene (P0)
1. Implement automatic backup cleanup
2. Update .gitignore
3. Clean up empty __init__.py files
4. Remove orphaned files

### Phase 4: Reorganization (P1)
1. Create services layer
2. Reorganize utilities
3. Update imports
4. Add module documentation

## Code Duplication Examples

### Before Duplication

**Location:** cli.py (multiple places)
```python
if not path.exists():
    console.print(f"[red]Error:[/red] File not found: {excel_path}")
    raise Exit(1)
```

**After Extraction**

**Utility function:**
```python
# utils/errors.py
def ensure_file_exists(path: Path) -> None:
    """Ensure file exists, exit if not."""
    if not path.exists():
        console.print(f"[red]Error:[/red] File not found: {path}")
        raise SystemExit(1)
```

**Usage:**
```python
# cli.py
from excel_to_sql.utils.errors import ensure_file_exists

ensure_file_exists(path)
```

## Testing Requirements

### Duplication Tests
```python
def test_utility_functions_used()
def test_error_handling_consistency()
def test_single_source_of_truth_for_pk_detection()
```

### Hygiene Tests
```python
def test_backup_cleanup()
def test_temp_files_not_in_repo()
def test_gitignore_effective()
```

## Benefits

### Maintainability
- Single place to update error messages
- Easier to fix bugs (fix once, applies everywhere)
- Less code to maintain

### Code Quality
- Reduced code duplication
- Better organization
- Clearer responsibilities

### User Experience
- Cleaner project directories
- Less disk space usage
- Better performance (less junk files)

## Breaking Changes

None. Internal refactoring only.

## Migration Guide

### For Developers

**Before:**
```python
from excel_to_sql.auto_pilot.detector import PatternDetector
```

**After (if moving modules):**
```python
from excel_to_sql.auto_pilot.detector import PatternDetector
```

Most refactoring is internal and won't affect public APIs.

## Dependencies

No new dependencies required.

## Related Issues

- Improves: Code maintainability
- Reduces: Technical debt
- Supports: #007 Performance/UX/Architecture refactoring
- Enables: Easier future development

## Files to Create

- `excel_to_sql/utils/` (new directory)
- `excel_to_sql/utils/__init__.py`
- `excel_to_sql/utils/errors.py`
- `excel_to_sql/utils/validation.py`
- `tests/test_utils.py`

## Files to Modify

- `excel_to_sql/cli.py` - Use utilities, reduce duplication
- `excel_to_sql/auto_pilot/` - Use shared utilities
- `tests/conftest.py` - Add utility fixtures
- `.gitignore` - Add more patterns

## Success Metrics

- **Code Reduction:** 30-40% reduction in CLI code
- **Duplication:** Eliminate all duplicated code patterns
- **Hygiene:** Clean backup directories
- **Organization:** Clear module responsibilities
- **Test Coverage:** Maintain >85% coverage

## Estimated Impact

### Code Reduction
- CLI: 1000+ → 600-700 lines
- Overall reduction: ~10-15%

### Maintenance
- Single source of truth for common operations
- Easier to update error messages
- Simpler debugging

### Disk Space
- Automatic cleanup of old backups
- Maximum 5 backup files per file
- No accumulation of junk files
