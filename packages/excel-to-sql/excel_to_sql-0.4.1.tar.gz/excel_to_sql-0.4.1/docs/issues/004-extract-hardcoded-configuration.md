# Refactor: Extract Hardcoded Configuration Values

## Problem Description

The codebase contains numerous hardcoded values throughout the CLI and modules, making the application difficult to configure and maintain. These values should be extracted into configuration files or constants.

## Hardcoded Values Found

### 1. File Extensions (CLI)
**Location:** `excel_to_sql/cli.py`

```python
# Line 100
if path.suffix.lower() not in {".xlsx", ".xls"}:
```

**Issue:** Extensions are hardcoded in multiple places.

### 2. Default Database Path
**Location:** `excel_to_sql/cli.py`

```python
# Line 50
db_path: str = Option("data/excel-to-sql.db", "--db-path")
```

**Issue:** Default path hardcoded as default parameter value.

### 3. Default Sheet Name
**Location:** Multiple locations

```python
# Throughout the code
sheet_name = "Sheet1"
```

**Issue:** Assumption about Excel sheet names.

### 4. Quality Thresholds
**Location:** `excel_to_sql/auto_pilot/recommender.py`

```python
# Hardcoded thresholds
if null_percentage > 10:  # Magic number
if null_percentage > 50:
```

**Issue:** Thresholds are not configurable.

### 5. Priority Mappings
**Location:** `excel_to_sql/auto_pilot/recommender.py`

```python
# Priority mappings hardcoded
priority_map = {
    "duplicate_pk": Priority.HIGH,
    "null_values": Priority.HIGH,
    # ...
}
```

**Issue:** Cannot customize priority levels.

### 6. Backup Configuration
**Location:** `excel_to_sql/auto_pilot/auto_fix.py`

```python
backup_dir = Path(".excel-to-sql/backups")
MAX_BACKUPS = 5
```

**Issue:** Backup paths and limits are hardcoded.

### 7. Console Formatting
**Location:** Throughout CLI

```python
# Hardcoded colors and styles
"[red]Error:[/red]"
"[green]OK[/green]"
"[yellow]Warning:[/yellow]"
```

**Issue:** Colors are hardcoded, no theme support.

## Impact

- **Maintainability:** Difficult to change behavior without code changes
- **Flexibility:** Users cannot configure basic settings
- **Testing:** Hardcoded values complicate testing
- **Reusability:** Code cannot be reused in different contexts

## Acceptance Criteria

### Must Have (P0)
- [ ] Create configuration constants module `excel_to_sql/config.py`
- [ ] Extract all hardcoded values to constants
- [ ] Replace hardcoded values with configuration references
- [ ] Add environment variable support for critical paths
- [ ] Create default configuration file
- [ ] Add type hints for all configuration values

### Should Have (P1)
- [ ] Support configuration file (YAML/TOML)
- [ ] Add configuration validation
- [ ] Allow runtime configuration changes
- [ ] Document all configuration options
- [ ] Add configuration examples

### Could Have (P2)
- [ ] Support user-specific configuration (~/.config/excel-to-sql/)
- [ ] Add configuration schema validation
- [ ] Implement configuration reload
- [ ] Add configuration migration support

## Proposed Configuration Structure

### Constants Module

