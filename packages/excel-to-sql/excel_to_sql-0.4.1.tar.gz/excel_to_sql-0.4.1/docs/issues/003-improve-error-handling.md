# Fix: Improve Error Handling in CLI

## Problem Description

The CLI contains multiple poor error handling patterns that make debugging difficult and can hide critical errors.

### Current Issues

#### 1. Bare Except Block
**Location:** `excel_to_sql/cli.py:295`

```python
except (EOFError, KeyboardInterrupt):
    pass
```

This is acceptable for user interruption, but the pattern is inconsistent.

#### 2. Generic Exception Handlers
**Location:** Throughout `excel_to_sql/cli.py`

Multiple instances of:
```python
except Exception as e:
    console.print(f"[red]Error:[/red] {e}")
```

**Problems:**
- Catches all exceptions including system errors
- No distinction between expected and unexpected errors
- Makes debugging difficult
- Can mask critical failures

#### 3. Inconsistent Error Message Format
Different parts of the code use different error message formats:
- `[red]Error:[/red] {message}`
- `[yellow]Warning:[/yellow] {message}`
- Plain print statements
- Mixed capitalization

## Impact

- **Debugging Difficulty:** Cannot trace error origins
- **Poor User Experience:** Generic error messages don't help users
- **Hidden Bugs:** System errors are swallowed
- **Inconsistent UX:** Different error styles across commands

## Current Examples of Poor Error Handling

### Example 1: Import Command
```python
try:
    # ... import logic ...
except Exception as e:
    console.print(f"[red]Error:[/red] {e}")
    raise Exit(1)
```

**Issues:**
- Catches SystemExit, KeyboardInterrupt, SystemExit
- No specific handling for expected errors (FileNotFound, PermissionError)
- No error recovery suggestions

### Example 2: Magic Command
```python
except Exception as e:
    console.print(f"[red]Error:[/red] {e}")
```

**Issues:**
- No re-raise, execution continues
- Errors are silently ignored
- User gets no actionable feedback

## Acceptance Criteria

### Must Have (P0)
- [ ] Remove all bare `except:` blocks
- [ ] Replace generic `except Exception:` with specific exception types
- [ ] Use specific exception types:
  - `FileNotFoundError` - Missing files
  - `PermissionError` - Access denied
  - `ValueError` - Invalid input
  - `pd.errors.EmptyDataError` - Empty Excel files
  - `pd.errors.ParserError` - Malformed files
  - `KeyError` - Missing configuration
  - `ValidationError` - Custom validation errors
- [ ] Add error recovery suggestions where appropriate
- [ ] Ensure all exceptions are either:
  - Logged with context
  - Re-raised with additional context
  - Handled gracefully with user feedback

### Should Have (P1)
- [ ] Create custom exception classes for common errors:
  - `ExcelFileError` - Excel file specific errors
  - `ConfigurationError` - Configuration issues
  - `ValidationError` - Data validation failures
  - `DatabaseError` - Database operation errors
- [ ] Add error context (file name, operation, parameters)
- [ ] Implement consistent error message format
- [ ] Add error codes for documentation

### Could Have (P2)
- [ ] Add error recovery mechanisms
- [ ] Implement retry logic for transient errors
- [ ] Add detailed error logging to file
- [ ] Create error handler utility class

## Proposed Error Handling Pattern

### Create Custom Exceptions

```python
# excel_to_sql/exceptions.py
class ExcelToSqlError(Exception):
    """Base exception for excel-to-sql errors."""

class ExcelFileError(ExcelToSqlError):
    """Raised when Excel file operations fail."""

class ConfigurationError(ExcelToSqlError):
    """Raised when configuration is invalid or missing."""

class ValidationError(ExcelToSqlError):
    """Raised when data validation fails."""

class DatabaseError(ExcelToSqlError):
    """Raised when database operations fail."""
```

### Improved Error Handling Pattern

```python
# Example for import command
try:
    excel_file = ExcelFile(path)
except FileNotFoundError:
    console.print(f"[red]Error:[/red] File not found: {path}")
    console.print("[dim]Tip: Check the file path and try again[/dim]")
    raise Exit(1)
except PermissionError:
    console.print(f"[red]Error:[/red] Permission denied: {path}")
    console.print("[dim]Tip: Check file permissions or run with appropriate access[/dim]")
    raise Exit(1)
except pd.errors.EmptyDataError:
    console.print(f"[red]Error:[/red] Excel file is empty: {path}")
    console.print("[dim]Tip: Ensure the file contains data in the first sheet[/dim]")
    raise Exit(1)
except pd.errors.ParserError as e:
    console.print(f"[red]Error:[/red] Invalid Excel file: {path}")
    console.print(f"[dim]Parser error: {e}[/dim]")
    console.print("[dim]Tip: Ensure the file is a valid .xlsx or .xls file[/dim]")
    raise Exit(1)
except Exception as e:
    # Log unexpected errors
    logger.exception(f"Unexpected error importing {path}")
    console.print(f"[red]Error:[/red] An unexpected error occurred")
    raise Exit(1)
```

## Testing Requirements

### Unit Tests
```python
def test_file_not_found_error()
def test_permission_denied_error()
def test_empty_excel_file_error()
def test_invalid_excel_format_error()
def test_configuration_missing_error()
def test_database_connection_error()
```

### Integration Tests
- Test error messages with various file states
- Test error handling with actual file system permissions
- Test error recovery suggestions

## Implementation Notes

### Priority Order

1. **Phase 1 (P0)** - Fix bare except and critical paths
   - Replace bare `except:` blocks
   - Add specific exceptions to import command
   - Add specific exceptions to magic command

2. **Phase 2 (P1)** - Create exception classes
   - Implement custom exception hierarchy
   - Add error context utilities

3. **Phase 3 (P2)** - Enhance error UX
   - Add error recovery suggestions
   - Implement consistent formatting

### Error Message Format

Adopt consistent format:
```
[red]Error:[/red] {brief_description}
[dim]Details: {error_details}[/dim]
[dim]Tip: {actionable_suggestion}[/dim]
```

## Breaking Changes

None. This improves error handling without changing public API.

## Related Issues

- Related to: #002 Missing QualityScorer Module
- Blocks: Better user experience
- Improves: Overall code quality

## References

- Current error handling locations:
  - `excel_to_sql/cli.py:295` - Bare except
  - `excel_to_sql/cli.py:100-145` - Import command errors
  - `excel_to_sql/cli.py:200-250` - Export command errors
  - `excel_to_sql/cli.py:450-500` - Magic command errors
