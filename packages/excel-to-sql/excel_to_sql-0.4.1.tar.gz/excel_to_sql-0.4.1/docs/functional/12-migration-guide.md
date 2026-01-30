# Migration Guide

Before and after comparisons for migrating to functional programming patterns.

## 1. Error Handling: Exceptions to Result

### Before (Exceptions)
```python
try:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    project = Project.from_current_directory()
except Exception as e:
    console.print(f"Error: {e}")
    raise Exit(1)
```

### After (Result Monad)
```python
def validate_file_exists(path: Path) -> Result[Path, str]:
    if not path.exists():
        return Result.fail(f"File not found: {path}")
    return Result.ok(path)

result = validate_file_exists(path)
if result.is_failure():
    console.print(f"Error: {result._value.error}")
    raise Exit(1)
path = result._value.value
```

## 2. Nullable Values: None to Maybe

### Before (None checks)
```python
mapping = self.mappings.get(type_name)
if mapping is None:
    raise ValueError(f"Unknown type: {type_name}")
# Use mapping...
```

### After (Maybe Monad)
```python
def get_mapping(self, type_name: str) -> Maybe[dict]:
    return Maybe.from_nullable(self.mappings.get(type_name))

mapping = self.get_mapping(type_name)
if mapping.is_empty():
    return Result.fail(f"Unknown type: {type_name}")
mapping_dict = mapping._value.value
```

## 3. Side Effects: Direct I/O to IO Monad

### Before (Direct I/O)
```python
class ExcelFile:
    def get_content_hash(self) -> str:
        df = pd.read_excel(self.path)  # Side effect!
        return self._compute_hash(df)
```

### After (IO Monad)
```python
@dataclass(frozen=True)
class ExcelFileFunctional:
    path: Path

    def read(self) -> IO[pd.DataFrame]:
        return IO(lambda: pd.read_excel(self.path))

    def get_content_hash(self) -> IO[str]:
        return self.read().map(self._compute_hash)
```

## 4. Stateful Operations: Mutable to State Monad

### Before (Mutable State)
```python
class PatternDetector:
    def detect_patterns(self, df: pd.DataFrame) -> dict:
        results = {"confidence": 0.0}
        results["confidence"] += 0.25  # Mutation!
        return results
```

### After (State Monad)
```python
@dataclass(frozen=True)
class DetectionState:
    confidence: float = 0.0

    def add_confidence(self, delta: float) -> "DetectionState":
        return replace(self, confidence=self.confidence + delta)

def detect_pk_state(df: pd.DataFrame) -> State[DetectionState, Optional[str]]:
    def run(state: DetectionState):
        pk = detect_primary_key_pure(df)
        new_state = state.add_confidence(0.25)
        return pk, new_state
    return State(run)
```

## 5. Validation: Mutable to Immutable

### Before (Mutable)
```python
@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)

    def add_error(self, error: ValidationError) -> None:
        self.errors.append(error)  # Mutation
        self.is_valid = False  # Mutation
```

### After (Immutable)
```python
@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool = True
    errors: tuple[ValidationError, ...] = ()

    def add_error(self, error: ValidationError) -> "ValidationResult":
        return replace(self, is_valid=False, errors=self.errors + (error,))
```

## 6. DataFrame Operations: In-Place to Pure

### Before (In-Place)
```python
def clean(self) -> None:
    df[col] = df[col].astype(str).str.strip()  # Mutation
    df.replace(r"^\s*$", np.nan, regex=True, inplace=True)  # Mutation
```

### After (Pure)
```python
def strip_whitespace(self) -> "ImmutableDataFrame":
    df = self._df.copy()
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()
    return ImmutableDataFrame(df)

def clean(self) -> "ImmutableDataFrame":
    return (
        self.strip_whitespace()
        .normalize_empty_strings()
        .drop_empty_rows()
    )
```

## Migration Checklist

For each module:
- [ ] Identify functions using exceptions -> Add Result
- [ ] Identify functions returning None -> Add Maybe
- [ ] Identify side effects -> Wrap in IO
- [ ] Identify mutable state -> Use frozen dataclasses
- [ ] Extract pure functions from business logic
- [ ] Add tests for pure functions
- [ ] Update documentation

## Common Patterns

| Current | Functional | Purpose |
|---------|-----------|---------|
| try/catch | Result.flat_map | Error handling |
| if x is None | Maybe.filter | Nullable values |
| df.col = ... | df.map() | Transformations |
| for acc += ... | items.fold(acc) | Accumulation |
| return None | Maybe.nothing() | Empty case |
| raise Error | Result.fail() | Failure case |
