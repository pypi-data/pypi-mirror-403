# Result/Either Monad

The Result monad (also known as Either) provides explicit error handling without exceptions. It represents a computation that can either succeed with a value or fail with an error.

## Overview

### Current Approach (Imperative)

The current codebase uses exceptions for error handling:

```python
# excel_to_sql/cli.py (lines 65-206)
@app.command("import")
def import_cmd(excel_path: str, type: str):
    path = Path(excel_path)

    try:
        if not path.exists():
            console.print(f"[red]Error:[/red] File not found: {excel_path}")
            raise Exit(1)

        if path.suffix.lower() not in {".xlsx", ".xls"}:
            console.print(f"[red]Error:[/red] Not an Excel file: {excel_path}")
            raise Exit(1)

        project = Project.from_current_directory()
        # ... more operations

    except FileNotFoundError:
        console.print(f"[red]Error:[/red] File not found: {excel_path}")
        raise Exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise Exit(1)
    except Exception as e:
        console.print(f"[red]Error:[/red] Import failed: {e}")
        raise Exit(1)
```

**Problems:**
- Error paths hidden in exception handlers
- Difficult to compose multiple validation steps
- Exceptions are implicit in function signatures
- Hard to track all possible error cases
- Control flow via exceptions (anti-pattern)

### Functional Approach (Result Monad)

```python
# Pure validation functions
def validate_file_exists(path: Path) -> Result[Path, str]:
    if not path.exists():
        return Result.fail(f"File not found: {path}")
    return Result.ok(path)

def validate_excel_extension(path: Path) -> Result[Path, str]:
    if path.suffix.lower() not in {".xlsx", ".xls"}:
        return Result.fail(f"Not an Excel file: {path}")
    return Result.ok(path)

def validate_project_exists() -> Result[Project, str]:
    try:
        project = Project.from_current_directory()
        return Result.ok(project)
    except Exception as e:
        return Result.fail(f"Not an excel-to-sql project: {e}")

# Composition using flat_map (and_then)
def validate_import_request(excel_path: str, type_name: str) -> Result[tuple, str]:
    path = Path(excel_path)

    return (
        validate_file_exists(path)
        .and_then(validate_excel_extension)
        .and_then(lambda _: validate_project_exists())
        .and_then(lambda project: validate_mapping_exists(project, type_name)
                  .map(lambda mapping: (path, project, mapping)))
    )

# Usage in CLI
@app.command("import")
def import_cmd(excel_path: str, type: str):
    validation_result = validate_import_request(excel_path, type)

    if validation_result.is_failure():
        console.print(f"[red]Error:[/red] {validation_result._value.error}")
        raise Exit(1)

    # Safe unpacking after validation
    path, project, mapping = validation_result._value.value
    # Continue with import...
```

**Benefits:**
- Error paths explicit in type signature
- Easy composition of validation steps
- All error cases visible upfront
- No control flow via exceptions
- Testable without special exception handling

## Implementation

### Core Result Monad

