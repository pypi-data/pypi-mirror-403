# Code Examples

Complete working examples of functional programming patterns in excel-to-sqlite.

## Example 1: File Import with Result Monad

```python
from pathlib import Path
from typing import Union
import pandas as pd

# Pure validation functions
def validate_file_exists(path: Path) -> Result[Path, str]:
    if not path.exists():
        return Result.fail(f"File not found: {path}")
    return Result.ok(path)

def validate_excel_extension(path: Path) -> Result[Path, str]:
    if path.suffix.lower() not in {".xlsx", ".xls"}:
        return Result.fail(f"Not an Excel file: {path}")
    return Result.ok(path)

# Composed validation pipeline
def validate_excel_file(path: Union[str, Path]) -> Result[Path, str]:
    path_obj = Path(path) if isinstance(path, str) else path

    return (
        validate_file_exists(path_obj)
        .and_then(validate_excel_extension)
    )
```

## Example 2: Maybe Monad for Configuration

```python
class Project:
    def get_mapping(self, type_name: str) -> Maybe[dict]:
        return Maybe.from_nullable(self.mappings.get(type_name))

    def get_target_table(self, type_name: str) -> Maybe[str]:
        return (
            self.get_mapping(type_name)
            .flat_map(lambda m: Maybe.from_nullable(m.get("target_table")))
        )
```

## Example 3: IO Monad for File Operations

```python
@dataclass(frozen=True)
class ExcelFile:
    path: Path

    def read(self) -> IO[pd.DataFrame]:
        def read_effect():
            if not self.path.exists():
                raise FileNotFoundError(f"File not found: {self.path}")
            return pd.read_excel(self.path)
        return IO(read_effect)

    def get_hash(self) -> IO[str]:
        return self.read().map(self.compute_hash)
```

## Example 4: State Monad for Pattern Detection

```python
@dataclass(frozen=True)
class DetectionState:
    confidence: float = 0.0
    issues: tuple[str, ...] = ()

    def add_confidence(self, delta: float) -> "DetectionState":
        return replace(self, confidence=min(1.0, self.confidence + delta))

def detect_pk_state(df: pd.DataFrame) -> State[DetectionState, Optional[str]]:
    def run(state: DetectionState):
        pk, issues = detect_primary_key_pure(df)
        new_state = state.add_confidence(0.25) if pk else state.add_issue(issues[0])
        return pk, new_state
    return State(run)
```

## Example 5: Validation Monad

```python
def validate_required(column: str, df: pd.DataFrame) -> ValidationResult:
    result = ValidationResult()
    null_rows = df[df[column].isna()].index.tolist()

    for idx in null_rows:
        result = result.add_error(
            ValidationError(column, idx, "Required field is null")
        )

    return result

def validate_product_data(df: pd.DataFrame) -> ValidationResult:
    return validate_all(
        df,
        lambda df: validate_required("id", df),
        lambda df: validate_unique("id", df),
        lambda df: validate_regex("email", df, r"^[^@]+@[^@]+$"),
    )
```

See other documents for complete examples.
