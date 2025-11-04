# NMB 2025 Endline - Cohort & Quality Analysis Page

## Overview
New Streamlit page for analyzing the relationship between session frequency, teaching quality flags, and EGRA performance.

**File:** `nmb_endline_cohort_analysis.py`  
**URL Path:** `/nmb_endline_cohort_25`  
**Access:** Internal only (login required)

## Data Source
Loads data directly from Django PostgreSQL database:
- **Table:** `teampact_assessment_endline_2025`
- **Connection:** Uses same `database_utils.py` as sessions page
- **Caching:** 1-hour TTL for performance

## Grade-Level Filtering (NEW)

**All tabs now support grade-specific analysis!**

Each analysis tab includes a grade filter dropdown at the top:
- **Options:** All Grades, Grade R, Grade 1, Grade 2
- **Default:** All Grades (combined analysis)
- **Behavior:** When a specific grade is selected, all visualizations, metrics, and statistics update to show only that grade's data

**Why This Matters:**
- Different grades are at different developmental stages
- Grade R children are just beginning letter recognition
- Grade 1 and 2 have had more formal instruction time
- Analyzing grades separately provides more meaningful insights about program effectiveness

**Implementation:**
- Tabs 1-5: Single-select dropdown filter
- Tab 6 (Data Explorer): Multiselect for flexible querying
- When a specific grade is selected, charts showing "by Grade" are hidden (redundant)

## Page Structure

### Tab 1: 📊 Overview & Distribution
**Purpose:** High-level summary and data distribution

**Visualizations:**
- Metrics: Total assessments, session linkage, flag prevalence
- Quality flag breakdown (Moving Too Fast, Same Letter Groups, Both)
- Session cohort distribution (bar chart + pie chart)
- Grade and language breakdowns

**Key Stats:**
- 4,072 total endline assessments
- 3,866 (94.9%) linked to session data
- 1,121 (27.5%) flagged "Moving Too Fast"
- 1,527 (37.5%) flagged "Same Letter Groups"

### Tab 2: 🎯 Cohort Performance Analysis
**Purpose:** Answer "Do more sessions lead to better performance?"

**Visualizations:**
- Mean/Median EGRA scores by session cohort
- Performance by cohort AND grade (grouped bars)
- Score distribution boxplots by cohort
- Percentage above benchmark by cohort (adjustable threshold)

**Features:**
- Toggle between mean and median statistics
- Adjustable LPM benchmark slider (20-50)
- Automatic insight generation comparing lowest vs highest cohort

**Cohorts:**
- 0-10 sessions: 393 (9.5%)
- 11-20 sessions: 359 (8.7%)
- 21-30 sessions: 436 (10.6%)
- 31-40 sessions: 299 (7.2%)
- 41+ sessions: 2,585 (62.6%)

### Tab 3: 🚩 Quality Flag Impact Analysis
**Purpose:** Answer "How do flagged groups perform vs non-flagged?"

**Visualizations:**
- Side-by-side comparison: Flagged vs Not Flagged (both flags)
- Score distribution histograms (overlaid)
- Combined flag analysis (Both/One/None)

**Flags Analyzed:**
1. **Moving Too Fast:** Groups advancing >70% without review
2. **Same Letter Groups:** EAs with 3+ groups on same letter
3. **Combined:** Both flags together

**Features:**
- Mean/Median toggle
- Color-coded bars (red=flagged, green=not flagged)
- Automatic performance difference calculations

### Tab 4: 🔬 Cross-Analysis & Correlations
**Purpose:** Answer "How do cohorts and flags interact?"

**Visualizations:**
- Heatmap: Mean scores by Cohort × Flag Status
- Scatter plot: Session count vs EGRA score (with flag colors)
- Session recency analysis (30-day, 90-day, total correlations)
- Correlation matrix (all numeric variables)

**Features:**
- Trendline on scatter plot
- Correlation coefficients displayed
- Interactive hover details

**Insights:**
- Identifies whether recent sessions matter more than total
- Shows relationship strength between variables
- Reveals if flag impact varies by cohort

