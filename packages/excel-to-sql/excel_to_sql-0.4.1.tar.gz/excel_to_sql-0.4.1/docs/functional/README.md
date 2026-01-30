# Functional Programming Documentation

This directory contains comprehensive documentation for refactoring the excel-to-sqlite project using functional programming patterns and monads.

## Overview

The current codebase uses traditional object-oriented patterns with:
- Mutable state throughout entities and services
- Exceptions for error handling
- Direct side effects mixed with business logic
- Imperative loops and state mutations
- Nullable values with None checks

This documentation provides a roadmap for transitioning to:
- **Immutable data structures** using frozen dataclasses
- **Monadic composition** for error handling and side effects
- **Pure functions** separated from I/O operations
- **Explicit effects** through monads (Result, Maybe, IO, State, etc.)
- **Composable operations** using function composition

## Documents

### Core Monads

| Document | Description |
|----------|-------------|
| [Result/Either Monad](./01-result-either-monad.md) | Error handling without exceptions |
| [Maybe Monad](./02-maybe-monad.md) | Safe handling of nullable values |
| [IO Monad](./03-io-monad.md) | Isolating side effects |
| [State Monad](./04-state-monad.md) | Managing stateful computations |
| [Validation Monad](./05-validation-monad.md) | Accumulating validation errors |
| [Transaction Monad](./06-transaction-monad.md) | Composable database operations |
| [Reader Monad](./07-reader-monad.md) | Dependency injection |

### Patterns and Techniques

| Document | Description |
|----------|-------------|
| [Immutable DataFrames](./08-immutable-dataframes.md) | Pure transformations on pandas DataFrames |
| [Monad Composition](./09-monad-composition.md) | Combining multiple monads |
| [Implementation Strategy](./10-implementation-strategy.md) | Step-by-step migration plan |
| [Code Examples](./11-code-examples.md) | Complete working examples |
| [Migration Guide](./12-migration-guide.md) | Before/after comparisons |

## Quick Reference

### Monad Selection Guide

```
┌─────────────────────────┬──────────────────────┬─────────────────────────┐
│ Use Case                │ Monad                │ Benefit                 │
├─────────────────────────┼──────────────────────┼─────────────────────────┤
│ Error handling          │ Result/Either        │ Explicit error paths    │
│ Nullable values         │ Maybe                │ Safe chaining           │
│ File I/O                │ IO                   │ Testable pure logic     │
│ State accumulation      │ State                │ Reproducible            │
│ Validation errors       │ Validation           │ Accumulate all errors   │
│ Database operations     │ Transaction          │ Composable operations   │
│ Configuration loading   │ Reader               │ Explicit dependencies   │
└─────────────────────────┴──────────────────────┴─────────────────────────┘
```

### Key Concepts

#### 1. Pure Functions
Functions that:
- Always return the same output for the same input
- Have no side effects
- Don't modify their arguments
- Are easy to test and reason about

```python
# Pure
def add(a: int, b: int) -> int:
    return a + b

# Not pure (depends on external state)
def get_current_time() -> datetime:
    return datetime.now()
```

#### 2. Immutability
Data structures that cannot be modified after creation:

```python
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class User:
    name: str
    email: str

# Create new instance instead of modifying
user = User("Alice", "alice@example.com")
updated_user = replace(user, email="new@email.com")
```

#### 3. Function Composition
Combining small functions to build complex behavior:

```python
from functools import reduce

# Compose functions
def compose(*functions):
    return reduce(lambda f, g: lambda x: f(g(x)), functions)

# Usage
process = compose(str.upper, str.strip)
process("  hello  ")  # "HELLO"
```

#### 4. Monadic Operations
Common monad interface:

```python
class Monad:
    def map(self, fn): pass        # Transform value
    def flat_map(self, fn): pass   # Chain monads
    # Also: filter, get_or_else, etc.
```

## Benefits of Functional Programming

### Code Quality
- **Predictable**: Pure functions always produce the same output
- **Testable**: No hidden dependencies or side effects
- **Maintainable**: Small, composable functions
- **Debuggable**: Explicit data flow and transformations

### Error Handling
- **Explicit**: Errors are visible in type signatures
- **Composable**: Error handling chains naturally
- **Safe**: Compiler/runtime checks for forgotten errors
- **Clear**: Error paths are documented

### Architecture
- **Decoupled**: Business logic separated from I/O
- **Reusable**: Pure functions work in any context
- **Parallelizable**: No shared mutable state
- **Refactorable**: Composable operations

## Migration Strategy

1. **Phase 1**: Add Result/Either monad for error handling
2. **Phase 2**: Introduce Maybe for nullable values
3. **Phase 3**: Create immutable data structures
4. **Phase 4**: Extract pure functions from I/O
5. **Phase 5**: Add IO wrapper for side effects
6. **Phase 6**: Introduce State for complex stateful operations
7. **Phase 7**: Build combinators and composition helpers

See [Implementation Strategy](./10-implementation-strategy.md) for details.

## Python Libraries

While this documentation shows custom implementations, consider these libraries:

### Returns
```bash
pip install returns
```

Comprehensive functional programming library with monads:
- `Result[E, T]` - Result/Either monad
- `Maybe[T]` - Maybe/Option monad
- `IO[T]` - IO monad
- `RequiresContext` - Reader monad

### Toolz / Cytoolz
```bash
pip install toolz
# or
pip install cytoolz  # Faster C implementation
```

Functional programming utilities:
- `compose`, `pipe` - Function composition
- `curry` - Currying support
- `map`, `filter`, `reduce` - Functional operations

### Fn.py
```bash
pip install fn
```

Functional programming tools:
- Monad implementations
- Currying and partial application
- Stream processing

## Getting Started

1. **Read** the [Result/Either Monad](./01-result-either-monad.md) document first
2. **Review** the [Code Examples](./11-code-examples.md) for practical usage
3. **Follow** the [Implementation Strategy](./10-implementation-strategy.md)
4. **Reference** the [Migration Guide](./12-migration-guide.md) when refactoring

## Contributing

When adding functional programming patterns:
1. Update this README with new patterns
2. Add code examples to `11-code-examples.md`
3. Document before/after in migration guide
4. Keep examples simple and practical

## Resources

### Books
- "Functional Programming in Python" by David Mertz
- "Learn You a Haskell for Great Good!" (concepts apply)
- "Functional Programming: A PragPub Anthology"

### Online
- [Python Functional Programming HOWTO](https://docs.python.org/3/howto/functional.html)
- [Returns Library Documentation](https://returns.readthedocs.io/)
- [Toolz Documentation](https://toolz.readthedocs.io/)

### Papers
- "Monads for Functional Programming" by Philip Wadler
- "Applicative Programming with Effects" by Conor McBride

## License

This documentation is part of the excel-to-sqlite project and follows the same license.
