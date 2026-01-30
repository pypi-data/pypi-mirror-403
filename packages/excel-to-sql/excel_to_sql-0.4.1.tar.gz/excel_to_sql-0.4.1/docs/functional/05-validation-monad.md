# Validation Monad

The Validation monad accumulates errors instead of failing fast. Unlike Result which stops on first error, Validation collects all errors.

## Overview

### Current Approach (Mutable ValidationResult)

```python
@dataclass
class ValidationResult:
    is_valid: bool = True
    errors: List[ValidationError] = field(default_factory=list)
    
    def add_error(self, column: str, row: int, message: str) -> None:
        self.errors.append(ValidationError(...))  # Mutation
        self.is_valid = False  # Mutation
```

**Problems:**
- Mutable validation result
- Hard to accumulate errors across multiple validations
- Cannot compose validators easily

### Functional Approach (Validation Monad)

```python
@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool = True
    errors: tuple[ValidationError, ...] = ()
    
    def add_error(self, error: ValidationError) -> "ValidationResult":
        return replace(self, is_valid=False, errors=self.errors + (error,))
    
    def merge(self, other: "ValidationResult") -> "ValidationResult":
        return replace(self,
            is_valid=self.is_valid and other.is_valid,
            errors=self.errors + other.errors
        )

def validate_product_data(df: pd.DataFrame) -> ValidationResult:
    return validate_all(
        df,
        lambda df: validate_required("id", df),
        lambda df: validate_unique("id", df),
        lambda df: validate_regex("email", df, r"^[^@]+@[^@]+$"),
    )
```

## Implementation

```python
from typing import Callable, TypeVar, Generic
from functools import reduce

T = TypeVar('T')
E = TypeVar('E')

class Validation(Generic[T, E]):
    """Monad for validation that accumulates errors"""
    
    def __init__(self, result: Union[T, "ValidationResult"]):
        if isinstance(result, ValidationResult):
            self._result = result
            self._value = None
        else:
            self._value = value
            self._result = ValidationResult()
    
    @staticmethod
    def success(value: T) -> "Validation[T, E]":
        return Validation(value)
    
    @staticmethod
    def failure(errors: tuple[E, ...]) -> "Validation[T, E]":
        result = ValidationResult(is_valid=False, errors=errors)
        return Validation(result)
    
    def map(self, fn: Callable[[T], "U"]) -> "Validation[U, E]":
        if self._result.is_valid:
            try:
                return Validation.success(fn(self._value))
            except Exception as e:
                return Validation.failure((e,))
        return Validation(self._result)
    
    def flat_map(self, fn: Callable[[T], "Validation[U, E]"]) -> "Validation[U, E]":
        if self._result.is_valid:
            return fn(self._value)
        return Validation(self._result)
    
    def ap(self, other: "Validation[Callable[[T], U], E]") -> "Validation[U, E]":
        """Applicative apply: Validation[fn] <*> Validation[value]"""
        if self._result.is_valid and other._result.is_valid:
            try:
                return Validation.success(other._value(self._value))
            except Exception as e:
                return Validation.failure((e,))
        # Combine errors from both
        combined_errors = self._result.errors + other._result.errors
        return Validation.failure(combined_errors)
    
    def combine(self, *others: "Validation[Any, E]") -> "Validation[tuple, E]":
        """Combine multiple validations"""
        all_results = (self,) + others
        combined = ValidationResult()
        values = []
        
        for v in all_results:
            combined = combined.merge(v._result)
            if v._result.is_valid:
                values.append(v._value)
        
        if combined.is_valid:
            return Validation.success(tuple(values))
        return Validation(combined)
    
    def to_result(self) -> "Result[T, ValidationResult]":
        """Convert to Result monad"""
        from .result_monad import Result
        if self._result.is_valid:
            return Result.ok(self._value)
        return Result.fail(self._result)
```

## Usage Patterns

### Single Validation

```python
def validate_required(column: str, df: pd.DataFrame) -> ValidationResult:
    result = ValidationResult()
    null_rows = df[df[column].isna()].index.tolist()
    
    for idx in null_rows:
        result = result.add_error(ValidationError(column, idx, "Required"))
    
    return result
```

### Combining Validations

```python
def validate_row(row: pd.Series) -> ValidationResult:
    return (
        validate_required("id", row)
        .merge(validate_required("name", row))
        .merge(validate_email_format("email", row))
    )
```

### Applicative Style

```python
def validate_user(data: dict) -> Validation[User, str]:
    """Validate all fields, accumulating errors"""
    return (
        validate_name(data.get("name"))
        .apply(lambda name: (
            validate_email(data.get("email"))
            .map(lambda email: User(name, email))
        ))
    )
```

## When to Use Validation

```
✅ Form validation with multiple fields
✅ Data validation requiring all errors
✅ Schema validation
✅ Configuration validation
✅ Batch data processing

❌ Single error cases (use Result)
❌ Simple yes/no checks (use bool)
```
