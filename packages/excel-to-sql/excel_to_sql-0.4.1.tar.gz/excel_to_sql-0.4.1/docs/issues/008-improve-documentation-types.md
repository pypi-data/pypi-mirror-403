# Docs: Improve Documentation and Type Hints

## Problem Description

The codebase has incomplete docstrings, inconsistent type hints, and lacks technical documentation needed for contributors and maintainers.

## Issues Identified

### 1. Missing Docstrings

**Locations:** Throughout codebase

**Examples:**
- Complex functions without docstrings
- Missing parameter documentation
- Missing return type documentation
- Inconsistent docstring formats

**Impact:**
- Difficult to understand function purpose
- No IDE autocomplete support for parameters
- Must read source code to understand behavior

### 2. Incomplete Type Hints

**Locations:** 20 files use typing but inconsistently

**Issues:**
- Some functions lack return type annotations
- Generic types not used (List, Dict, Optional)
- Complex nested types not properly typed
- Optional parameters not marked

**Examples:**
```python
# Without proper typing
def detect_patterns(df, table_name, confidence_threshold=0.7):
    # What are the types?
    pass

# Should be:
def detect_patterns(
    df: pd.DataFrame,
    table_name: str,
    confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    pass
```

### 3. Missing Technical Documentation

**Missing Documents:**
- Architecture overview
- Data flow diagrams
- Component interaction diagrams
- Internal conventions
- Development setup guide

**Impact:**
- Difficult for new contributors
- No understanding of system design
- Hard to make architectural decisions

### 4. Inconsistent Docstring Formats

**Current State:**
- Google-style in some files
- NumPy-style in others
- No docstrings in some modules

**Impact:**
- Confusing documentation
- Inconsistent IDE rendering
- Hard to maintain

## Acceptance Criteria

### Must Have (P0)
- [ ] Add docstrings to all public functions
- [ ] Add type hints to all function signatures
- [ ] Document all parameters (types, defaults)
- [ ] Document all return types
- [ ] Use consistent Google-style docstrings
- [ ] Add docstrings to all classes

### Should Have (P1)
- [ ] Add docstrings to private methods
- [ ] Add type hints for complex nested types
- [ ] Create architecture documentation
- [ ] Create data flow diagrams
- [ ] Add developer setup guide
- [ ] Document internal conventions

### Could Have (P2)
- [ ] Generate API documentation from docstrings
- [ ] Create UML diagrams
- [ ] Add sequence diagrams for workflows
- [ ] Create architecture decision records (ADRs)

## Docstring Standards

### Google-Style Format

```python
def process_file(
    file_path: Path,
    patterns: Dict[str, Any],
    quality: Dict[str, Any]
) -> Dict[str, Any]:
    """Process a single Excel file and detect patterns.

    This function analyzes an Excel file to detect patterns such as
    primary keys, foreign keys, value mappings, and split fields.
    Results are returned as a dictionary with detected patterns.

    Args:
        file_path: Path to the Excel file to process.
        patterns: Dictionary of detected patterns from PatternDetector.
            Expected keys: 'primary_key', 'foreign_keys', 'value_mappings'.
        quality: Dictionary containing quality report information.
            Expected keys: 'score', 'grade', 'issues'.

    Returns:
        Dictionary containing processing results with keys:
            - 'file_path' (str): Absolute path to processed file
            - 'file_name' (str): Name of the file
            - 'accepted_transformations' (list): List of transformation dicts
            - 'skipped' (bool): Whether the user chose to skip this file

    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If the file is not a valid Excel file.
        PermissionError: If the file cannot be read due to permissions.

    Examples:
        >>> wizard = InteractiveWizard()
        >>> result = wizard._process_file(Path("data.xlsx"), {}, {})
        >>> result["file_name"]
        'data.xlsx'
    """
```

### Type Hint Standards

```python
from typing import Dict, List, Any, Optional, Union

# Simple types
def simple_function(value: int) -> str:
    pass

# Complex types
def complex_function(
    data: Dict[str, List[int]]
) -> Dict[str, Dict[str, int]]:
    pass

# Optional parameters
def optional_function(
    required: str,
    optional: Optional[int] = None
) -> Union[str, None]:
    pass
```

## Proposed Documentation Structure

Create `docs/` with:

```
docs/
├── architecture/
│   ├── overview.md          # System architecture
│   ├── data-flow.md         # Data flow diagrams
│   ├── components/          # Component documentation
│   │   ├── cli.md
│   │   ├── sdk.md
│   │   ├── auto-pilot/
│   │   │   ├── detector.md
│   │   │   ├── recommender.md
│   │   │   ├── auto_fix.md
│   │   │   └── quality.md
│   │   └── ui.md
│   └── decisions/           # Architecture Decision Records
├── development/
│   ├── setup.md             # Development environment setup
│   ├── testing.md            # Testing guidelines
│   ├── style-guide.md       # Code style guide
│   └── conventions.md       # Coding conventions
└── api/                     # API documentation (generated)
    ├── cli.md
    ├── sdk.md
    └── auto-pilot.md
```

## Implementation Plan

### Phase 1: Add Missing Docstrings (P0)
1. Add docstrings to all public functions in CLI
2. Add docstrings to all public methods in entities
3. Add docstrings to all public methods in transformations
4. Add docstrings to all public methods in validators

### Phase 2: Add Type Hints (P0)
1. Add type hints to CLI functions
2. Add type hints to entity methods
3. Add type hints to transformation methods
4. Add type hints to validator methods
5. Fix any type hint errors

### Phase 3: Create Technical Documentation (P1)
1. Create architecture overview
2. Create component documentation
3. Add development setup guide
4. Add style guide and conventions
5. Create architecture decision records

### Phase 4: Generate API Docs (P2)
1. Set up Sphinx or MkDocs
2. Generate API documentation from docstrings
3. Deploy to documentation site

## Tools Required

### Documentation Generation
- **Sphinx** - API documentation generation
- **sphinx-autodoc** - Extract docstrings
- **sphinx-rtd-theme** - ReadTheDocs theme

### Type Checking
- **mypy** - Static type checker
- Add to CI/CD pipeline

## Examples of Improvements

### Before

```python
def detect_patterns(df, table_name, confidence_threshold=0.7):
    patterns = {}
    # ... logic ...
    return patterns
```

### After

```python
def detect_patterns(
    df: pd.DataFrame,
    table_name: str,
    confidence_threshold: float = 0.7
) -> Dict[str, Any]:
    """Detect patterns in DataFrame.

    Args:
        df: DataFrame to analyze.
        table_name: Name for the table.
        confidence_threshold: Minimum confidence for pattern detection.

    Returns:
        Dictionary with detected patterns.
    """
    patterns: Dict[str, Any] = {}
    # ... logic ...
    return patterns
```

## Testing Requirements

### Docstring Tests
```python
def test_docstring_coverage()
def test_type_hint_coverage()
def test_docstring_format()
```

### Type Checking
```python
def test_mypy_passes()
```

## Success Metrics

- **Docstring Coverage:** 100% for public APIs
- **Type Hint Coverage:** >95% for public APIs
- **mypy Score:** No type errors
- **Documentation:** Complete architecture docs

## Related Issues

- Improves: Code maintainability
- Enables: Better IDE support
- Related to: All refactoring issues
- Supports: New contributor onboarding

## Files to Create

- `docs/architecture/` (new directory)
- `docs/development/` (new directory)
- Various documentation files

## Files to Modify

- All Python files in `excel_to_sql/`
- Add `docs/` directory structure