```python
from typing import Callable, TypeVar, Generic, Union, Any
from dataclasses import dataclass
from functools import wraps

T = TypeVar('T')  # Success type
E = TypeVar('E')  # Error type
U = TypeVar('U')

@dataclass
class Success(Generic[T]):
    """Success case of Result monad"""
    value: T

@dataclass
class Failure(Generic[E]):
    """Failure case of Result monad"""
    error: E

class Result(Generic[T, E]):
    """
    Result monad for error handling without exceptions.

    Represents either Success(value) or Failure(error).
    """
    def __init__(self, value: Union[Success[T], Failure[E]]):
        self._value = value

    # ========== Constructors ==========

    @staticmethod
    def ok(value: T) -> "Result[T, E]":
        """Create a successful Result"""
        return Result(Success(value))

    @staticmethod
    def fail(error: E) -> "Result[T, E]":
        """Create a failed Result"""
        return Result(Failure(error))

    @staticmethod
    def from_exception(fn: Callable[..., T]) -> Callable[..., "Result[T, str]":
        """Wrap function that may raise exception"""
        @wraps(fn)
        def wrapper(*args, **kwargs) -> Result[T, str]:
            try:
                return Result.ok(fn(*args, **kwargs))
            except Exception as e:
                return Result.fail(str(e))
        return wrapper

    @staticmethod
    def from_optional(value: Union[T, None], error: E) -> "Result[T, E]":
        """Convert optional value to Result"""
        if value is None:
            return Result.fail(error)
        return Result.ok(value)

    # ========== Query ==========

    def is_success(self) -> bool:
        """Check if Result is successful"""
        return isinstance(self._value, Success)

    def is_failure(self) -> bool:
        """Check if Result is failed"""
        return isinstance(self._value, Failure)

    # ========== Transform ==========

    def map(self, fn: Callable[[T], U]) -> "Result[U, E]":
        """
        Transform success value, ignoring failures.

        If Result is Success, applies fn to value.
        If Result is Failure, passes through unchanged.
        """
        if isinstance(self._value, Success):
            try:
                return Result.ok(fn(self._value.value))
            except Exception as e:
                return Result.fail(str(e))
        return Result(self._value)

    def flat_map(self, fn: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        """
        Chain Result-returning operations.

        If Result is Success, applies fn which returns new Result.
        If Result is Failure, passes through unchanged.
        """
        if isinstance(self._value, Success):
            try:
                return fn(self._value.value)
            except Exception as e:
                return Result.fail(str(e))
        return Result(self._value)

    # Alias for flat_map - more readable in chains
    and_then = flat_map

    # ========== Recovery ==========

    def or_else(self, fn: Callable[[E], "Result[T, E]"]) -> "Result[T, E]":
        """
        Recover from failure.

        If Result is Failure, applies fn to error.
        If Result is Success, passes through unchanged.
        """
        if isinstance(self._value, Failure):
            return fn(self._value.error)
        return Result(self._value)

    def recover(self, default: T) -> T:
        """Get value or return default on failure"""
        if isinstance(self._value, Success):
            return self._value.value
        return default

    def get_or_raise(self, error: Exception = None) -> T:
        """
        Get value or raise exception.

        Use this at the boundary of your application (e.g., CLI entry point).
        Avoid using in internal logic.
        """
        if isinstance(self._value, Success):
            return self._value.value

        if error:
            raise error
        raise ValueError(self._value.error)

    # ========== Bifunctor ==========

    def map_error(self, fn: Callable[[E], E]) -> "Result[T, E]":
        """Transform error value"""
        if isinstance(self._value, Failure):
            return Result.fail(fn(self._value.error))
        return Result(self._value)

    def swap(self) -> "Result[E, T]":
        """Swap success and error cases"""
        if isinstance(self._value, Success):
            return Result.fail(self._value.value)
        return Result.ok(self._value.error)

    # ========== Conversion ==========

    def to_maybe(self) -> "Maybe[T]":
        """Convert Result to Maybe (losing error information)"""
        from .maybe_monad import Maybe
        if isinstance(self._value, Success):
            return Maybe.some(self._value.value)
        return Maybe.nothing()

    def to_tuple(self) -> tuple[bool, Union[T, None], Union[E, None]]:
        """
        Convert to (is_success, value, error) tuple.

        Useful for pattern matching:
        is_success, value, error = result.to_tuple()
        """
        if isinstance(self._value, Success):
            return (True, self._value.value, None)
        return (False, None, self._value.error)

    # ========== Representation ==========

    def __repr__(self) -> str:
        if isinstance(self._value, Success):
            return f"Result.ok({repr(self._value.value)})"
        return f"Result.fail({repr(self._value.error)})"

    def __str__(self) -> str:
        if isinstance(self._value, Success):
            return f"Success: {self._value.value}"
        return f"Failure: {self._value.error}"

    def __eq__(self, other: "Result[T, E]") -> bool:
        if not isinstance(other, Result):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)
```

