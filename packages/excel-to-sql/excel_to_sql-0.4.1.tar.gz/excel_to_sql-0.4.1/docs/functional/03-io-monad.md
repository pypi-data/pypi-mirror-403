# IO Monad

The IO monad represents side effects (I/O operations) as pure values, allowing explicit separation of pure logic from impure operations like file reading, database queries, and user interaction.

## Overview

### Current Approach (Direct Side Effects)

The current codebase mixes business logic with side effects:

```python
# excel_to_sql/entities/excel_file.py (lines 140-180)
class ExcelFile:
    def get_content_hash(self, sheet_name: Optional[str] = None) -> str:
        """Direct I/O - impure function"""
        cache_key = sheet_name or ""

        if cache_key not in self._hash_cache:
            df = pd.read_excel(self.path, sheet_name=sheet_name)  # Side effect!
            self._hash_cache[cache_key] = self._compute_hash(df)  # Mutation!

        return self._hash_cache[cache_key]

    def read(self, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Direct file reading - side effect"""
        return pd.read_excel(self.path, sheet_name=sheet_name)
```

**Problems:**
- Side effects hidden in function signatures
- Difficult to test (need to mock file system)
- Cannot reason about functions in isolation
- Side effects can't be composed or deferred
- Mutable cache complicates testing

### Functional Approach (IO Monad)

```python
@dataclass(frozen=True)
class ExcelFile:
    """Immutable Excel file with IO operations"""
    path: Path

    # Pure computations (no I/O)
    def exists(self) -> bool:
        """Pure: check if file exists"""
        return self.path.exists()

    def is_excel_file(self) -> bool:
        """Pure: check file extension"""
        return self.path.suffix.lower() in {".xlsx", ".xls"}

    def compute_hash(self, df: pd.DataFrame) -> str:
        """Pure: compute hash of DataFrame"""
        import hashlib
        content_str = df.to_string(index=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    # IO operations - explicit about side effects
    def read(self, sheet_name: Union[str, None] = None) -> IO[pd.DataFrame]:
        """IO action: read Excel file"""
        def read_effect():
            if not self.exists():
                raise FileNotFoundError(f"File not found: {self.path}")

            if not self.is_excel_file():
                raise ValueError(f"Not an Excel file: {self.path}")

            actual_sheet = 0 if sheet_name is None else sheet_name
            return pd.read_excel(self.path, sheet_name=actual_sheet, engine="openpyxl")

        return IO(read_effect)

    def get_content_hash(self, sheet_name: Union[str, None] = None) -> IO[str]:
        """IO action: get content hash"""
        return (
            self.read(sheet_name)
            .map(self.compute_hash)
        )

    def get_content_hash_cached(self, sheet_name: Union[str, None] = None) -> IO[str]:
        """IO action with caching"""
        return self.get_content_hash(sheet_name).memoize()

# Composition of IO operations
def process_excel_file(file_path: Path) -> IO[dict]:
    """Pure function returning IO action"""
    excel_file = ExcelFile(file_path)

    return (
        excel_file.validate()
        .flat_map(lambda is_valid: (
            excel_file.read() if is_valid else IO.pure(pd.DataFrame())
        ))
        .map(lambda df: ({
            "rows": len(df),
            "columns": len(df.columns),
            "hash": excel_file.compute_hash(df)
        }))
    )
```

**Benefits:**
- Side effects explicit in type signature
- Pure business logic testable without I/O
- Composable I/O operations
- Deferred execution (actions are values)
- Easy to mock IO for testing

## Implementation

### Core IO Monad

