# State Monad

The State monad manages stateful computations in a functional way. Instead of mutating variables, it transforms state explicitly: `S -> (A, S)` - takes a state S and returns a value A with a new state S.

## Overview

### Current Approach (Mutable State)

```python
# excel_to_sql/auto_pilot/detector.py (lines 117-182)
class PatternDetector:
    def detect_patterns(self, df: pd.DataFrame, table_name: str) -> dict:
        results = {"confidence": 0.0, "issues": []}  # Mutable state

        pk = self._detect_primary_key(df)
        if pk:
            results["primary_key"] = pk
            results["confidence"] += 0.25  # Mutation!
        else:
            results["issues"].append("No PK")  # Mutation!

        # More mutations...
        return results
```

**Problems:**
- Hidden state mutations
- Difficult to reproduce/debug
- Cannot easily inspect intermediate states
- Hard to test state transitions

### Functional Approach (State Monad)

```python
@dataclass(frozen=True)
class DetectionState:
    """Immutable detection state"""
    confidence: float = 0.0
    issues: tuple[str, ...] = ()
    patterns_found: int = 0

    def add_confidence(self, delta: float) -> "DetectionState":
        return replace(self, confidence=min(1.0, self.confidence + delta))

    def add_issue(self, issue: str) -> "DetectionState":
        return replace(self, issues=self.issues + (issue,))

def detect_patterns_functional(df: pd.DataFrame, table_name: str) -> dict:
    initial_state = DetectionState()

    computation = (
        detect_pk_state(df)
        .flat_map(lambda pk: detect_mappings_state(df)
                  .flat_map(lambda mappings: detect_fks_state(df, table_name)
                            .map(lambda fks: (pk, mappings, fks))))
    )

    (pk, mappings, fks), final_state = computation.run(initial_state)

    return {
        "primary_key": pk,
        "value_mappings": mappings,
        "foreign_keys": fks,
        "confidence": final_state.confidence,
        "issues": list(final_state.issues),
    }
```

## Implementation

```python
from typing import Callable, TypeVar, Generic, Tuple

S = TypeVar('S')  # State type
A = TypeVar('A')  # Result type
B = TypeVar('B')

class State(Generic[S, A]):
    """
    State monad: S -> (A, S)

    A computation that reads and transforms state S
    while producing a value A.
    """

    def __init__(self, run: Callable[[S], Tuple[A, S]]):
        """run is a function: state -> (value, new_state)"""
        self.run = run

    # ========== Execution ==========

    def run_state(self, initial_state: S) -> Tuple[A, S]:
        """Execute state computation"""
        return self.run(initial_state)

    def eval_state(self, initial_state: S) -> A:
        """Execute and get only the value"""
        value, _ = self.run(initial_state)
        return value

    def exec_state(self, initial_state: S) -> S:
        """Execute and get only the final state"""
        _, state = self.run(initial_state)
        return state

    # ========== Constructors ==========

    @staticmethod
    def pure(value: A) -> "State[S, A]":
        """Lift value into State (doesn't change state)"""
        return State(lambda s: (value, s))

    @staticmethod
    def get() -> "State[S, S]":
        """Get current state"""
        return State(lambda s: (s, s))

    @staticmethod
    def put(state: S) -> "State[S, None]":
        """Replace state"""
        return State(lambda _: (None, state))

    @staticmethod
    def modify(fn: Callable[[S], S]) -> "State[S, None]":
        """Modify state with function"""
        return State(lambda s: (None, fn(s)))

    @staticmethod
    def gets(fn: Callable[[S], A]) -> "State[S, A]":
        """Read and transform state"""
        return State(lambda s: (fn(s), s))

    # ========== Transform ==========

    def map(self, fn: Callable[[A], B]) -> "State[S, B]":
        """Transform value, pass through state"""
        def run(s: S) -> Tuple[B, S]:
            a, new_s = self.run(s)
            return fn(a), new_s
        return State(run)

    def flat_map(self, fn: Callable[[A], "State[S, B]"]) -> "State[S, B]":
        """Chain stateful computations"""
        def run(s: S) -> Tuple[B, S]:
            a, new_s = self.run(s)
            return fn(a).run(new_s)
        return State(run)

    # ========== State Operations ==========

    def and_then(self, other: "State[S, B]") -> "State[S, B]":
        """Sequence state operations, keep second value"""
        return self.flat_map(lambda _: other)
```

## Usage Examples

### Counter with State

```python
def increment(n: int) -> State[int, None]:
    """Increment state by n"""
    return State.modify(lambda count: count + n)

def get_count() -> State[int, int]:
    """Get current count"""
    return State.get()

# Usage
computation = (
    increment(5)
    .and_then(increment(3))
    .and_then(get_count)
)

result, final_state = computation.run_state(0)
# result = 8, final_state = 8
```

### Pattern Detection

```python
def detect_pk_state(df: pd.DataFrame) -> State[DetectionState, Optional[str]]:
    """Stateful PK detection"""
    def run(s: DetectionState):
        pk, issues = detect_primary_key_pure(df)
        new_state = s.add_confidence(0.25) if pk else s.add_issue(issues[0])
        return pk, new_state
    return State(run)

def detect_mappings_state(df: pd.DataFrame) -> State[DetectionState, dict]:
    """Stateful value mapping detection"""
    def run(s: DetectionState):
        mappings = detect_value_mappings_pure(df)
        delta = 0.20 * len(mappings) / 3
        return mappings, s.add_confidence(delta)
    return State(run)
```

## When to Use State

```
✅ Accumulators (counters, sums)
✅ Multi-step algorithms
✅ Validation with context
✅ Parsing with position
✅ Random number generation with seed
✅ Building complex data structures

❌ Simple mutations (use immutable types)
❌ One-time computations
❌ Stateless operations
```
