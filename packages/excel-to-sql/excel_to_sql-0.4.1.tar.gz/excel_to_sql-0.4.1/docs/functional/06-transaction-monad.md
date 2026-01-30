# Transaction Monad

The Transaction monad provides composable database operations with automatic transaction management.

## Overview

### Current Approach (Imperative)

```python
def upsert(self, df: pd.DataFrame, primary_key: list[str]) -> dict:
    inserted = 0
    updated = 0
    
    for _, row in df.iterrows():
        if exists:
            self._database.execute(update_sql, row_dict)
            updated += 1
        else:
            self._database.execute(insert_sql, row_dict)
            inserted += 1
    
    return {"inserted": inserted, "updated": updated}
```

**Problems:**
- Manual counter management
- No transaction guarantees
- Cannot compose operations

### Functional Approach

```python
@dataclass(frozen=True)
class UpsertStats:
    inserted: int = 0
    updated: int = 0
    failed: int = 0
    
    def record_insert(self) -> "UpsertStats":
        return replace(self, inserted=self.inserted + 1)
    
    def merge(self, other: "UpsertStats") -> "UpsertStats":
        return replace(self,
            inserted=self.inserted + other.inserted,
            updated=self.updated + other.updated,
            failed=self.failed + other.failed,
        )

class Transaction(Generic[T]):
    """Monad for database transactions"""
    
    def __init__(self, run: Callable[[Database], tuple[T, int]]):
        self.run = run
    
    def map(self, fn: Callable[[T], "U"]) -> "Transaction[U]":
        def run(db: Database):
            result, rowcount = self.run(db)
            return fn(result), rowcount
        return Transaction(run)
    
    def flat_map(self, fn: Callable[[T], "Transaction[U]"]) -> "Transaction[U]":
        def run(db: Database):
            result, rowcount = self.run(db)
            return fn(result).run(db)
        return Transaction(run)
    
    @staticmethod
    def pure(value: T) -> "Transaction[T]":
        return Transaction(lambda db: (value, 0))

def upsert_dataframe(table: TableFunctional, df: pd.DataFrame, pk: list[str]) -> Transaction[UpsertStats]:
    """Transactional bulk upsert"""
    rows = [row.to_dict() for _, row in df.iterrows()]
    
    def fold(acc: UpsertStats, row: dict) -> UpsertStats:
        result, _ = table.upsert_row(row, pk).run(table.database)
        return acc.merge(result)
    
    return Transaction(lambda db: (
        reduce(fold, rows, UpsertStats()),
        0
    ))
```

## Usage

```python
# Single operation
result = (
    table.create(df, ["id"])
    .and_then(table.upsert(df, ["id"]))
)
stats, _ = result.run(database)

# Batch operations
def import_multiple_files(files: list[Path]) -> Transaction[ImportStats]:
    return IO.traverse(files, lambda f: import_file(f))
```

## When to Use Transaction

```
✅ Multi-step database operations
✅ Batch imports
✅ Operations requiring rollback
✅ Complex queries with dependencies

❌ Single queries (use plain functions)
❌ Read-only operations (use Query)
```