```python
from typing import Callable, TypeVar, Generic, Any
from threading import Lock
from functools import wraps

T = TypeVar('T')
U = TypeVar('U')

class IO(Generic[T]):
    """
    IO monad for representing side effects as pure values.

    An IO[T] is a description of a computation that produces T
    when executed. It doesn't perform the side effect until
    unsafe_run() is called.

    This allows separating pure logic from side effects while
    keeping effects explicit in the type system.
    """

    def __init__(self, effect: Callable[[], T]):
        """
        Create IO from a function.

        The function is NOT executed until unsafe_run() is called.
        """
        self._effect = effect

    # ========== Execution ==========

    def unsafe_run(self) -> T:
        """
        Execute the IO action.

        "unsafe" because it performs side effects.
        Should only be called at application boundaries (main, CLI entry points).
        """
        return self._effect()

    # ========== Constructors ==========

    @staticmethod
    def pure(value: T) -> "IO[T]":
        """Lift pure value into IO (no side effect)"""
        return IO(lambda: value)

    @staticmethod
    def delay(effect: Callable[[], T]) -> "IO[T]":
        """Delay computation (same as IO constructor)"""
        return IO(effect)

    @staticmethod
    def now(value: T) -> "IO[T]":
        """Eagerly evaluated value (same as pure)"""
        return IO.pure(value)

    @staticmethod
    def from_exception(fn: Callable[..., T]) -> Callable[..., "IO[Result[T, Exception]]"]:
        """Wrap exception-throwing function"""
        @wraps(fn)
        def wrapper(*args, **kwargs) -> IO[Result[T, Exception]]:
            def inner():
                try:
                    return Result.ok(fn(*args, **kwargs))
                except Exception as e:
                    return Result.fail(e)
            return IO(inner)
        return wrapper

    # ========== Transform ==========

    def map(self, fn: Callable[[T], U]) -> "IO[U]":
        """
        Transform the result of IO.

        Returns new IO that applies fn to the result.
        """
        return IO(lambda: fn(self.unsafe_run()))

    def flat_map(self, fn: Callable[[T], "IO[U]"]) -> "IO[U]":
        """
        Chain IO operations.

        Returns new IO that runs self, then applies fn to result.
        """
        def run():
            result = self.unsafe_run()
            return fn(result).unsafe_run()
        return IO(run)

    and_then = flat_map  # Alias for readability

    # ========== Flattening ==========

    def flatten(self: "IO[IO[T]]") -> "IO[T]":
        """Flatten nested IO"""
        return self.flat_map(lambda x: x)

    # ========== Error Handling ==========

    def recover(self, fn: Callable[[Exception], T]) -> "IO[T]":
        """Catch exceptions and recover"""
        def run():
            try:
                return self.unsafe_run()
            except Exception as e:
                return fn(e)
        return IO(run)

    def recover_with(self, fn: Callable[[Exception], "IO[T]"]) -> "IO[T]":
        """Catch exceptions and recover with IO"""
        def run():
            try:
                return self.unsafe_run()
            except Exception as e:
                return fn(e).unsafe_run()
        return IO(run)

    def attempt(self) -> "IO[Result[T, Exception]]":
        """Convert IO to IO of Result"""
        from .result_monad import Result

        def run():
            try:
                return Result.ok(self.unsafe_run())
            except Exception as e:
                return Result.fail(e)
        return IO(run)

    # ========== Concurrency ==========

    def par_zip(self, other: "IO[U]") -> "IO[tuple[T, U]]":
        """Run two IO operations in parallel, combine results"""
        from concurrent.futures import ThreadPoolExecutor

        def run():
            with ThreadPoolExecutor(max_workers=2) as executor:
                future1 = executor.submit(self.unsafe_run)
                future2 = executor.submit(other.unsafe_run)
                return (future1.result(), future2.result())
        return IO(run)

    # ========== Caching ==========

    def memoize(self) -> "IO[T]":
        """
        Cache result of first execution.

        Subsequent calls return cached result without re-executing.
        Thread-safe.
        """
        cache: list = []
        lock = Lock()

        def run():
            with lock:
                if not cache:
                    cache.append(self.unsafe_run())
                return cache[0]

        return IO(run)

    def memoize_unsafe(self) -> "IO[T]":
        """Non-thread-safe version of memoize (faster)"""
        cache: list = []

        def run():
            if not cache:
                cache.append(self.unsafe_run())
            return cache[0]

        return IO(run)

    # ========== Side Effects ==========

    def and_then_discard(self, other: "IO[Any]") -> "IO[T]":
        """Sequence IO, keeping first result"""
        return self.flat_map(lambda result: other.map(lambda _: result))

    def tap(self, fn: Callable[[T], None]) -> "IO[T]":
        """Call function with result, return result"""
        def run():
            result = self.unsafe_run()
            fn(result)
            return result
        return IO(run)

    # ========== Iteration ==========

    @staticmethod
    def sequence(actions: list["IO[T]"]) -> "IO[list[T]]":
        """
        Execute list of IO actions in sequence, collect results.

        Returns IO[list[T]] containing all results.
        """
        def run():
            return [action.unsafe_run() for action in actions]
        return IO(run)

    @staticmethod
    def traverse(items: list[T], fn: Callable[[T], "IO[U]"]) -> "IO[list[U]]":
        """
        Apply IO-returning function to each item.

        Returns IO[list[U]] containing all results.
        """
        return IO.sequence([fn(item) for item in items])

    @staticmethod
    def traverse_parallel(
        items: list[T],
        fn: Callable[[T], "IO[U]"]
    ) -> "IO[list[U]]":
        """Apply function in parallel, collect results"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        def run():
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(lambda x=item: fn(x).unsafe_run(), item)
                          for item in items]
                return [f.result() for f in as_completed(futures)]
        return IO(run)

    # ========== Repetition ==========

    def repeat(self, n: int) -> "IO[list[T]]":
        """Repeat IO action n times"""
        def run():
            return [self.unsafe_run() for _ in range(n)]
        return IO(run)

    @staticmethod
    def repeat_io(n: int, action: "IO[T]") -> "IO[list[T]]":
        """Repeat action n times, collect results"""
        return action.repeat(n)

    # ========== Debugging ==========

    def tap_log(self, label: str = "IO") -> "IO[T]":
        """Log value before returning"""
        def run():
            result = self.unsafe_run()
            print(f"[{label}] {result}")
            return result
        return IO(run)

    def time(self) -> "IO[tuple[T, float]]":
        """Measure execution time"""
        import time

        def run():
            start = time.time()
            result = self.unsafe_run()
            elapsed = time.time() - start
            return (result, elapsed)
        return IO(run)

    # ========== Representation ==========

    def __repr__(self) -> str:
        return f"IO(<effect at {hex(id(self._effect))}>)"

    def __str__(self) -> str:
        return "IO(...)"
```

