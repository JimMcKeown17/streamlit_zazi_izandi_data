# Mentor Visit Tracker - Data Merge Scripts

This package contains scripts to fetch and merge data from two versions of the Mentor Visit Tracker survey.

## Overview

- **Old Survey (ID: 612)**: "Mentor Visit Tracker (Copy)" - 17 questions, 209 responses
- **New Survey (ID: 677)**: "New Mentor Visit Tracker." - 20 questions, 183 responses

## Files

1. **fetch_mentor_visit_data.py** - Fetches data from both surveys via API
2. **merge_mentor_visit_data.py** - Merges old and new survey data into unified dataset
3. **README.md** - This file

## Setup

### 1. Install Required Packages

```bash
pip install requests pandas --break-system-packages
```

### 2. Set API Token

Set your Teampact API token as an environment variable:

```bash
export TEAMPACT_API_TOKEN='your_token_here'
```

## Usage

### Step 1: Fetch Survey Data

Run the fetch script to download both surveys:

```bash
python fetch_mentor_visit_data.py
```

This will:
- Fetch all responses from Survey 612 (old)
- Fetch all responses from Survey 677 (new)
- Save data to `data/mentor_visit_tracker/` directory
- Create both timestamped and "latest" CSV files

**Output Files:**
- `data/mentor_visit_tracker/survey612_old_YYYYMMDD_HHMMSS.csv`
- `data/mentor_visit_tracker/survey677_new_YYYYMMDD_HHMMSS.csv`
- `data/mentor_visit_tracker/latest_old.csv`
- `data/mentor_visit_tracker/latest_new.csv`

### Step 2: Merge Data

Run the merge script to combine both surveys:

```bash
python merge_mentor_visit_data.py
```

This will:
- Load both old and new survey data
- Create unified schema with all columns
- Handle missing columns gracefully (fills with NaN)
- Add `survey_source` column to identify origin
- Sort by response date (most recent first)
- Generate data quality report
- Save merged dataset

**Output Files:**
- `data/mentor_visit_tracker/merged_data_YYYYMMDD_HHMMSS.csv`
- `data/mentor_visit_tracker/merged_data_latest.csv`

## Survey Differences

### Common Questions (14)
Both surveys share these questions:
- Mentor Name
- School Name
- EA Name
- Grade
- Class
- Are the EA's children grouped correctly?
- If EA grouping are incorrect, please explain why?
- Are the EA using their letter tracker correctly?
- How engaged did you feel the learners are?
- How energertic & prepared was the EA?
- Please rate the overall quality of the sessions you observe
- How many sessions does the EA say they can do per day?
- How is the EA's relationship with their teacher?
- Any additional commentary?

### Removed in New Survey (3)
These questions only exist in old survey (will be NaN for new survey responses):
- Is the EA using the comment section and session tags on Teampact accordingly?
- The EA is teaching the correct letters per the group's letter knowledge (and letter trackers)
- Does the EA say that they often have trouble getting children for sessions (please ask them)?

### Added in New Survey (6)
These questions only exist in new survey (will be NaN for old survey responses):
- If No, have you corrected it?
- Session Tag (multiple-select)
- Is the EA using the comment section accordingly?
- Teaching at the right level (multiple-select)
- Does the EA experience challenges accessing the learners
- Reason for having 1 session or none (multiple-select)

## Data Quality Report

The merge script generates a comprehensive report including:

- **Survey Distribution**: Count and percentage from each survey
- **Date Range**: Earliest and latest responses
- **Completion Rate**: Percentage of completed responses
- **Top Respondents**: Most active mentors
- **Response Duration**: Statistics on completion time
- **Missing Data**: Columns with null values and percentages

## Merged Dataset Structure

The merged CSV contains:

### Metadata Columns (11)
- response_id
- response_uuid
- survey_id
- user_id
- user_name
- response_start_at
- response_end_at
- duration_minutes
- is_completed
- created_at
- updated_at

### Identifier Column (1)
- survey_source: Either "Old Survey (612)" or "New Survey (677)"

### Question Columns (20)
- 14 common questions
- 3 old-only questions (NaN for new survey)
- 3 new-only questions (NaN for old survey)

**Total Columns: 32**

## Usage in Python

```python
import pandas as pd

# Load merged data
df = pd.read_csv('data/mentor_visit_tracker/merged_data_latest.csv')

# Filter by survey source
old_only = df[df['survey_source'] == 'Old Survey (612)']
new_only = df[df['survey_source'] == 'New Survey (677)']

# Analyze common questions (no NaN issues)
common_questions = [
    'Mentor Name',
    'School Name',
    'EA Name',
    # ... etc
]

# Work with data
mentors = df['Mentor Name'].value_counts()
avg_duration = df['duration_minutes'].mean()
```

## Notes

- All question columns use the `column_name` from the API (not question_id)
- Response dates are parsed as datetime objects
- Data is sorted by response date (newest first)
- Missing data is expected for questions that don't exist in one survey
- The merge preserves all responses from both surveys (no data loss)

## Troubleshooting

**"TEAMPACT_API_TOKEN not found"**
- Make sure you've exported the environment variable
- Check: `echo $TEAMPACT_API_TOKEN`

**"Error loading data files"**
- Run `fetch_mentor_visit_data.py` first
- Check that `data/mentor_visit_tracker/` directory exists

**"Failed to fetch data"**
- Check your API token is valid
- Verify network connectivity
- Check survey IDs are correct (612 and 677)

## Contact

For issues with the Teampact API or survey structure changes, contact your Teampact administrator.
