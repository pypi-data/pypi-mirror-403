# Maybe Monad

The Maybe monad (also known as Option) represents optional values - computations that may return a value or nothing. It's a functional alternative to using None and nullable types.

## Overview

### Current Approach (Nullable with None)

The current codebase uses nullable values with None checks:

```python
# excel_to_sql/sdk/client.py (lines 50-95)
class ExcelToSqlite:
    def __init__(self, project_path: Optional[Path] = None) -> None:
        if project_path is None:
            project_path = Path.cwd()
        self._project_path = Path(project_path)
        self._project: Optional[Project] = None
        self._database: Optional[Database] = None

    @property
    def database(self) -> Database:
        """Get database instance."""
        if self._database is None:  # None check
            self._database = self.project.database
        return self._database

    def get_mapping(self, type_name: str) -> Optional[dict]:
        """Get mapping or None if not found"""
        return self.mappings.get(type_name)
```

**Problems:**
- None checks scattered throughout code
- Unclear if function can return None
- No type safety for None cases
- Easy to forget None check → AttributeError/TypeError
- Cannot chain operations that might return None

### Functional Approach (Maybe Monad)

```python
class ExcelToSqliteFunctional:
    """Functional SDK client using Maybe monad"""

    def __init__(self, project_path: Union[Path, None] = None):
        self._project_path = Maybe.from_nullable(project_path).get_or_else(Path.cwd())
        self._project: Maybe[Project] = Maybe.nothing()
        self._database: Maybe[Database] = Maybe.nothing()

    @property
    def database(self) -> Maybe[Database]:
        """Get database instance - functional approach"""
        return self._database.or_else(
            lambda: self.project.map(lambda p: p.database)
        )

    def get_mapping(self, type_name: str) -> Maybe[dict]:
        """Get mapping as Maybe"""
        return Maybe.from_nullable(self.mappings.get(type_name))

    def get_table_schema(self, table_name: str) -> Maybe[dict]:
        """Get table schema with composed operations"""
        return (
            self.database
            .flat_map(lambda db: Maybe.from_nullable(db.get_table(table_name)))
            .map(lambda table: table.columns)
            .map(lambda cols: {"name": table_name, "columns": cols})
        )

    def import_excel_safe(
        self,
        file_path: Path,
        type_name: str
    ) -> Result[dict, str]:
        """Import combining Maybe and Result"""
        return (
            self.get_mapping(type_name)
            .to_result(lambda: f"Mapping '{type_name}' not found")
            .flat_map(lambda mapping: self._execute_import(file_path, mapping))
        )
```

**Benefits:**
- Explicit optional nature in type signature
- Safe chaining of nullable operations
- No NullPointerException equivalent
- Forced handling of empty case
- Composable operations

## Implementation

### Core Maybe Monad