## Usage Patterns

### 1. File Operations

```python
def read_file(path: Path) -> IO[str]:
    """IO action to read file"""
    def read():
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return IO(read)

def write_file(path: Path, content: str) -> IO[None]:
    """IO action to write file"""
    def write():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    return IO(write)

def process_file(input_path: Path, output_path: Path) -> IO[None]:
    """Compose file operations"""
    return (
        read_file(input_path)
        .map(str.upper)
        .flat_map(lambda content: write_file(output_path, content))
    )
```

### 2. Database Operations

```python
def query_database(sql: str, params: dict) -> IO[pd.DataFrame]:
    """IO action to query database"""
    def query():
        return database.execute(sql, params)
    return IO(query)

def export_table(table_name: str, output_path: Path) -> IO[None]:
    """Export table to file"""
    return (
        query_database(f"SELECT * FROM {table_name}", {})
        .map(lambda df: df.to_excel(output_path, index=False))
    )
```

### 3. API Calls

```python
def fetch_url(url: str) -> IO[str]:
    """IO action to fetch URL"""
    import requests

    def fetch():
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    return IO(fetch)

def download_multiple(urls: list[str]) -> IO[list[str]]:
    """Download multiple URLs in parallel"""
    return IO.traverse_parallel(urls, fetch_url)
```

### 4. Console I/O

```python
def print_message(message: str) -> IO[None]:
    """IO action to print message"""
    return IO(lambda: print(message))

def read_line(prompt: str) -> IO[str]:
    """IO action to read line from user"""
    return IO(lambda: input(prompt))

def greet_user() -> IO[None]:
    """Compose console I/O"""
    return (
        read_line("What is your name? ")
        .flat_map(lambda name: print_message(f"Hello, {name}!"))
    )
```

## Examples from excel-to-sqlite

### Excel File Operations

```python
# excel_to_sql/functional/excel_file.py

@dataclass(frozen=True)
class ExcelFileFunctional:
    path: Path

    def read_all_sheets(self) -> IO[dict[str, pd.DataFrame]]:
        """IO action: read all sheets"""
        def read_all():
            if not self.path.exists():
                raise FileNotFoundError(f"File not found: {self.path}")

            return pd.read_excel(self.path, sheet_name=None, engine="openpyxl")

        return IO(read_all)

    def get_combined_hash(self) -> IO[str]:
        """IO action: get combined hash of all sheets"""
        def combine_hashes(sheets: dict[str, pd.DataFrame]) -> str:
            import hashlib

            combined = ""
            for sheet_name in sorted(sheets.keys()):
                sheet_hash = self.compute_hash(sheets[sheet_name])
                combined += f"{sheet_name}:{sheet_hash}"

            return hashlib.sha256(combined.encode()).hexdigest()

        return (
            self.read_all_sheets()
            .map(combine_hashes)
        )

    def validate(self) -> IO[bool]:
        """IO action: validate file is readable"""
        def validate_effect():
            if not self.path.exists():
                return False
            if not self.is_excel_file():
                return False
            try:
                pd.ExcelFile(self.path, engine="openpyxl")
                return True
            except Exception:
                return False

        return IO(validate_effect)

    def import_to_database(
        self,
        database: Database,
        table_name: str,
        mapping: dict
    ) -> IO[ImportResult]:
        """IO action: import Excel to database"""
        return (
            self.read()
            .flat_map(lambda df: self._transform_dataframe(df, mapping))
            .flat_map(lambda df: database.upsert(table_name, df))
            .map(lambda stats: ImportResult(
                table_name=table_name,
                rows_imported=stats.inserted + stats.updated,
                file_hash=self.compute_hash(df)
            }))
        )
```

