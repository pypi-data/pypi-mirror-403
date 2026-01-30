# Contributing to excel-to-sql

Thank you for your interest in contributing to excel-to-sql! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and constructive in all interactions.

### Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- GitHub account
- Basic understanding of Python, Git, and CLI tools

### First Time Setup

```bash
# 1. Fork the repository on GitHub
# Click the "Fork" button in the top-right corner

# 2. Clone your fork locally
git clone https://github.com/YOUR_USERNAME/excel-to-sql.git
cd excel-to-sql

# 3. Add the original repository as upstream
git remote add upstream https://github.com/wareflowx/excel-to-sql.git

# 4. Install uv (Python package manager)
# On Windows:
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# On Linux/macOS:
curl -LsSf https://astral.sh/uv/install.sh | sh

# 5. Install dependencies
uv sync

# 6. Install development dependencies
uv sync --dev
```

## Development Setup

### Creating a Feature Branch

```bash
# 1. Ensure your main branch is up-to-date
git checkout main
git fetch upstream
git rebase upstream/main

# 2. Create a new feature branch
git checkout -b feature/your-feature-name
```

### Branch Naming Conventions

- `feature/feature-name` - New features
- `fix/bug-name` - Bug fixes
- `docs/documentation-name` - Documentation updates
- `refactor/component-name` - Code refactoring
- `test/test-name` - Test additions or updates

### Development Workflow

```bash
# 1. Make your changes
# Edit files, add features, fix bugs

# 2. Run tests locally
uv run pytest

# 3. Run with coverage
uv run pytest --cov=excel_to_sql --cov-report=html

# 4. Format code
uv run ruff format excel_to_sql/ tests/

# 5. Lint code
uv run ruff check excel_to_sql/ tests/

# 6. Commit your changes
git add .
git commit -m "feat: add your feature description"

# 7. Push to your fork
git push origin feature/your-feature-name
```

## Coding Standards

### Python Style Guide

We follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines with the following tools:

#### Formatting - Ruff

```bash
# Format code
uv run ruff format excel_to_sql/ tests/

# Check formatting
uv run ruff format --check excel_to_sql/ tests/
```

#### Linting - Ruff

```bash
# Lint code
uv run ruff check excel_to_sql/ tests/

# Auto-fix linting issues
uv run ruff check --fix excel_to_sql/ tests/
```

### Code Organization

```
excel_to_sql/
├── cli.py                # CLI interface entry point
├── __init__.py           # Package exports
├── __version__.py        # Version information
├── sdk/                  # Python SDK implementation
├── entities/             # Domain entities (Project, Database, Table, etc.)
├── transformations/      # Data transformation logic
├── validators/           # Validation framework
├── profiling/            # Data quality profiling
├── auto_pilot/           # Auto-Pilot mode components
└── ui/                   # Interactive wizard UI
```

### Import Style

Use `isort` for import organization (included in ruff):

```python
# Standard library imports
import os
from pathlib import Path

# Third-party imports
import pandas as pd
from rich.console import Console

# Local imports
from excel_to_sql.entities import Project
from excel_to_sql.validators import ValidationRule
```

### Docstrings

Use Google-style docstrings:

```python
def process_file(file_path: Path, patterns: dict) -> dict:
    """Process a single Excel file and detect patterns.

    Args:
        file_path: Path to the Excel file to process.
        patterns: Dictionary of detected patterns.

    Returns:
        Dictionary containing processing results with keys:
            - 'file_path': str - Path to processed file
            - 'table_name': str - Detected table name
            - 'patterns': dict - Detected patterns

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid.
    """
```

### Type Hints

All functions should include type hints:

```python
from typing import Dict, List, Optional

def detect_patterns(
    df: pd.DataFrame,
    table_name: str,
    confidence_threshold: float = 0.7
) -> Dict[str, any]:
    """Detect patterns in DataFrame."""
    pass
```

### Error Handling

```python
# Use specific exceptions
try:
    df = pd.read_excel(file_path)
except FileNotFoundError:
    raise FileNotFoundError(f"Excel file not found: {file_path}")
except Exception as e:
    raise ValueError(f"Failed to read Excel file: {e}")

# Log errors appropriately
import logging

logger = logging.getLogger(__name__)
logger.error(f"Error processing file {file_path}: {e}")
```

## Testing Guidelines

### Test Structure

```
tests/
├── test_cli.py              # CLI command tests
├── test_sdk.py              # SDK functionality tests
├── test_transformations/    # Transformation tests
├── test_validators/         # Validator tests
├── test_auto_pilot/         # Auto-Pilot component tests
│   ├── test_detector.py     # PatternDetector tests
│   ├── test_quality.py      # QualityScorer tests
│   ├── test_recommender.py  # RecommendationEngine tests
│   ├── test_auto_fix.py     # AutoFixer tests
│   └── test_auto_fix_integration.py  # Integration tests
├── test_ui/                 # UI component tests
└── fixtures/                # Test data and fixtures
    └── auto_pilot/          # Auto-Pilot test Excel files
```

### Writing Tests

