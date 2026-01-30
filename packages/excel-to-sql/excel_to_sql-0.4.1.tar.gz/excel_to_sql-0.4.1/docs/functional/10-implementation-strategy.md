# Implementation Strategy

Step-by-step migration plan for introducing functional programming patterns.

## Phase 1: Result/Either Monad (Week 1-2)

### Goals
- Replace exception handling with Result
- Create Result monad implementation
- Add to existing error-prone functions

### Tasks
1. Create `excel_to_sql/functional/result.py`
2. Identify functions with exception handling
3. Convert one module at a time:
   - `cli.py` → validation functions
   - `entities/excel_file.py` → file operations
   - `entities/database.py` → database operations

### Example
```python
# Before
try:
    project = Project.from_current_directory()
except Exception as e:
    console.print(f"Error: {e}")
    raise Exit(1)

# After
result = validate_project_exists()
if result.is_failure():
    console.print(f"Error: {result._value.error}")
    raise Exit(1)
project = result._value.value
```

### Success Criteria
- No try/catch in CLI commands
- All validation functions return Result
- >80% of exceptions converted to Result

## Phase 2: Maybe Monad (Week 2-3)

### Goals
- Replace None checks with Maybe
- Create Maybe monad implementation
- Convert nullable operations

### Tasks
1. Create `excel_to_sql/functional/maybe.py`
2. Identify functions returning Optional[T]
3. Convert:
   - SDK client properties
   - Mapping lookups
   - Database queries that might not find data

### Example
```python
# Before
mapping = self.mappings.get(type_name)
if mapping is None:
    raise ValueError(f"Unknown type: {type_name}")

# After
mapping = self.get_mapping(type_name)
if mapping.is_empty():
    return Result.fail(f"Unknown type: {type_name}")
mapping_dict = mapping._value.value
```

## Phase 3: Immutable Data Structures (Week 3-4)

### Goals
- Use frozen dataclasses
- Replace in-place mutations
- Create pure functions

### Tasks
1. Add `@dataclass(frozen=True)` to entities
2. Replace mutation with `replace()`
3. Extract pure transformation functions

### Example
```python
# Before
@dataclass
class DetectionState:
    confidence: float = 0.0
    issues: list = field(default_factory=list)
    
    def add_confidence(self, delta: float):
        self.confidence += delta  # Mutation

# After
@dataclass(frozen=True)
class DetectionState:
    confidence: float = 0.0
    issues: tuple = ()
    
    def add_confidence(self, delta: float) -> "DetectionState":
        return replace(self, confidence=self.confidence + delta)
```

## Phase 4: IO Monad (Week 4-5)

### Goals
- Separate pure logic from side effects
- Wrap I/O operations in IO
- Enable testing of pure logic

### Tasks
1. Create `excel_to_sql/functional/io.py`
2. Identify side effects in business logic
3. Wrap:
   - File operations
   - Database queries
   - Console I/O

### Example
```python
# Before
def get_content_hash(self, sheet_name: str = None) -> str:
    df = pd.read_excel(self.path, sheet_name=sheet_name)
    return self._compute_hash(df)

# After
def read(self, sheet_name: str = None) -> IO[pd.DataFrame]:
    return IO(lambda: pd.read_excel(self.path, sheet_name=sheet_name))

def get_content_hash(self, sheet_name: str = None) -> IO[str]:
    return self.read(sheet_name).map(self._compute_hash)
```

## Phase 5: State Monad (Week 5-6)

### Goals
- Remove mutable state from classes
- Use State monad for accumulators
- Make state transitions explicit

### Tasks
1. Create `excel_to_sql/functional/state.py`
2. Identify stateful operations
3. Convert pattern detection to State

### Example
```python
# Before
class PatternDetector:
    def detect_patterns(self, df: pd.DataFrame) -> dict:
        results = {"confidence": 0.0}
        results["confidence"] += 0.25  # Mutation
        return results

# After
def detect_patterns(df: pd.DataFrame) -> State[DetectionState, dict]:
    def run(state: DetectionState):
        new_state = state.add_confidence(0.25)
        return (pk, new_state)
    return State(run)
```

## Phase 6: Composition & Refactoring (Week 6-8)

### Goals
- Build combinators
- Create reusable pipelines
- Refactor service layer

### Tasks
1. Create composition helpers
2. Build transformation pipelines
3. Extract business logic from CLI

### Example
```python
# Build validation pipeline
validate_import = compose(
    validate_file_exists,
    and_then(validate_excel_extension),
    and_then(validate_project_exists),
    and_then(validate_mapping_exists),
)
```

## Phase 7: Testing & Documentation (Ongoing)

### Goals
- Add tests for all monads
- Document patterns
- Create examples

### Tasks
1. Unit tests for each monad
2. Integration tests for composed operations
3. Documentation updates

## Priority Order

| Priority | Monad | Impact | Effort |
|----------|-------|--------|--------|
| 1 | Result/Either | High | Medium |
| 2 | Maybe | High | Low |
| 3 | Immutable Types | Medium | Medium |
| 4 | IO | Medium | High |
| 5 | State | Low | High |
| 6 | Validation | Medium | Medium |
| 7 | Transaction | Low | Medium |
| 8 | Reader | Low | Low |

## Rollout Strategy

1. **Start small**: Convert one module at a time
2. **Parallel development**: New features use functional patterns
3. **Gradual migration**: Old code converted when touched
4. **No breaking changes**: Public APIs stay compatible

## Tools & Libraries

Consider using established libraries:
- `returns` - Complete monad implementations
- `toolz` - Functional utilities
- `cytoolz` - Faster toolz (C implementation)

## Success Metrics

- Reduction in exception usage
- Increase in pure function percentage
- Test coverage improvement
- Code reduction in CLI
- Developer feedback
