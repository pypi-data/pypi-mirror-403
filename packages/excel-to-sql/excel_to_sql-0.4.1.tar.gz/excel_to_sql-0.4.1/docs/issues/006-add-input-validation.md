# Security: Add Input Validation and Sanitization

## Problem Description

The application lacks proper input validation and sanitization, creating potential security vulnerabilities when processing user-provided file paths and data.

## Security Concerns

### 1. Path Traversal Vulnerability
**Location:** All CLI commands accepting file paths

**Current Code:**
```python
# No validation of file_path parameter
path = Path(excel_path)
```

**Vulnerability:**
- User could provide `../../../../etc/passwd`
- User could access system files outside project directory
- No restriction on which files can be accessed

### 2. Unrestricted File Access
**Location:** Import, export, and magic commands

**Current Code:**
```python
# No restrictions on file reading
df = pd.read_excel(file_path)
```

**Vulnerabilities:**
- No file size limits
- No file type validation beyond extension check
- No permission validation before reading

### 3. SQL Injection Risk
**Location:** SDK query method

**Current Code:**
```python
df = sdk.query("SELECT * FROM products WHERE price > 100")
```

**Vulnerability:**
- If query string comes from user input, potential SQL injection
- No query validation or sanitization

### 4. Arbitrary Code Execution
**Location:** Calculated columns feature

**Current Code:**
```python
# Expression evaluation in calculated columns
expression = "quantity * price"
```

**Vulnerability:**
- If expression comes from user input, potential code injection
- No validation of expression content

## Impact

- **Security Risk:** High - Path traversal, unauthorized file access
- **Data Integrity:** Medium - Invalid or malicious data could be imported
- **System Stability:** Low - Could crash on very large files
- **Compliance:** Medium - May fail security audits

## Acceptance Criteria

### Must Have (P0)
- [ ] Add path validation to all file path inputs
- [ ] Resolve paths to prevent path traversal
- [ ] Add file size limits (configurable, default 100MB)
- [ ] Validate file permissions before operations
- [ ] Add file type validation beyond extension checking
- [ ] Sanitize all user inputs
- [ ] Add SQL injection prevention for query method
- [ ] Validate calculated column expressions

### Should Have (P1)
- [ ] Add file content validation (magic numbers)
- [ ] Implement user/group permission checks
- [ ] Add rate limiting for file operations
- [ ] Add audit logging for security events
- [ ] Create security policy documentation

### Could Have (P2)
- [ ] Add virus/malware scanning for uploaded files
- [ ] Implement file quarantine for suspicious files
- [ ] Add digital signature verification
- [ ] Implement content-addressable storage (CAS)

## Proposed Security Measures

### 1. Path Validation

```python
from pathlib import Path
import os

def validate_file_path(file_path: str, allowed_dir: Path = None) -> Path:
    """Validate and sanitize file path.

    Args:
        file_path: User-provided file path
        allowed_dir: Base directory (defaults to current working directory)

    Returns:
        Validated, absolute Path object

    Raises:
        ValueError: If path is invalid or outside allowed directory
    """
    path = Path(file_path).resolve()

    # Check if path is within allowed directory
    if allowed_dir:
        allowed_dir = allowed_dir.resolve()
        try:
            path.relative_to(allowed_dir)
        except ValueError:
            raise ValueError(
                f"Access denied: {file_path} is outside allowed directory"
            )

    # Check path doesn't escape to sensitive system directories
    sensitive_dirs = ['/etc', '/sys', '/proc', '/dev']
    if any(str(path).startswith(d) for d in sensitive_dirs):
        raise ValueError(f"Access denied: System directory access not allowed")

    return path
```

### 2. File Size Validation

```python
MAX_FILE_SIZE_MB = 100  # Default

def validate_file_size(file_path: Path, max_size_mb: int = MAX_FILE_SIZE_MB) -> None:
    """Validate file size before processing.

    Raises:
        ValueError: If file is too large
    """
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise ValueError(
            f"File too large: {file_size_mb:.1f}MB "
            f"(maximum: {max_size_mb}MB)"
        )
```

### 3. File Type Validation

```python
import magic

def validate_excel_file(file_path: Path) -> None:
    """Validate file is actually an Excel file.

    Raises:
        ValueError: If file is not valid Excel file
    """
    mime = magic.from_file(str(file_path), mime=True)
    valid_types = [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/vnd.ms-excel.sheet.macroEnabled.12"
    ]

    if mime not in valid_types:
        raise ValueError(
            f"Invalid file type: {mime}. "
            f"Expected Excel file (.xlsx or .xls)"
        )
```

