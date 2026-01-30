# Reader Monad

The Reader monad represents computations that depend on a shared environment/context. It enables dependency injection and implicit configuration passing.

## Overview

### Current Approach (Hardcoded Dependencies)

```python
def load_mappings() -> dict:
    """Hardcoded dependency on config path"""
    path = Path("config/mappings.json")  # Hardcoded!
    with open(path) as f:
        return json.load(f)
```

**Problems:**
- Hardcoded dependencies
- Difficult to test
- No flexibility in configuration

### Functional Approach (Reader Monad)

```python
class ConfigReader:
    """Reader monad for configuration"""
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
    
    def read_json(self) -> Result[dict, str]:
        if not self.config_path.exists():
            return Result.fail(f"Config not found: {self.config_path}")
        
        try:
            with open(self.config_path) as f:
                return Result.ok(json.load(f))
        except Exception as e:
            return Result.fail(str(e))

def load_config(reader: ConfigReader) -> Result[MappingsConfig, str]:
    return (
        reader.read_json()
        .flat_map(MappingsConfig.from_dict)
    )
```

## Implementation

```python
from typing import Callable, TypeVar, Generic

R = TypeVar('R')  # Environment/Reader type
A = TypeVar('A')  # Result type

class Reader(Generic[R, A]):
    """R -> A: function from environment to value"""
    
    def __init__(self, run: Callable[[R], A]):
        self.run = run
    
    def map(self, fn: Callable[[A], "B"]) -> "Reader[R, B]":
        def run(env: R) -> B:
            return fn(self.run(env))
        return Reader(run)
    
    def flat_map(self, fn: Callable[[A], "Reader[R, B]"]) -> "Reader[R, B]":
        def run(env: R) -> B:
            return fn(self.run(env)).run(env)
        return Reader(run)
    
    @staticmethod
    def ask() -> "Reader[R, R]":
        """Get the environment"""
        return Reader(lambda env: env)
    
    @staticmethod
    def asks(fn: Callable[[R], A]) -> "Reader[R, A]":
        """Read and transform environment"""
        return Reader(lambda env: fn(env))
    
    @staticmethod
    def local(fn: Callable[[R], R], reader: "Reader[R, A]") -> "Reader[R, A]":
        """Modify environment for computation"""
        return Reader(lambda env: reader.run(fn(env)))
    
    def run_reader(self, env: R) -> A:
        """Run with environment"""
        return self.run(env)
```

## Usage Examples

### Configuration

```python
def get_db_path() -> Reader[Config, Path]:
    return Reader(lambda config: config.db_path)

def load_database() -> Reader[Config, Database]:
    return (
        get_db_path()
        .map(lambda path: Database(path))
    )

# Usage
config = Config(db_path="data.db")
database = load_database().run_reader(config)
```

### Dependency Injection

```python
def import_excel(file: Path) -> Reader[Dependencies, ImportResult]:
    return (
        Reader.ask()
        .flat_map(lambda deps: (
            deps.database
            .upsert(file)
            .map(lambda result: ImportResult(result))
        ))
    )
```

## When to Use Reader

```
✅ Configuration dependency
✅ Database connections
✅ Logger instances
✅ API clients
✅ Any shared environment

❌ Simple computations (use plain functions)
❌ State that changes during computation (use State)
```
