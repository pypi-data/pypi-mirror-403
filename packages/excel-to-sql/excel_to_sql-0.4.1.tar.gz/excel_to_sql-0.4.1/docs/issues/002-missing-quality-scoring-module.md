# Implement Missing QualityScorer Module

## Problem Description

The CLI imports `excel_to_sql.auto_pilot.quality` (line 471 in `cli.py`) but this module does not exist in the codebase. This will cause runtime errors when certain code paths are executed.

**Current Issue:**
```python
# In cli.py line 471
from excel_to_sql.auto_pilot.quality import QualityScorer
```

However, the file `excel_to_sql/auto_pilot/quality.py` does not exist. Only `detector.py`, `recommender.py`, and `auto_fix.py` are present.

## Impact

- **Runtime Failure:** Application crashes when quality scoring features are accessed
- **Broken Magic Command:** Auto-Pilot mode depends on quality scoring
- **Test Failures:** Some tests may be skipped or failing silently

## Root Cause

The QualityScorer module was planned as part of the Auto-Pilot EPIC but was never implemented, despite being imported and referenced throughout the codebase.

## Evidence

**Import in CLI:**
```python
# excel_to_sql/cli.py:471
from excel_to_sql.auto_pilot.quality import QualityScorer
```

**Usage in CLI:**
```python
# excel_to_sql/cli.py:579
quality_report = scorer.generate_quality_report(df, table_name)
```

**Documentation References:**
- README mentions QualityScorer in Auto-Pilot components section
- CHANGELOG mentions QualityScorer as a delivered feature
- CONTRIBUTING.md lists QualityScorer in examples

**Expected Module Interface:**
Based on usage throughout the codebase, the QualityScorer should provide:

```python
class QualityScorer:
    def generate_quality_report(
        self,
        df: pd.DataFrame,
        table_name: str
    ) -> Dict[str, Any]:
        """Generate quality report for DataFrame.

        Returns:
            Dict with keys:
                - score (int): 0-100 quality score
                - grade (str): Letter grade A-D
                - issues (list): List of detected issues
                - column_stats (dict): Per-column statistics
        """
```

## Acceptance Criteria

### Must Have (P0)
- [ ] Create `excel_to_sql/auto_pilot/quality.py` module
- [ ] Implement QualityScorer class with `generate_quality_report()` method
- [ ] Return quality score (0-100) with letter grade (A-D)
- [ ] Detect common quality issues:
  - High null percentages
  - Duplicate values in primary key columns
  - Type mismatches
  - Empty columns
  - Outliers
- [ ] Include per-column statistics (null count, null percentage, unique count)
- [ ] Add type hints to all methods
- [ ] Add comprehensive docstrings
- [ ] Add unit tests with >85% coverage

### Should Have (P1)
- [ ] Add configurable quality thresholds
- [ ] Support custom quality checks
- [ ] Add integration tests with real Excel fixtures
- [ ] Include recommendations for quality improvements

### Could Have (P2)
- [ ] Add quality trend analysis (compare with previous imports)
- [ ] Generate HTML quality reports
- [ ] Add visualization of quality metrics

## Testing Requirements

### Unit Tests
```python
def test_quality_scorer_initialization()
def test_generate_quality_report_high_quality()
def test_generate_quality_report_low_quality()
def test_detect_null_values()
def test_detect_duplicates()
def test_per_column_statistics()
def test_quality_score_calculation()
def test_grade_assignment()
```

### Integration Tests
- Test with real Excel fixtures from `tests/fixtures/auto_pilot/`
- Verify compatibility with PatternDetector
- Verify compatibility with RecommendationEngine

## Implementation Notes

### Quality Score Calculation

Suggested algorithm:
```
Base Score: 100

Deductions:
- Null values: -0.5 per percentage point over 10%
- Duplicates: -2 per duplicate in PK column
- Type mismatches: -1 per column
- Empty columns: -5 per column
- Outliers: -0.1 per outlier (3 sigma)

Grade Assignment:
- A: 90-100
- B: 75-89
- C: 60-74
- D: <60
```

### Per-Column Statistics

For each column, collect:
- Null count
- Null percentage
- Unique count
- Data type
- Sample values (top 5)

## Dependencies

- Requires: pandas, numpy
- Related modules: PatternDetector, RecommendationEngine

## Breaking Changes

None. This adds missing functionality.

## Related Issues

- Depends on: Auto-Pilot EPIC structure
- Blocks: Complete Auto-Pilot functionality
- Related to: #14 Pattern Detection, #20 Recommendations

## References

- Current import location: `excel_to_sql/cli.py:471`
- Usage location: `excel_to_sql/cli.py:579`
- Documentation: README.md Auto-Pilot section