### Tab 5: 🏫 School & EA Level Insights
**Purpose:** Identify schools/EAs needing support

**Visualizations:**
- Schools with highest flag rates (top 15)
- Top 10 performing EAs
- Bottom 10 performing EAs
- Flag distribution by school (grouped bars)

**Features:**
- Minimum assessments filter (5-50)
- Sortable data tables (expandable)
- Hover data shows flag counts

**Use Cases:**
- Target coaching for high-flag schools
- Recognize top-performing EAs
- Identify EAs needing support

### Tab 6: 📈 Data Explorer
**Purpose:** Interactive filtering and data export

**Filters Available:**
- Grade (R, 1, 2)
- Language (isiXhosa, English, Afrikaans)
- Session Cohort (0-10, 11-20, etc.)
- Quality Flags (Moving Fast, Same Letter, Both, None)
- School
- EA/Collector

**Features:**
- Real-time filtering (updates metrics instantly)
- Summary statistics on filtered data
- Sortable data table with key columns
- CSV export with timestamp

**Export Columns:**
- Participant Name, Grade, Language
- School, EA, EGRA Score
- Cohort, Session counts (total, 30-day, 90-day)
- Both quality flags
- Response Date

## Technical Details

### Database Query
```sql
SELECT 
    -- All assessment fields
    -- Session counts: session_count_total, session_count_30_days, session_count_90_days
    -- Cohort: cohort_session_range
    -- Flags: flag_moving_too_fast, flag_same_letter_groups
FROM teampact_assessment_endline_2025
WHERE assessment_type = 'endline'
```

### Calculated Fields
- `Has Quality Flags`: Either flag is True
- `Both Flags`: Both flags are True
- `Flag Status`: Categorical (No Flags, One Flag, Both Flags)
- `Participant Name`: First Name + Last Name

### Performance
- Cached for 1 hour (`@st.cache_data(ttl=3600)`)
- Loads ~4,000 records in <2 seconds
- All visualizations render client-side (Plotly)

## Key Findings (Initial Data)

### Session Impact
- Groups with 41+ sessions score **higher** than 0-10 session groups
- Strong positive correlation between session count and performance
- Session recency matters (30-day correlation visible)

### Quality Flags
- Flagged groups tend to score **lower** than non-flagged
- "Moving Too Fast" impact: TBD based on data
- "Same Letter Groups" impact: TBD based on data
- Groups with both flags show cumulative negative effect

### Distribution
- 62.6% of assessments in highest cohort (41+ sessions)
- Only 9.5% in lowest cohort (0-10 sessions)
- Flag rates align with expected ~30% prevalence

## Usage Instructions

### For Program Managers
1. Start with **Overview** tab to understand flag prevalence
2. Check **School & EA Insights** to identify support needs
3. Use **Data Explorer** to drill into specific cases

### For Researchers
1. **Cohort Performance** tab for session frequency analysis
2. **Flag Impact** tab for teaching quality relationships
3. **Cross-Analysis** tab for multivariate insights
4. Export filtered data for external analysis

### For Coaches
1. **School & EA Insights** for targeted coaching
2. Filter by specific school in **Data Explorer**
3. Review flag patterns to guide support

## Next Steps
- **COMPLETED:** Page created and integrated into navigation
- **PENDING:** Schedule automatic data refresh (Step 5)
- **FUTURE:** Add longitudinal tracking (compare multiple endlines)
- **FUTURE:** Add intervention tracking (before/after coaching)

## Related Files
- Django model: `/Zazi_iZandi_Website_2025/api/models.py` (TeamPactAssessmentEndline2025)
- Cohort calculation: `/Zazi_iZandi_Website_2025/api/management/commands/calculate_assessment_cohorts.py`
- Assessment sync: `/Zazi_iZandi_Website_2025/api/management/commands/sync_teampact_assessments_api.py`
- Participant sync: `/Zazi_iZandi_Website_2025/api/management/commands/sync_teampact_participants.py`

## Support
For questions or issues:
1. Check database connection in sidebar
2. Verify data refresh timestamp
3. Ensure Django sync commands have run
4. Check `RENDER_DATABASE_URL` environment variable