```python
import pytest
import pandas as pd
from pathlib import Path

class TestPatternDetector:
    """Unit tests for PatternDetector class."""

    def test_initialization(self) -> None:
        """Test that PatternDetector initializes correctly."""
        from excel_to_sql.auto_pilot.detector import PatternDetector

        detector = PatternDetector()
        assert detector is not None

    def test_detect_primary_key(self) -> None:
        """Test primary key detection."""
        from excel_to_sql.auto_pilot.detector import PatternDetector

        detector = PatternDetector()
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "name": ["A", "B", "C"]
        })

        patterns = detector.detect_patterns(df, "test")
        assert patterns["primary_key"] == "id"
```

### Test Coverage Requirements

- New features must have test coverage > 80%
- Critical paths must have 100% coverage
- Integration tests for complex workflows

```bash
# Run tests with coverage
uv run pytest --cov=excel_to_sql --cov-report=html

# Check coverage report
open htmlcov/index.html
```

### Fixtures

Place test data in `tests/fixtures/`:

```
tests/fixtures/
├── auto_pilot/
│   ├── commandes.xlsx
│   ├── mouvements.xlsx
│   └── produits.xlsx
└── transformations/
    └── test_data.xlsx
```

## Commit Messages

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks
- `perf` - Performance improvements

### Examples

```
feat(auto_pilot): add pattern detection for foreign keys

Implement foreign key detection based on column name patterns
and value overlap analysis with existing tables.

Closes #14

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>
```

```
fix(cli): handle Windows path separators correctly

Fix issue where Windows backslashes in paths caused errors.
Use pathlib.Path for cross-platform compatibility.

Fixes #42
```

```
docs: update README with Auto-Pilot documentation

Add comprehensive documentation for Auto-Pilot mode including:
- Pattern detection overview
- Quality scoring explanation
- Interactive wizard usage
- Code examples

Co-Authored-By: Claude Sonnet <noreply@anthropic.com>
```

## Pull Request Process

### Before Submitting

1. **Tests Pass** - All tests must pass locally
2. **Code Formatted** - Run `uv run ruff format .`
3. **Code Linted** - Run `uv run ruff check .`
4. **Coverage Adequate** - New code has >80% test coverage
5. **Documentation Updated** - Update relevant docs if needed

### Creating a Pull Request

```bash
# 1. Push your feature branch
git push origin feature/your-feature-name

# 2. Create pull request on GitHub
# Visit: https://github.com/wareflowx/excel-to-sql/compare/main...YOUR_USERNAME:excel-to-sql:feature/your-feature-name
```

### Pull Request Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Tests added/updated
- [ ] All tests pass locally
- [ ] Coverage maintained above 80%

## Checklist
- [ ] My code follows the style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
```

### Review Process

1. **Automated Checks** - CI runs tests and linting
2. **Code Review** - Maintainers review your code
3. **Feedback** - Address review comments
4. **Approval** - PR approved and merged
5. **Cleanup** - Delete your feature branch after merge

### Merging

- Maintainers will squash and merge commits
- Maintainers will update CHANGELOG.md
- Maintainers will create a release if appropriate

## Reporting Issues

### Bug Reports

Report bugs using [GitHub Issues](https://github.com/wareflowx/excel-to-sql/issues) with the following template:

```markdown
### Description
Clear description of the bug

### Reproduction Steps
1. Step 1
2. Step 2
3. ...

### Expected Behavior
What should happen

### Actual Behavior
What actually happens

### Environment
- OS: [e.g. Windows 11, macOS 14, Ubuntu 22.04]
- Python Version: [e.g. 3.11.5]
- excel-to-sql Version: [e.g. 0.3.0]

### Additional Context
Stack traces, screenshots, etc.
```

### Feature Requests

Request features using [GitHub Issues](https://github.com/wareflowx/excel-to-sql/issues):

```markdown
### Problem Description
What problem does this solve?

### Proposed Solution
How should it work?

### Alternatives Considered
What other approaches did you consider?

### Additional Context
Examples, mockups, etc.
```

## Development Resources

### Documentation

- [README](README.md) - Main documentation
- [CHANGELOG](CHANGELOG.md) - Version history
- [API Reference](docs/api/) - API documentation (planned)
- [Examples](docs/examples/) - Usage examples (planned)

### Tools Used

- [uv](https://github.com/astral-sh/uv) - Python package manager
- [pytest](https://pytest.org/) - Testing framework
- [ruff](https://docs.astral.sh/ruff/) - Linter and formatter
- [pandas](https://pandas.pydata.org/) - Data manipulation
- [Rich](https://rich.readthedocs.io/) - Terminal output
- [Typer](https://typer.tiangolo.com/) - CLI framework

## Getting Help

- **Documentation** - Start with the README and existing code
- **Issues** - Search [GitHub Issues](https://github.com/wareflowx/excel-to-sql/issues) for similar problems
- **Discussions** - Use [GitHub Discussions](https://github.com/wareflowx/excel-to-sql/discussions) for questions
- **Contact** - Open an issue for bugs or feature requests

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).

---

Thank you for contributing to excel-to-sql! Your contributions are greatly appreciated.