## Usage Patterns

### 1. Validation Pipeline

```python
def validate_import_request(excel_path: str, type_name: str) -> Result[tuple, str]:
    """Chain multiple validations"""
    path = Path(excel_path)

    return (
        validate_file_exists(path)
        .and_then(validate_excel_extension)
        .and_then(lambda _: validate_project_exists())
        .and_then(lambda project: validate_mapping_exists(project, type_name)
                  .map(lambda mapping: (path, project, mapping)))
    )
```

### 2. Error Recovery

```python
def load_config_with_default(path: Path) -> Result[dict, str]:
    """Load config or use default"""
    return (
        load_config(path)
        .or_else(lambda error: Result.ok(get_default_config()))
    )
```

### 3. Combining Results

```python
def validate_all(data: dict) -> Result[ValidatedData, list[str]]:
    """Combine multiple validations, accumulating errors"""
    errors = []

    name_result = validate_name(data.get("name"))
    email_result = validate_email(data.get("email"))
    age_result = validate_age(data.get("age"))

    results = [name_result, email_result, age_result]

    # Collect all errors
    for result in results:
        if result.is_failure():
            errors.append(result._value.error)

    if errors:
        return Result.fail(errors)

    # All successful - extract values
    return Result.ok(ValidatedData(
        name=name_result._value.value,
        email=email_result._value.value,
        age=age_result._value.value,
    ))
```

### 4. Pattern Matching

```python
def handle_result(result: Result[Data, str]) -> str:
    """Handle Result using pattern matching"""
    is_success, value, error = result.to_tuple()

    if is_success:
        return f"Success: {value}"
    else:
        return f"Error: {error}"
```

### 5. Exception Wrapping

```python
@Result.from_exception
def read_file(path: Path) -> str:
    """Automatically wraps exceptions in Result"""
    with open(path) as f:
        return f.read()

# Usage
result = read_file("data.txt")
if result.is_failure():
    print(f"Failed to read: {result._value.error}")
```

## Examples from excel-to-sqlite

### File Validation

```python
# excel_to_sql/functional/validation.py

def validate_excel_file(path: Path) -> Result[Path, str]:
    """Validate Excel file"""
    return (
        validate_file_exists(path)
        .and_then(validate_not_directory)
        .and_then(validate_file_extension)
        .and_then(validate_file_readable)
    )

def validate_file_exists(path: Path) -> Result[Path, str]:
    if not path.exists():
        return Result.fail(f"File not found: {path}")
    return Result.ok(path)

def validate_not_directory(path: Path) -> Result[Path, str]:
    if path.is_dir():
        return Result.fail(f"Path is a directory: {path}")
    return Result.ok(path)

def validate_file_extension(path: Path) -> Result[Path, str]:
    if path.suffix.lower() not in {".xlsx", ".xls"}:
        return Result.fail(f"Invalid file extension: {path}")
    return Result.ok(path)

def validate_file_readable(path: Path) -> Result[Path, str]:
    if not os.access(path, os.R_OK):
        return Result.fail(f"Permission denied: {path}")
    return Result.ok(path)
```

### Configuration Loading

```python
# excel_to_sql/functional/config.py

def load_mappings_config(path: Path) -> Result[MappingsConfig, str]:
    """Load and validate mappings configuration"""
    return (
        read_json_file(path)
        .flat_map(validate_json_structure)
        .flat_map(parse_mappings_config)
        .flat_map(validate_mappings_config)
    )

def read_json_file(path: Path) -> Result[dict, str]:
    """Read JSON file"""
    if not path.exists():
        return Result.fail(f"Config file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            return Result.ok(json.load(f))
    except json.JSONDecodeError as e:
        return Result.fail(f"Invalid JSON: {e}")
    except Exception as e:
        return Result.fail(f"Error reading file: {e}")

def validate_json_structure(data: dict) -> Result[dict, str]:
    """Validate JSON has required structure"""
    if "mappings" not in data:
        return Result.fail("Missing 'mappings' key")
    return Result.ok(data)

def parse_mappings_config(data: dict) -> Result[MappingsConfig, str]:
    """Parse mappings from JSON data"""
    try:
        return Result.ok(MappingsConfig.from_dict(data))
    except Exception as e:
        return Result.fail(f"Invalid mappings: {e}")
```