```python
from typing import Callable, TypeVar, Generic, Union, Any
from dataclasses import dataclass
from functools import reduce

T = TypeVar('T')
U = TypeVar('U')

class Maybe(Generic[T]):
    """
    Maybe monad for handling optional values without None.

    Represents either Some(value) or Nothing.
    """

    def __init__(self, value: Union[T, None]):
        self._value = value
        self._is_present = value is not None

    # ========== Constructors ==========

    @staticmethod
    def some(value: T) -> "Maybe[T]":
        """Create a Maybe with a value"""
        if value is None:
            raise ValueError("Maybe.some() requires non-None value")
        return Maybe(value)

    @staticmethod
    def nothing() -> "Maybe[T]":
        """Create an empty Maybe"""
        return Maybe(None)

    @staticmethod
    def from_nullable(value: Union[T, None]) -> "Maybe[T]":
        """Create Maybe from nullable value"""
        return Maybe(value)

    @staticmethod
    def from_condition(
        condition: bool,
        if_true: T,
        if_false: Union[T, None] = None
    ) -> "Maybe[T]":
        """Create Maybe based on condition"""
        return Maybe(if_true if condition else if_false)

    # ========== Query ==========

    def is_present(self) -> bool:
        """Check if value exists"""
        return self._is_present

    def is_empty(self) -> bool:
        """Check if value is absent"""
        return not self._is_present

    # ========== Transform ==========

    def map(self, fn: Callable[[T], U]) -> "Maybe[U]":
        """
        Transform value if present.

        If Maybe is Some, applies fn to value.
        If Maybe is Nothing, returns Nothing.
        """
        if self._is_present:
            try:
                return Maybe.some(fn(self._value))
            except Exception:
                return Maybe.nothing()
        return Maybe.nothing()

    def flat_map(self, fn: Callable[[T], "Maybe[U]"]) -> "Maybe[U]":
        """
        Chain Maybe-returning operations.

        If Maybe is Some, applies fn which returns new Maybe.
        If Maybe is Nothing, returns Nothing.
        """
        if self._is_present:
            try:
                return fn(self._value)
            except Exception:
                return Maybe.nothing()
        return Maybe.nothing()

    and_then = flat_map  # Alias

    # ========== Filter ==========

    def filter(self, predicate: Callable[[T], bool]) -> "Maybe[T]":
        """
        Keep value only if predicate matches.

        Returns Nothing if predicate returns False.
        """
        if self._is_present and predicate(self._value):
            return Maybe.some(self._value)
        return Maybe.nothing()

    # ========== Alternatives ==========

    def or_else(self, supplier: Callable[[], "Maybe[T]"]) -> "Maybe[T]"]:
        """
        Provide alternative Maybe if empty.

        If Maybe is Some, returns self.
        If Maybe is Nothing, calls supplier() for alternative.
        """
        if self._is_present:
            return self
        return supplier()

    def get_or_else(self, default: T) -> T:
        """Get value or return default"""
        return self._value if self._is_present else default

    def get_or_raise(self, error: Exception = None) -> T:
        """
        Get value or raise exception.

        Use at application boundaries, not in internal logic.
        """
        if self._is_present:
            return self._value

        if error:
            raise error
        raise ValueError("Maybe.nothing() has no value")

    def get_or_call(self, supplier: Callable[[], T]) -> T:
        """Get value or call supplier for default"""
        return self._value if self._is_present else supplier()

    # ========== Side Effects ==========

    def if_present(self, consumer: Callable[[T], None]) -> None:
        """Execute action if value exists"""
        if self._is_present:
            consumer(self._value)

    def if_empty(self, action: Callable[[], None]) -> None:
        """Execute action if no value exists"""
        if not self._is_present:
            action()

    # ========== Conversion ==========

    def to_list(self) -> list[T]:
        """Convert to list (0 or 1 elements)"""
        return [self._value] if self._is_present else []

    def to_tuple(self) -> tuple[bool, Union[T, None]]:
        """Convert to (is_present, value) tuple"""
        return (self._is_present, self._value)

    def to_result(
        self,
        error_if_none: Callable[[], E]
    ) -> "Result[T, E]":
        """Convert Maybe to Result"""
        from .result_monad import Result

        if self._is_present:
            return Result.ok(self._value)
        return Result.fail(error_if_none())

    def to_either(
        self,
        left_if_none: Callable[[], L]
    ) -> "Either[L, T]":
        """Convert Maybe to Either"""
        from .either_monad import Either

        if self._is_present:
            return Either.right(self._value)
        return Either.left(left_if_none())

    # ========== Collection Operations ==========

    def map_or_default(
        self,
        fn: Callable[[T], U],
        default: U
    ) -> U:
        """Map or return default"""
        if self._is_present:
            return fn(self._value)
        return default

    # ========== Representation ==========

    def __repr__(self) -> str:
        if self._is_present:
            return f"Maybe.some({repr(self._value)})"
        return "Maybe.nothing()"

    def __str__(self) -> str:
        if self._is_present:
            return f"Some({self._value})"
        return "Nothing"

    def __eq__(self, other: "Maybe[T]") -> bool:
        if not isinstance(other, Maybe):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __iter__(self):
        """Allow iteration over 0 or 1 values"""
        if self._is_present:
            yield self._value
```

## Usage Patterns

