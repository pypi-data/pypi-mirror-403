# Refactor: Improve Performance, UX, and Architecture

## Problem Description

The codebase has several performance issues, user experience gaps, and architectural inconsistencies that impact usability and maintainability.

## 1. Performance Issues

### 1.1 Eager Loading of All Dependencies

**Location:** All modules

**Current Issue:**
```python
# All heavy dependencies imported at startup
import pandas as pd  # Always loaded
from sqlalchemy import create_engine  # Always loaded
from rich.console import Console  # Always loaded
```

**Impact:**
- Slow application startup
- High memory usage for simple operations
- Unnecessary imports for CLI help commands

### 1.2 No Streaming for Large Files

**Location:** Excel file reading

**Current Code:**
```python
df = pd.read_excel(file_path)  # Loads entire file into memory
```

**Impact:**
- Cannot process files larger than available RAM
- Crashes on large files (>100MB)
- No progress indication during load

### 1.3 No Caching

**Location:** Profiling, metadata operations

**Current Issue:**
- Quality profiling recalculates everything on every run
- Metadata queries repeated without caching
- No result caching for expensive operations

**Impact:**
- Slow repeated operations
- Poor performance on large datasets

## 2. User Experience Issues

### 2.1 Generic Error Messages

**Current State:**
```python
console.print(f"[red]Error:[/red] {e}")
```

**Issue:**
- Error messages don't explain what went wrong
- No suggestions for resolution
- No context about what operation failed

**Example:**
```
Error: FileNotFoundError
# Better:
Error: File 'products.xlsx' not found in directory './data'
       Tip: Check the file path or run 'excel-to-sql status' to see imported files
```

### 2.2 No Progress Indication for Long Operations

**Current State:**
- Rich spinner for "Processing..." but no percentage
- No time estimates
- No indication of which step is running

**User Impact:**
- Unclear wait times
- Cannot estimate completion
- Frustration with long-running operations

### 2.3 No Confirmation for Destructive Operations

**Missing:**
- No confirmation before overwriting existing data
- No confirmation before deleting files
- No "dry run" mode for most operations

## 3. Architectural Issues

### 3.1 Business Logic in CLI

**Location:** `cli.py` (1000+ lines)

**Current Issue:**
- CLI contains business logic for:
  - Pattern detection logic
  - Quality assessment
  - Configuration generation
  - Data transformation logic

**Impact:**
- CLI is difficult to test
- Business logic cannot be reused programmatically
- Violates Single Responsibility Principle

**Example:**
```python
# In cli.py - Should be in a separate service module
def _generate_mappings_config(all_results, patterns_dict, quality_dict):
    # 50+ lines of business logic
```

### 3.2 InteractiveWizard Mixing Concerns

**Location:** `ui/interactive.py`

**Current Issue:**
- Wizard handles both:
  - User interaction (input prompts)
  - Display formatting (Rich output)
  - Business logic (transformation extraction)
  - State management

**Impact:**
- Difficult to test business logic independently
- Cannot reuse wizard logic in different UI (web, GUI)
- Tight coupling to Rich library

### 3.3 No Lazy Loading

**Location:** All imports

**Current Issue:**
```python
# All imports at top level
import pandas as pd
from rich.console import Console
```

**Impact:**
- Slow startup time
- High memory usage
- Cannot run simple commands without loading everything

## Acceptance Criteria

### Performance Improvements (P0)
- [ ] Implement lazy loading for heavy dependencies (pandas, SQLAlchemy)
- [ ] Add streaming support for large Excel files
- [ ] Implement caching for expensive operations
- [ ] Add chunked reading for large files
- [ ] Optimize import statements

### User Experience (P0)
- [ ] Improve error messages with context and suggestions
- [ ] Add progress percentage for long operations
- [ ] Add time estimates for operations
- [ ] Add confirmation prompts for destructive operations
- [ ] Add cancel support for long operations

### Architecture Refactoring (P1)
- [ ] Extract business logic from CLI into service layer
- [ ] Separate InteractiveWizard concerns (UI vs logic)
- [ ] Create service module for business operations
- [ ] Implement lazy loading pattern
- [ ] Add dependency injection for testing