### Database Operations

```python
# excel_to_sql/functional/database.py

def upsert_data(
    table: str,
    data: pd.DataFrame,
    primary_key: list[str]
) -> Result[UpsertStats, str]:
    """Upsert data with Result error handling"""
    return (
        validate_table_exists(table)
        .flat_map(lambda _: validate_primary_key_columns(table, primary_key))
        .flat_map(lambda _: validate_dataframe_columns(data))
        .flat_map(lambda _: perform_upsert(table, data, primary_key))
    )

def perform_upsert(
    table: str,
    data: pd.DataFrame,
    primary_key: list[str]
) -> Result[UpsertStats, str]:
    """Perform upsert operation"""
    try:
        stats = _execute_upsert(table, data, primary_key)
        return Result.ok(stats)
    except DatabaseError as e:
        return Result.fail(f"Database error: {e}")
    except Exception as e:
        return Result.fail(f"Unexpected error: {e}")
```

## Best Practices

### DO
- **Use Result for operations that can fail** - File I/O, parsing, validation
- **Chain validations with and_then** - Compose multiple validation steps
- **Handle errors explicitly** - Never ignore a Result without checking
- **Provide meaningful error messages** - Help users understand what went wrong
- **Use at application boundaries** - Convert exceptions to Result at edges

### DON'T
- **Don't use Result for simple checks** - Use bool for straightforward conditions
- **Don't nest Results** - Use flat_map to chain instead
- **Don't ignore failures** - Always check is_failure before using value
- **Don't use get_or_raise internally** - Reserve for application entry points
- **Don't overuse** - Not every function needs to return Result

### When to Use Result

```
✅ File operations (read, write, validate)
✅ Network requests
✅ Parsing (JSON, XML, CSV)
✅ Validation with error messages
✅ Database operations
✅ External API calls
✅ Configuration loading

❌ Simple arithmetic (use try/except for overflow)
❌ List indexing (use Maybe for nullable values)
❌ Boolean conditions (use bool)
❌ Internal computations with assertions
```

## Testing

### Testing Success Cases

```python
def test_validate_file_exists_success():
    path = Path("/tmp/test.xlsx")
    # Mock path.exists() to return True

    result = validate_file_exists(path)

    assert result.is_success()
    assert result._value.value == path
```

### Testing Failure Cases

```python
def test_validate_file_exists_failure():
    path = Path("/tmp/test.xlsx")
    # Mock path.exists() to return False

    result = validate_file_exists(path)

    assert result.is_failure()
    assert "not found" in result._value.error
```

### Testing Chained Operations

```python
def test_validation_pipeline():
    result = validate_import_request("test.xlsx", "products")

    assert result.is_success()
    path, project, mapping = result._value.value
    assert path.name == "test.xlsx"
```

## Comparison with Other Languages

```
Haskell: Either Error a
Rust:    Result<T, E>
Scala:   Either[E, A]
Java:    Either<L, R> (Vavr)
C#:      Result<T, TError> (OneOf)
```

## Further Reading

- [Returns Library - Result](https://returns.readthedocs.io/en/latest/pages/result.html)
- [Rust Result Documentation](https://doc.rust-lang.org/std/result/)
- [Either Monad in Haskell](https://hackage.haskell.org/package/category-extras-0.52.0/docs/Control-Monad-Either.html)