### 1. Safe Chaining

```python
def get_user_email(user_id: int) -> Maybe[str]:
    return (
        get_user(user_id)
        .flat_map(lambda user: get_user_profile(user.id))
        .map(lambda profile: profile.email)
        .filter(lambda email: "@" in email)
    )
```

### 2. Default Values

```python
def get_config_value(key: str) -> Maybe[str]:
    return Maybe.from_nullable(config.get(key))

timeout = get_config_value("timeout").get_or_else("30s")
```

### 3. Conditional Operations

```python
def find_active_user(user_id: int) -> Maybe[User]:
    return (
        get_user(user_id)
        .filter(lambda u: u.is_active)
    )
```

### 4. Side Effects on Presence

```python
def send_notification_if_exists(user_id: int) -> None:
    get_user_email(user_id).if_present(lambda email:
        send_email(email, "Welcome!")
    )
```

### 5. Collection Conversion

```python
# Maybe with 0 or 1 elements can be used in for loops
for email in get_user_email(user_id):
    print(email)  # Only executes if email exists
```

## Examples from excel-to-sqlite

### Mapping Lookup

```python
# excel_to_sql/functional/mappings.py

def get_column_mapping(
    mappings: dict,
    source_column: str
) -> Maybe[ColumnMapping]:
    """Get column mapping if exists"""
    return (
        Maybe.from_nullable(mappings.get("column_mappings"))
        .flat_map(lambda cols: Maybe.from_nullable(cols.get(source_column)))
    )

def get_target_column(
    mappings: dict,
    source_column: str
) -> Maybe[str]:
    """Get target column name"""
    return get_column_mapping(mappings, source_column)\
        .map(lambda mapping: mapping.target)
```

### Database Queries

```python
# excel_to_sql/functional/database.py

def get_table_by_name(name: str) -> Maybe[Table]:
    """Get table if exists"""
    return Maybe.from_nullable(database.get_table(name))

def get_primary_key(table_name: str) -> Maybe[str]:
    """Get primary key column"""
    return (
        get_table_by_name(table_name)
        .flat_map(lambda table: Maybe.from_nullable(table.primary_key))
    )

def get_foreign_keys(table_name: str) -> Maybe[list[ForeignKey]]:
    """Get foreign keys for table"""
    return (
        get_table_by_name(table_name)
        .map(lambda table: table.foreign_keys)
        .filter(lambda fks: len(fks) > 0)
    )
```

### Configuration Access

```python
# excel_to_sql/functional/config.py

def get_mapping_config(project: Project, type_name: str) -> Maybe[dict]:
    """Get mapping configuration"""
    return (
        Maybe.from_nullable(project.mappings)
        .flat_map(lambda mappings: Maybe.from_nullable(mappings.get(type_name)))
    )

def get_validation_rules(
    project: Project,
    type_name: str,
    column: str
) -> Maybe[list[ValidationRule]]:
    """Get validation rules for column"""
    return (
        get_mapping_config(project, type_name)
        .flat_map(lambda config: Maybe.from_nullable(config.get("validations")))
        .flat_map(lambda validations: Maybe.from_nullable(validations.get(column)))
    )
```

### Composed Operations

```python
# excel_to_sql/functional/import.py

def prepare_import_context(
    project: Project,
    file_path: Path,
    type_name: str
) -> Maybe[ImportContext]:
    """Prepare all data needed for import"""
    return (
        Maybe.from_nullable(ExcelFile(file_path))
        .filter(lambda ef: ef.exists())
        .flat_map(lambda ef: get_mapping_config(project, type_name)
                  .map(lambda mapping: (ef, mapping)))
        .map(lambda tuple: ImportContext(
            excel_file=tuple[0],
            mapping=tuple[1],
            project=project
        ))
    )
```

## Maybe Combinators

### Lift

```python
def lift_maybe(fn: Callable[[T], U]) -> Callable[[Maybe[T]], Maybe[U]]:
    """Lift function to operate on Maybe"""
    return lambda maybe: maybe.map(fn)

# Usage
uppercase = lift_maybe(str.upper)
Maybe.some("hello").pipe(uppercase)  # Maybe.some("HELLO")
```

