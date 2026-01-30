# Monad Composition

Combining multiple monads for complex operations.

## Combining Monads

### Result + Maybe

```python
def get_mapping_safe(project: Project, type_name: str) -> Result[dict, str]:
    """Combine Maybe and Result"""
    return (
        Maybe.from_nullable(project.mappings.get(type_name))
        .to_result(lambda: f"Mapping '{type_name}' not found")
    )
```

### Maybe + IO

```python
def get_table_schema(table_name: str) -> IO[Maybe[dict]]:
    """Combine IO and Maybe"""
    return (
        query_table(table_name)
        .map(lambda result: Maybe.from_nullable(result))
    )
```

### Result + IO

```python
def import_excel(file_path: Path) -> IO[Result[ImportStats, str]]:
    """Combine IO and Result"""
    return (
        validate_file(file_path)
        .flat_map(lambda path: read_excel(path))
        .map(lambda df: import_to_db(df))
    )
```

## Monad Transformers

For deep nesting, use transformers (simplified):

```python
class MaybeResult(Generic[T]):
    """Result[T] wrapped in Maybe, or Maybe[T] wrapped in Result"""
    
    @staticmethod
    def from_result(result: Result[T, E]) -> MaybeResult[T]:
        if result.is_success():
            return MaybeResult(Maybe.some(result._value.value))
        return MaybeResult(Maybe.nothing())
    
    @staticmethod
    def from_maybe(maybe: Maybe[T], error_if_none: E) -> MaybeResult[T]:
        if maybe.is_present():
            return MaybeResult(Result.ok(maybe._value))
        return MaybeResult(Result.fail(error_if_none))
```

## Practical Patterns

### Sequential Validation

```python
def validate_import(data: dict) -> Result[ValidatedData, list[str]]:
    return (
        validate_file(data["file"])
        .flat_map(lambda f: validate_type(data["type"])
                  .map(lambda t: (f, t)))
        .flat_map(lambda ft: validate_mapping(ft[1])
                  .map(lambda m: (*ft, m)))
    )
```

### Parallel Operations

```python
def validate_all(data: dict) -> Result[AllValid, list[str]]:
    """Validate all fields in parallel"""
    return (
        Result.success((data,))
        .apply(lambda d: validate_name(d[0].get("name")))
        .apply(lambda name: validate_email(data.get("email")))
        .map(lambda email: AllValid(name, email))
    )
```

## Composition Helpers

```python
def compose_result(*fns):
    """Compose Result-returning functions"""
    return reduce(lambda f, g: lambda x: f(x).flat_map(g), fns)

def compose_maybe(*fns):
    """Compose Maybe-returning functions"""
    return reduce(lambda f, g: lambda x: f(x).flat_map(g), fns)

def compose_io(*fns):
    """Compose IO-returning functions"""
    return reduce(lambda f, g: lambda x: f(x).flat_map(g), fns)
```

## Examples

### Multi-Step Import

```python
def import_pipeline(file_path: str, type_name: str) -> IO[Result[ImportStats, str]]:
    return (
        IO.pure((file_path, type_name))
        .map(lambda t: validate_request(t[0], t[1]))
        .flat_map(lambda result: (
            IO.pure(result) if result.is_success()
            else IO.pure(result)
        ))
        .flat_map(lambda validated: (
            perform_import(validated._value.value)
        ))
    )
```