```python
# excel_to_sql/config.py
from pathlib import Path
from typing import Set, Dict

# File Extensions
SUPPORTED_EXCEL_EXTENSIONS: Set[str] = {".xlsx", ".xls"}
DEFAULT_EXCEL_EXTENSION: str = ".xlsx"

# Database
DEFAULT_DATABASE_PATH: str = "data/excel-to-sql.db"
DEFAULT_DATABASE_NAME: str = "excel-to-sql.db"

# Project Structure
DEFAULT_CONFIG_DIR: str = "config"
DEFAULT_IMPORTS_DIR: str = "imports"
DEFAULT_EXPORTS_DIR: str = "exports"
DEFAULT_DATA_DIR: str = "data"

# Excel Defaults
DEFAULT_SHEET_NAME: str = "Sheet1"
MAX_FILE_SIZE_MB: int = 100  # Maximum file size in MB

# Quality Thresholds
QUALITY_THRESHOLD_HIGH: float = 90.0
QUALITY_THRESHOLD_MEDIUM: float = 75.0
QUALITY_THRESHOLD_LOW: float = 60.0
NULL_PERCENTAGE_HIGH: float = 10.0
NULL_PERCENTAGE_MEDIUM: float = 50.0

# Backup Configuration
BACKUP_DIR_NAME: str = ".excel-to-sql/backups"
DEFAULT_MAX_BACKUPS: int = 5

# Console Colors (for Rich library)
COLOR_ERROR: str = "red"
COLOR_SUCCESS: str = "green"
COLOR_WARNING: str = "yellow"
COLOR_INFO: str = "cyan"
COLOR_DIM: str = "dim"

# Auto-Pilot
AUTOPILOT_CONFIDENCE_THRESHOLD: float = 0.7
DETECTION_SAMPLE_SIZE: int = 1000
```

### Configuration File Support

Create `excel-to-sql.toml`:

```toml
[database]
path = "data/excel-to-sql.db"
name = "excel-to-sql"

[project]
config_dir = "config"
imports_dir = "imports"
exports_dir = "exports"
data_dir = "data"

[excel]
supported_extensions = [".xlsx", ".xls"]
default_extension = ".xlsx"
default_sheet = "Sheet1"
max_file_size_mb = 100

[quality]
threshold_high = 90.0
threshold_medium = 75.0
threshold_low = 60.0
null_percentage_high = 10.0
null_percentage_medium = 50.0

[backup]
directory = ".excel-to-sql/backups"
max_backups = 5

[console.colors]
error = "red"
success = "green"
warning = "yellow"
info = "cyan"
dim = "dim"
```

## Implementation Plan

### Phase 1: Create Constants Module (P0)
1. Create `excel_to_sql/config.py`
2. Define all constant values
3. Add type hints
4. Add docstrings

### Phase 2: Replace Hardcoded Values (P0)
1. Update CLI to use constants
2. Update auto_pilot modules
3. Update other modules
4. Test all changes

### Phase 3: Add Configuration File Support (P1)
1. Add TOML dependency
2. Implement config file loader
3. Add environment variable overrides
4. Add configuration validation

### Phase 4: Documentation (P1)
1. Document all configuration options
2. Add configuration examples
3. Update README with configuration section

## Testing Requirements

### Unit Tests
```python
def test_default_constants_loaded()
def test_custom_configuration_loading()
def test_environment_variable_overrides()
def test_configuration_validation()
def test_configuration_file_not_found()
```

### Integration Tests
- Test application with custom configuration
- Test with environment variables
- Test configuration precedence (file > env > defaults)

## Breaking Changes

None. This is internal refactoring that doesn't change public API.

## Migration Guide

### For Users

No changes required. All defaults remain the same.

### For Developers

Before:
```python
if path.suffix.lower() not in {".xlsx", ".xls"}:
```

After:
```python
from excel_to_sql.config import SUPPORTED_EXCEL_EXTENSIONS
if path.suffix.lower() not in SUPPORTED_EXCEL_EXTENSIONS:
```

## Related Issues

- Improves: #003 Improve Error Handling
- Related to: Configuration management
- Blocks: Advanced customization features

## Files to Modify

- `excel_to_sql/config.py` (create)
- `excel_to_sql/cli.py` (major updates)
- `excel_to_sql/auto_pilot/detector.py`
- `excel_to_sql/auto_pilot/recommender.py`
- `excel_to_sql/auto_pilot/auto_fix.py`
- `excel_to_sql/entities/project.py`

## References

- Hardcoded values found in:
  - `cli.py`: Lines 100, 112, 50, etc.
  - `recommender.py`: Quality thresholds
  - `auto_fix.py`: Backup configuration
  - Multiple modules: Default values, file extensions