### Map2 (combining two Maybes)

```python
def map2(
    maybe1: Maybe[T1],
    maybe2: Maybe[T2],
    fn: Callable[[T1, T2], U]
) -> Maybe[U]:
    """Combine two Maybes"""
    if maybe1.is_present() and maybe2.is_present():
        return Maybe.some(fn(maybe1._value, maybe2._value))
    return Maybe.nothing()

# Usage
full_name = map2(
    get_first_name(user_id),
    get_last_name(user_id),
    lambda first, last: f"{first} {last}"
)
```

### Sequence

```python
def sequence(maybes: list[Maybe[T]]) -> Maybe[list[T]]:
    """
    Convert list of Maybes to Maybe of list.

    Returns Maybe[list[T]] if all Maybes are Some.
    Returns Nothing if any Maybe is Nothing.
    """
    result = []
    for maybe in maybes:
        if maybe.is_empty():
            return Maybe.nothing()
        result.append(maybe._value)
    return Maybe.some(result)

# Usage
emails = sequence([
    get_user_email(1),
    get_user_email(2),
    get_user_email(3),
])
```

### Traverse

```python
def traverse(
    items: list[T],
    fn: Callable[[T], Maybe[U]]
) -> Maybe[list[U]]:
    """
    Apply Maybe-returning function to each item in list.

    Returns Maybe[list[U]] if all calls succeed.
    Returns Nothing if any call fails.
    """
    return sequence([fn(item) for item in items])

# Usage
user_ids = [1, 2, 3]
emails = traverse(user_ids, get_user_email)
```

## Best Practices

### DO
- **Use Maybe for truly optional values** - Data that may or may not exist
- **Chain operations with flat_map** - Compose multiple nullable operations
- **Use filter for conditions** - Narrow down valid values
- **Provide meaningful defaults** - With get_or_else for business logic
- **Convert to Result at boundaries** - To provide error context

### DON'T
- **Don't use Maybe for error handling** - Use Result instead
- **Don't use get_or_raise internally** - Reserve for app boundaries
- **Don't wrap everything** - Not every value needs to be in Maybe
- **Don't forget to handle empty case** - Always consider Nothing branch
- **Don't nest Maybes** - Use flat_map to chain instead

### When to Use Maybe

```
✅ Dictionary get() operations
✅ Optional configuration values
✅ Search operations (find by id)
✅ Nullable database columns
✅ Optional function parameters
✅ Filtering operations

❌ Error handling (use Result)
❌ System failures (use Result)
❌ Validation with messages (use Validation/Result)
❌ Boolean conditions (use bool)
```

## Testing

### Testing Some Case

```python
def test_get_column_mapping_found():
    mappings = {
        "column_mappings": {
            "name": {"target": "product_name", "type": "string"}
        }
    }

    result = get_column_mapping(mappings, "name")

    assert result.is_present()
    assert result._value.target == "product_name"
```

### Testing Nothing Case

```python
def test_get_column_mapping_not_found():
    mappings = {"column_mappings": {}}

    result = get_column_mapping(mappings, "name")

    assert result.is_empty()
```

### Testing Chained Operations

```python
def test_get_primary_key_chain():
    result = get_primary_key("products")

    assert result.is_present()
    assert result._value == "id"
```

## Comparison with Other Languages

```
Haskell: Maybe a
Scala:   Option[A]
Rust:    Option<T>
Java:    Optional<T> (Java 8+)
C#:      Nullable<T> or Option<T> (System.CommandLine)
Swift:   Optional<T> (written as T?)
TypeScript: T | null
```

## Further Reading

- [Returns Library - Maybe](https://returns.readthedocs.io/en/latest/pages/maybe.html)
- [Rust Option Documentation](https://doc.rust-lang.org/std/option/)
- [Scala Option Documentation](https://www.scala-lang.org/api/current/scala/Option.html)
- [Maybe Monad in Haskell](https://hackage.haskell.org/package/base/docs/Data-Maybe.html)