### 4. SQL Injection Prevention

```python
def validate_sql_query(query: str) -> None:
    """Validate SQL query for safety.

    Args:
        query: SQL query string

    Raises:
        ValueError: If query contains dangerous patterns
    """
    dangerous_patterns = [
        r";\s*DROP",  # DROP TABLE
        r";\s*DELETE",  # DELETE FROM
        r";\s*INSERT",  # INSERT INTO
        r";\s*UPDATE",  # UPDATE ... SET
        r"\bEXEC\b",  # EXEC
        r"\bEVAL\b",  # EVAL
    ]

    query_upper = query.upper()
    for pattern in dangerous_patterns:
        if re.search(pattern, query_upper):
            raise ValueError(
                f"Query contains dangerous pattern: {pattern}"
            )

    # Ensure query starts with SELECT
    if not query.strip().upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed")
```

### 5. Expression Validation

```python
def validate_expression(expression: str) -> None:
    """Validate calculated column expression.

    Args:
        expression: SQL expression string

    Raises:
        ValueError: If expression contains dangerous operations
    """
    # Allow only safe operations
    safe_patterns = [
        r"^[a-zA-Z_][a-zA-Z0-9_]*\s*[+\-*/]\s*[a-zA-Z0-9_()\.]*$",
        r"^[a-zA-Z_][a-zA-Z0-9_]*$"
    ]

    # Check for function calls
    dangerous_functions = ["EXEC", "EVAL", "EXECUTE", "SCRIPT"]
    expr_upper = expression.upper()
    for func in dangerous_functions:
        if func in expr_upper:
            raise ValueError(f"Dangerous function not allowed: {func}")
```

## Implementation Plan

### Phase 1: Path Validation (P0)
1. Create security utilities module
2. Add path validation to import command
3. Add path validation to export command
4. Add path validation to magic command
5. Add tests for path validation

### Phase 2: File Validation (P0)
1. Add file size checks
2. Add file type validation
3. Add permission checks
4. Add tests for file validation

### Phase 3: Input Sanitization (P0)
1. Add SQL query validation
2. Add expression validation
3. Sanitize all string inputs
4. Add tests for input sanitization

### Phase 4: Security Documentation (P1)
1. Create SECURITY.md policy
2. Document security considerations
3. Add security guidelines to CONTRIBUTING.md
4. Add security tests to CI/CD

## Testing Requirements

### Security Tests
```python
def test_path_traversal_prevention()
def test_file_size_limit_enforcement()
def test_malicious_file_detection()
def test_sql_injection_prevention()
def test_expression_validation()
def test_permission_denied_handling()
```

### Edge Case Tests
```python
def test_symlink_attack_prevention()
def test_race_condition_handling()
def test_concurrent_access_safety()
```

## Breaking Changes

None. This adds validation only.

## Migration Guide

### For Users

No changes required for legitimate use cases.

For invalid inputs (which should not have worked):
- Path traversal attempts will now raise errors
- Oversized files will be rejected
- Invalid file types will be rejected

## Dependencies

### Required Packages
- `python-magic` - File type detection
- Existing packages (no new dependencies for basic validation)

## Related Issues

- Critical for: Production deployment
- Related to: #003 Improve Error Handling
- Improves: Overall security posture
- Blocks: Enterprise adoption

## Files to Create

- `excel_to_sql/security.py` (new)
- `tests/test_security.py` (new)
- `SECURITY.md` (new)

## Files to Modify

- `excel_to_sql/cli.py` - Add validation to all file operations
- `excel_to_sql/sdk/client.py` - Add query validation
- `excel_to_sql/transformations/calculated.py` - Add expression validation
- All modules accepting user input

## Security Policy

### Reporting Vulnerabilities

If you discover a security vulnerability, please:

1. Do NOT open a public issue
2. Email: [security contact email]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if known)

### Response Timeline

- Initial response: Within 48 hours
- Fix timeline: Based on severity
- Disclosure: Coordinated disclosure after fix

## References

- OWASP Path Traversal: https://owasp.org/www-community/attacks/Path_Traversal
- OWASP SQL Injection: https://owasp.org/www-community/attacks/SQL_Injection
- CWE-20: Improper Input Validation
- OWASP Input Validation Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html
