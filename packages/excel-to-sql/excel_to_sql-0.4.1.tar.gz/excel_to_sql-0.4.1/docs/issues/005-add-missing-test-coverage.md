# Test: Add Missing Test Coverage for SDK, Models, and Config

## Problem Description

Several critical modules lack dedicated test coverage, reducing confidence in code quality and making refactoring risky.

### Untested Modules

#### 1. SDK Client (`sdk/client.py`)
- **Current Status:** No dedicated test file
- **Importance:** Primary API for programmatic access
- **Risk:** High - Core functionality untested

#### 2. Mapping Models (`models/mapping.py`)
- **Current Status:** No dedicated test file
- **Importance:** Data validation and serialization
- **Risk:** Medium - Data integrity

#### 3. Configuration Management
- **Current Status:** No configuration tests
- **Importance:** Project setup and initialization
- **Risk:** Medium - Setup failures

#### 4. Main Entry Point (`__main__.py`)
- **Current Status:** No test file
- **Importance:** CLI entry point
- **Risk:** Low - Simple wrapper

### Coverage Gaps

#### Low Coverage Areas
- `ui/interactive.py` - Only 54% coverage
  - Interactive workflows difficult to test
  - User input simulation required
  - Rich terminal output hard to verify

- Error handling edge cases
  - File permission errors
  - Corrupted Excel files
  - Database connection failures
  - Invalid user input

## Impact

- **Refactoring Risk:** Untested code cannot be safely refactored
- **Bug Detection:** Bugs in core SDK may go unnoticed
- **Regression Risk:** Changes may break existing functionality
- **Confidence:** Low confidence in untested modules

## Current Test Coverage by Module

| Module | Coverage | Status |
|--------|----------|--------|
| `entities/project.py` | 97% | ✅ Excellent |
| `entities/database.py` | 34% | ⚠️ Needs improvement |
| `entities/dataframe.py` | 30% | ⚠️ Needs improvement |
| `entities/excel_file.py` | 27% | ⚠️ Needs improvement |
| `entities/table.py` | 26% | ⚠️ Needs improvement |
| `transformations/mapping.py` | 37% | ⚠️ Needs improvement |
| `transformations/hooks.py` | 48% | ⚠️ Acceptable |
| `validators/custom.py` | 21% | ⚠️ Needs improvement |
| `auto_pilot/detector.py` | 97% | ✅ Excellent |
| `auto_pilot/quality.py` | N/A | ❌ Missing module |
| `auto_pilot/recommender.py` | 92% | ✅ Excellent |
| `auto_pilot/auto_fix.py` | 88% | ✅ Excellent |
| `ui/interactive.py` | 54% | ⚠️ Needs improvement |
| **sdk/client.py** | **0%** | **❌ No tests** |
| **models/mapping.py** | **0%** | **❌ No tests** |
| **__main__.py** | **0%** | **❌ No tests** |
| `config/` | **0%** | **❌ No tests** |

## Acceptance Criteria

### Must Have (P0)
- [ ] Create `tests/test_sdk.py` with SDK client tests
- [ ] Create `tests/test_models.py` with mapping model tests
- [ ] Create `tests/test_config.py` with configuration tests
- [ ] Create `tests/test_main.py` for entry point tests
- [ ] Achieve >80% coverage for SDK client
- [ ] Achieve >80% coverage for mapping models
- [ ] Test all public API methods
- [ ] Test error conditions

### Should Have (P1)
- [ ] Improve coverage for low-coverage entities modules (>80%)
- [ ] Add edge case tests for error handling
- [ ] Add integration tests for SDK workflows
- [ ] Test configuration loading and validation
- [ ] Add performance tests for large datasets

### Could Have (P2)
- [ ] Add property-based tests for models
- [ ] Test SDK with real Excel files
- [ ] Add stress tests for concurrent operations
- [ ] Test CLI entry point with various arguments

## Proposed Test Structure

### SDK Client Tests (`tests/test_sdk.py`)

```python
class TestExcelToSqliteClient:
    """Test suite for SDK client."""

    def test_initialization()
    def test_import_excel_basic()
    def test_import_excel_with_tags()
    def test_import_excel_with_transformations()
    def test_import_excel_file_not_found()
    def test_query_data()
    def test_query_invalid_sql()
    def test_profile_table()
    def test_profile_table_not_found()
    def test_export_to_excel()
    def test_export_invalid_table()
    def test_export_multi_sheet()
```

### Mapping Models Tests (`tests/test_models.py`)

```python
class TestMappingModels:
    """Test suite for mapping models."""

    def test_column_mapping_model()
    def test_value_mapping_model()
    def test_validation_rule_model()
    def test_configuration_model()
    def test_model_serialization()
    def test_model_validation()
    def test_model_defaults()
```

### Configuration Tests (`tests/test_config.py`)

```python
class TestProjectConfiguration:
    """Test suite for configuration management."""

    def test_project_initialization()
    def test_config_directory_creation()
    def test_config_file_loading()
    def test_config_file_not_found()
    def test_config_validation()
    def test_custom_config_path()
    def test_environment_variable_overrides()
```

## Testing Requirements

### SDK Client Tests

**Must Cover:**
- Initialize SDK with default and custom settings
- Import Excel files (success and failure cases)
- Query data with SQL
- Profile table quality
- Export to Excel (single and multi-sheet)
- Error handling for all operations

**Mock Requirements:**
- Mock database operations
- Mock file system operations
- Mock pandas DataFrame operations

### Models Tests

**Must Cover:**
- Model creation and validation
- Serialization/deserialization
- Type coercion and conversion
- Edge cases (empty values, null values, invalid types)

### Configuration Tests

**Must Cover:**
- Project initialization
- Configuration file parsing
- Default configuration
- Custom configuration overrides
- Configuration validation

## Implementation Notes

### Test Fixtures Required

Create shared test fixtures in `tests/conftest.py`:
- Sample Excel files
- Sample DataFrames
- Mock database
- Temporary directories

### Test Data

Add test data in `tests/fixtures/`:
- Sample Excel files (various sizes and complexity)
- Invalid Excel files (for error testing)
- Sample configuration files

### Coverage Goals

- **Overall target:** >85% coverage
- **Critical modules:** >90% coverage (SDK, models, config)
- **Acceptable:** >75% for UI/interactive modules

## Dependencies

### Required Packages
- `pytest` - Testing framework
- `pytest-cov` - Coverage plugin
- `pytest-mock` - Mocking support
- `pyfakefs` - Fake filesystem for file operations

## Related Issues

- Depends on: #002 Missing QualityScorer Module
- Improves: Overall code quality and confidence
- Enables: Safe refactoring
- Related to: Code quality and maintainability

## Files to Create

- `tests/test_sdk.py` (new)
- `tests/test_models.py` (new)
- `tests/test_config.py` (new)
- `tests/test_main.py` (new)
- `tests/conftest.py` (enhance)

## Files to Modify

- `tests/conftest.py` - Add shared fixtures
- `tests/__init__.py` - Update if needed
- `.coveragerc` - Adjust coverage configuration if needed

## Success Metrics

- SDK client coverage: >80%
- Models coverage: >80%
- Configuration coverage: >80%
- Overall coverage: >85%
- All tests passing
- No test skipped or xfailed

## References

- Current test coverage report: `htmlcov/index.html`
- Uncovered modules:
  - `sdk/client.py` (0%)
  - `models/mapping.py` (0%)
  - `__main__.py` (0%)
  - `config/` directory (0%)
