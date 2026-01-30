# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Documentation website (Fumadocs)
- Enhanced API reference with auto-generation
- Performance optimizations for large datasets
- Additional validation rules

## [0.3.0] - 2025-01-22

### Added
- **Auto-Pilot Mode** - Zero-configuration import with intelligent pattern detection
  - PatternDetector - Automatic detection of primary keys, foreign keys, value mappings, and split fields
  - QualityScorer - Multi-dimensional data quality analysis with letter grades (A-D)
  - RecommendationEngine - Prioritized, actionable recommendations (HIGH/MEDIUM/LOW)
  - AutoFixer - Automatic correction of data quality issues with backup system
  - InteractiveWizard - Step-by-step guided configuration workflow
- **CLI Enhancement** - `magic` command for automatic configuration
  - `--interactive` flag for guided wizard mode
  - `--dry-run` flag for analysis without generation
- **French Code Support** - Automatic translation (ENTRÉE→inbound, SORTIE→outbound, ACTIF→active, INACTIF→inactive, etc.)
- **Split Field Detection** - Intelligent COALESCE for redundant status columns
- **Auto-Fix Capabilities** - One-click corrections for null values, French codes, and split fields
- **Backup System** - Automatic backups before modifications with rotation (max 5)

### Changed
- **README** - Complete restructure for professional documentation
  - Removed emojis for professional appearance
  - Added Table of Contents for navigation
  - Reorganized sections with clear hierarchy
  - Reduced from 705 to 588 lines (-16.5%)
- **Improved** - Terminal output formatting with Rich library
- **Enhanced** - Error handling and user feedback throughout CLI

### Fixed
- Windows compatibility issues with tempfile handling
- Unicode character encoding issues (cp1252 console support)
- Test path duplication in integration tests
- Backup timestamp collision in test suite

### Testing
- Added 143 tests for Auto-Pilot components
- Integration tests with real Excel fixtures
- Achieved >85% coverage on core Auto-Pilot modules
- Total: 200+ tests across all features

### Documentation
- Comprehensive Auto-Pilot documentation in README
- Component API documentation (PatternDetector, QualityScorer, RecommendationEngine, AutoFixer, InteractiveWizard)
- Usage examples and best practices
- Interactive workflow examples

## [0.2.0] - 2024-XX-XX

### Added
- **Value Mapping** - Standardize data values during import (e.g., "NY" → "New York")
- **Calculated Columns** - Create derived columns using SQL expressions
- **Custom Validators** - Extensible validation system with 7 validator types
- **Reference/Lookup Validation** - Foreign key validation against lookup tables
- **Data Profiling** - Automatic quality analysis with detailed HTML reports
- **Multi-Sheet Import** - Import multiple sheets in one operation
- **Multi-Sheet Export** - Export multiple tables/sheets to single Excel file
- **Incremental/Delta Import** - Only process changed files using content hashing
- **Data Validation Rules** - Declarative rule-based validation system
- **Pre/Post Hooks** - Execute custom code during import/export pipeline
- **Python SDK** - Full-featured programmatic API for all operations
- **Metadata & Tags** - Tag and categorize imports with rich metadata

### Testing
- Added 68 tests with comprehensive coverage for all new features

## [0.1.0] - 2024-XX-XX

### Added
- Initial release
- Basic Excel to SQLite import functionality
- Automatic schema detection
- UPSERT logic for duplicate handling
- Data cleaning (whitespace trimming, empty row removal)
- Rich terminal display with colored output
- Project initialization and management
- Import history tracking
- Basic configuration system

### Features
- CLI commands: `init`, `import`, `export`, `config`, `status`, `history`
- SQLite database integration
- Excel file support (.xlsx, .xls)
- Multi-sheet support

## [0.1.1] - 2024-XX-XX

### Fixed
- Minor bug fixes
- Improved error messages

---

## Versioning Scheme

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0) - Incompatible API changes
- **MINOR** (0.X.0) - Backwards-compatible functionality additions
- **PATCH** (0.0.X) - Backwards-compatible bug fixes

## Release Types

- **Stable Release** - Versioned releases (0.1.0, 0.2.0, etc.)
- **Development Branch** - `main` branch for ongoing development
- **Feature Branches** - `feature/feature-name` for new features
- **Release Branches** - `release/X.Y.Z` for release preparation

## Changelog Maintenance

When adding changes to the changelog:

1. Add entries under the `[Unreleased]` section
2. Use the following categories:
   - `Added` - New features
   - `Changed` - Changes to existing functionality
   - `Deprecated` - Soon-to-be removed features
   - `Removed` - Removed features
   - `Fixed` - Bug fixes
   - `Security` - Security vulnerability fixes
3. When releasing, move entries to a new version section
4. Include release date in ISO 8601 format (YYYY-MM-DD)
5. Link to relevant issues and pull requests when applicable

## References

- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
- [Semantic Versioning](https://semver.org/spec/v2.0.0.html/)
- [How to Changelog](https://howtochangelog.com/)
