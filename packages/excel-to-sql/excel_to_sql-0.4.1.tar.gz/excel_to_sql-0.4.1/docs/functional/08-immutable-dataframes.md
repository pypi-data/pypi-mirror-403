# Immutable DataFrames

Pure transformations on pandas DataFrames without in-place mutations.

## Overview

### Current Approach (Mutable)

```python
class DataFrame:
    def clean(self, strip_columns: bool = True) -> None:
        """Clean data in place - mutation!"""
        df[col] = df[col].astype(str).str.strip()  # Mutation
        df.replace(r"^\s*$", np.nan, regex=True, inplace=True)  # In-place
        df.dropna(how="all", inplace=True)  # In-place
```

**Problems:**
- Mutates original data
- Difficult to track transformations
- Cannot undo or inspect intermediate steps

### Functional Approach

```python
class ImmutableDataFrame:
    """Immutable DataFrame with pure transformations"""
    
    def strip_whitespace(self) -> "ImmutableDataFrame":
        """Returns NEW DataFrame with stripped whitespace"""
        df = self._df.copy()
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].astype(str).str.strip()
        return ImmutableDataFrame(df)
    
    def normalize_empty_strings(self) -> "ImmutableDataFrame":
        df = self._df.replace(r"^\s*$", np.nan, regex=True)
        return ImmutableDataFrame(df)
    
    def drop_empty_rows(self) -> "ImmutableDataFrame":
        df = self._df.dropna(how="all")
        return ImmutableDataFrame(df)
    
    def transform(self, *fns) -> "ImmutableDataFrame":
        """Apply transformations in sequence"""
        return reduce(
            lambda acc, fn: ImmutableDataFrame(fn(acc._df)),
            fns,
            self
        )
```

## Pure Transformation Functions

```python
# Standalone pure functions
def strip_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for col in result.columns:
        if result[col].dtype == "object":
            result[col] = result[col].astype(str).str.strip()
    return result

def normalize_empty_strings(df: pd.DataFrame) -> pd.DataFrame:
    return df.replace(r"^\s*$", np.nan, regex=True)

def drop_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(how="all")
```

## Function Composition

```python
from functools import reduce

def compose(*functions):
    """Compose functions: compose(f, g)(x) = f(g(x))"""
    return reduce(lambda f, g: lambda x: f(g(x)), functions)

def pipe(value, *functions):
    """Pipe value through functions: pipe(x, f, g) = g(f(x))"""
    return reduce(lambda acc, fn: fn(acc), functions, value)

# Usage
clean_composed = compose(
    lowercase_columns,
    drop_empty_rows,
    normalize_empty_strings,
    strip_whitespace
)

clean_df = clean_composed(raw_df)
```

## Pipeline Pattern

```python
def clean_pipeline(raw_df: pd.DataFrame) -> ImmutableDataFrame:
    """Reusable cleaning pipeline"""
    return (
        ImmutableDataFrame(raw_df)
        .transform(
            strip_whitespace,
            normalize_empty_strings,
            drop_empty_rows,
            lowercase_columns
        )
    )
```

## Best Practices

```
✅ Always return new DataFrame
✅ Use copy() before modifications
✅ Chain transformations
✅ Create reusable pipelines

❌ Never use inplace=True
❌ Never modify df in place
❌ Don't mix mutations with pure functions
```
