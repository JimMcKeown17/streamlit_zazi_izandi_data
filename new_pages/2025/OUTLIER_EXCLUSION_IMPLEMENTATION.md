# Outlier Exclusion Filter Implementation

## Summary

Successfully implemented outlier exclusion functionality in `nmb_endline_cohort_analysis_exclude.py`. This allows users to filter out problematic data records using a toggle control at the top of the page.

## What Was Implemented

### 1. Helper Functions Added

#### `merge_baseline_endline(baseline_df, endline_df)`
- Merges baseline and endline assessment data using Name + Grade + School matching keys
- Performs left merge to keep all endline records
- Calculates improvement scores (Endline - Baseline)
- Adds `has_baseline_match` flag for tracking matched records

#### `apply_outlier_exclusions(df, baseline_df=None)`
- Creates boolean exclusion flags for three criteria:
  - **Filter 1**: Grade 1 children with baseline score >= 40
  - **Filter 2**: Children with score decline >= 10 letters
  - **Filter 3**: Specific underperforming EAs (14 names)
- Combines flags into single `exclude_outlier` column
- Returns dataframe with all exclusion flags added

### 2. UI Toggle Control

Added after the "11+ sessions" toggle:
- Toggle label: "🚫 Exclude Outlier Data"
- Default: OFF (no exclusions applied)
- Help text explains the three exclusion criteria
- Key: `exclude_outliers_toggle`

### 3. Exclusion Logic Flow

When toggle is ON:
1. Loads baseline data from CSV
2. Merges baseline and endline data
3. Applies all three exclusion flags
4. Calculates exclusion counts for each criterion
5. Filters out records where `exclude_outlier == True`
6. Displays summary metrics showing:
   - Number excluded by each criterion
   - Total excluded count and percentage
   - Remaining assessment count

### 4. Data Explorer Tab Updates

Updated the "Baseline vs Endline Matching Analysis" section to handle two scenarios:

**Scenario A: Outlier exclusions applied**
- Detects baseline data already merged (checks for `Baseline Score` and `has_baseline_match` columns)
- Shows simplified matched data view
- Displays improvement statistics, distributions, and by-grade breakdowns
- Info message: "✅ Baseline data already merged due to outlier exclusion filter being active."

**Scenario B: No outlier exclusions**
- Uses original matching logic
- Loads baseline data fresh
- Performs merge in the tab
- Full matching analysis as before

### 5. Exclusion Criteria Details

#### Filter 1: High-Performing Grade 1s
- **Logic**: `(Grade == 'Grade 1') AND (Baseline Score >= 40)`
- **Rationale**: These children were already reading at grade level and don't represent typical program impact
- **Applies to**: Both baseline and endline records

#### Filter 2: Score Decline Anomalies
- **Logic**: `(Improvement <= -10)` where Improvement = Endline - Baseline
- **Rationale**: Score drops of 10+ letters indicate data quality issues (assessment errors, wrong child, etc.)
- **Applies to**: Only matched records (requires baseline data)

#### Filter 3: Underperforming EAs
- **Logic**: EA name in excluded list
- **EAs excluded** (14 total):
  - Sinoxolo Sani
  - Thulani Mthombeni
  - Asanda Betsha
  - Lizalithetha Mhlobo
  - Siphosethu Mampangashe
  - Hlumela Ntloko
  - Lerato Njovane
  - Ntombizine Goqwana
  - Zikhona Tshakweni
  - Lucia Jacobs
  - Khahliso Sabasaba
  - Lithemba Mdunyelwa
  - Raeesa Ishmael
  - Kanyisa Matshaya
- **Rationale**: These EAs had implementation quality issues
- **Applies to**: All records from these EAs

### 6. Visual Display

When exclusions are active, shows 4-column metrics:
```
┌─────────────────────────┬─────────────────────────┬─────────────────────────┬─────────────────────────┐
│ Grade 1 (baseline ≥ 40) │ Score Decline ≥ 10      │ Excluded EAs            │ Total Excluded          │
│ XXX (excluded)          │ XXX (excluded)          │ XXX (excluded)          │ XXX (X.X% of data)      │
└─────────────────────────┴─────────────────────────┴─────────────────────────┴─────────────────────────┘
```

## Files Modified

- **`new_pages/2025/nmb_endline_cohort_analysis_exclude.py`** - All implementation in this file
- **`new_pages/2025/nmb_endline_cohort_analysis.py`** - Original file unchanged (as requested)

## Technical Notes

### Data Flow
1. Load endline from database
2. Apply 11+ sessions filter (if toggled)
3. If outlier exclusions toggled:
   - Load baseline from CSV
   - Merge on Name+Grade+School
   - Apply exclusion flags
   - Filter out excluded records
4. Pass filtered `df` to all tabs
5. All tabs automatically respect the filtering

### Matched vs Unmatched Records
- Filter #1 (high baseline) applies to all records with baseline data
- Filter #2 (score decline) only applies to matched records (requires both baseline and endline)
- Filter #3 (EA exclusion) applies to all records regardless of matching
- Unmatched endline records won't be affected by Filter #2 (no improvement calculation possible)

### Caching Considerations
- `load_baseline_data()` is already cached (TTL: 1 hour)
- `merge_baseline_endline()` is not cached (runs fresh when toggle enabled)
- Processing time added: ~1-2 seconds for merge operation

### Performance
- Merge operation: O(n) where n = number of endline records
- Three boolean filters: O(n) each, trivial performance impact
- Overall overhead: Minimal, ~1-2 seconds added when toggle is ON

## Usage Instructions

1. Open the page: `NMB 2025 Endline Analysis (Exclude)`
2. Toggle ON: "🚫 Exclude Outlier Data"
3. Wait for baseline data to load and merge (~1-2 seconds)
4. View exclusion summary showing counts for each criterion
5. All charts, tables, and analyses now reflect filtered data
6. Toggle OFF to return to full dataset

## Testing Recommendations

1. **Toggle functionality**: Verify toggle turns ON/OFF correctly
2. **Data counts**: Check that exclusion counts are non-zero and reasonable
3. **Filter #1**: Verify Grade 1 with baseline >= 40 are excluded
4. **Filter #2**: Check that large negative improvements are excluded
5. **Filter #3**: Confirm records from excluded EAs don't appear
6. **Data Explorer**: Verify baseline matching section handles both scenarios
7. **All tabs**: Confirm filtering applies across all tabs consistently
8. **Toggle OFF**: Ensure full data returns when toggle is disabled

## Future Enhancements

Potential improvements for database implementation:
1. Move exclusion flags into database table
2. Pre-calculate matched improvements in database
3. Add UI for customizing EA exclusion list
4. Add UI for adjusting threshold values (40 LPM, -10 decline)
5. Add "Preview" mode to see what would be excluded before applying
6. Export functionality for excluded records (for review)

## Date Implemented

December 3, 2025