### Database Operations

```python
# excel_to_sql/functional/database.py

def export_to_excel(
    database: Database,
    tables: list[str],
    output_path: Path
) -> IO[None]:
    """Export multiple tables to Excel"""
    def write_excel(dataframes: dict[str, pd.DataFrame]):
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for table_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=table_name, index=False)

    return (
        IO.traverse(tables, lambda table: (
            database.query(f"SELECT * FROM {table}", {})
        ))
        .map(lambda dfs: dict(zip(tables, dfs)))
        .flat_map(lambda dfs: IO(lambda: write_excel(dfs)))
    )

def backup_database(database: Database, backup_path: Path) -> IO[None]:
    """IO action: backup database"""
    def backup():
        import shutil
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(database.path, backup_path)

    return IO(backup)
```

### CLI Operations

```python
# excel_to_sql/functional/cli.py

def import_command(
    excel_path: str,
    type_name: str,
    force: bool
) -> IO[Exit]:
    """IO action: execute import command"""
    def execute_import():
        # Pure validation
        validation = validate_import_request(excel_path, type_name)
        if validation.is_failure():
            console.print(f"[red]Error:[/red] {validation._value.error}")
            return Exit(1)

        # Unpack validated data
        path, project, mapping = validation._value.value

        # Import with IO
        result = (
            ExcelFileFunctional(path)
            .import_to_database(project.database, type_name, mapping)
            .unsafe_run()
        )

        console.print(f"[green]Success:[/green] Imported {result.rows_imported} rows")
        return Exit(0)

    return IO(execute_import)
```

## Best Practices

### DO
- **Separate pure logic from IO** - Keep business logic pure, wrap only I/O
- **Use IO at boundaries** - File I/O, network, database, console
- **Compose IO operations** - Build complex operations from simple ones
- **Defer execution** - IO is a description, not execution
- **Call unsafe_run() only once** - At application entry point
- **Use memoize for caching** - Avoid repeating expensive operations

### DON'T
- **Don't wrap everything in IO** - Only actual side effects
- **Don't call unsafe_run() internally** - Except at app boundaries
- **Don't nest IO without flat_map** - Use composition instead
- **Don't mix pure and impure code** - Keep them separate
- **Don't use IO for simple computations** - Pure functions are better

### When to Use IO

```
✅ File operations (read, write, delete)
✅ Database queries
✅ Network requests
✅ Console I/O (print, input)
✅ System time
✅ Random number generation
✅ Environment variables
✅ External API calls

❌ Pure computations (use functions)
❌ Data transformations (use functions)
❌ Validation logic (use functions)
❌ Business rules (use functions)
```

## Testing

### Testing IO Operations

```python
def test_read_excel_file():
    """Test by mocking the file system"""
    excel_file = ExcelFileFunctional(Path("test.xlsx"))

    # Mock pd.read_excel
    with patch('pandas.read_excel') as mock_read:
        mock_read.return_value = pd.DataFrame({"a": [1, 2, 3]})

        result = excel_file.read().unsafe_run()

        assert len(result) == 3
        assert list(result.columns) == ["a"]
```

### Testing Pure Logic

```python
def test_compute_hash():
    """Test pure function without IO"""
    excel_file = ExcelFileFunctional(Path("test.xlsx"))

    df = pd.DataFrame({"a": [1, 2, 3]})
    hash_value = excel_file.compute_hash(df)

    assert isinstance(hash_value, str)
    assert len(hash_value) == 64  # SHA256 hex length
```

## Comparison with Other Languages

```
Haskell: IO a
Scala:   IO[T] (cats-effect)
Rust:    No built-in IO monad (use futures)
PureScript: Aff a
Idris:   IO a
```

## Further Reading

- [Returns Library - IO](https://returns.readthedocs.io/en/latest/pages/io.html)
- [Haskell IO Monad](https://wiki.haskell.org/IO_inside)
- [Functional Programming: IO Monad](https://fsharpforfunandprofit.com/posts/13-ways-of-looking-at-a-turtle/)
- [Effect Systems in Python](https://github.com/gcanti/fp-ts)