## Proposed Architecture

### Service Layer

Create `excel_to_sql/services/`:

```
services/
├── import_service.py      # Import business logic
├── export_service.py      # Export business logic
├── analysis_service.py    # Quality analysis logic
└── configuration_service.py # Configuration management
```

**Benefits:**
- CLI becomes thin wrapper around services
- Business logic reusable in SDK
- Easier testing (mock services)
- Better separation of concerns

### Lazy Loading Pattern

```python
# Lazy load heavy dependencies
def get_pandas():
    """Lazy import pandas."""
    import pandas as pd
    return pd

def get_sqlalchemy():
    """Lazy import SQLAlchemy."""
    from sqlalchemy import create_engine
    return create_engine
```

### Streaming Pattern

```python
def read_excel_streaming(file_path: Path, chunk_size: int = 1000):
    """Read Excel file in chunks."""
    # Use openpyxl chunked reading
    # Process in batches to avoid memory issues
    pass
```

## Performance Targets

### Startup Time
- **Current:** ~2-3 seconds
- **Target:** <500ms for help command
- **Target:** <1 second for operations

### Memory Usage
- **Current:** Loads all dependencies (~200MB)
- **Target:** <50MB for simple operations
- **Target:** Progressive loading for heavy ops

### File Processing
- **Current:** Files >100MB cause crashes
- **Target:** Support files up to 1GB with streaming
- **Target:** Constant memory usage regardless of file size

## Implementation Plan

### Phase 1: Performance Quick Wins (P0)
1. Implement lazy loading for CLI imports
2. Add file size checks and streaming
3. Add caching for expensive operations

### Phase 2: UX Improvements (P0)
1. Enhance error messages
2. Add progress percentages
3. Add confirmation prompts

### Phase 3: Architecture Refactoring (P1)
1. Extract service layer
2. Refactor InteractiveWizard
3. Implement dependency injection

### Phase 4: Advanced Features (P2)
1. Add cancellation support
2. Add parallel processing for multiple files
3. Add incremental progress reporting

## Testing Requirements

### Performance Tests
```python
def test_startup_time_performance()
def test_memory_usage_small_files()
def test_large_file_streaming()
def test_cache_effectiveness()
def test_concurrent_operations()
```

### UX Tests
```python
def test_error_message_clarity()
def test_progress_indication()
def test_confirmation_prompts()
def test_cancellation_support()
```

## Dependencies

### Required Packages
- `tqdm` - Progress bars
- `click` - Better CLI interactions (consider replacing Typer or enhance)
- Existing packages (no new dependencies for basic improvements)

## Breaking Changes

### Potential Breaking Changes
- Lazy loading may affect import paths
- Service layer extraction changes internal APIs
- These are internal refactors, not public API changes

### Migration Path
- Public API remains unchanged
- Internal reorganization is transparent to users

## Related Issues

- Depends on: #004 Extract Hardcoded Configuration
- Related to: #003 Improve Error Handling
- Enables: Better performance and usability
- Improves: Overall code quality

## Files to Create

- `excel_to_sql/services/` (new directory)
- `excel_to_sql/services/__init__.py`
- `excel_to_sql/services/import_service.py`
- `excel_to_sql/services/export_service.py`
- `excel_to_sql/services/analysis_service.py`

## Files to Modify

- `excel_to_sql/cli.py` - Refactor to use services
- `excel_to_sql/ui/interactive.py` - Separate concerns
- `excel_to_sql/__init__.py` - Lazy imports
- `excel_to_sql/sdk/client.py` - Use services

## Success Metrics

### Performance
- Startup time <500ms (help command)
- Memory usage <50MB (idle)
- Can process 1GB files without crashing

### User Experience
- Clear error messages with suggestions
- Progress indication with percentages
- Confirmation for destructive operations
- Cancellation support for long operations

### Architecture
- CLI <500 lines (from 1000+)
- Services layer with clear responsibilities
- >90% testability of business logic
- Lazy loading of heavy dependencies
