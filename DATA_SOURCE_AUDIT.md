# Data Source Audit - October 28, 2025

## Summary
Audit of all files to ensure they're using the correct database table (`teampact_sessions_complete`) and not calling TeamPact APIs directly.

## ✅ CORRECT - Using Database Utils (teampact_sessions_complete)

### Pages using `load_session_data_from_db()` from database_utils:
1. **new_pages/2025/teampact_sessions_2025.py** - ✅ Correct
2. **new_pages/project_management/session_quality_review.py** - ✅ Correct

### Pages using database_utils functions directly:
3. **new_pages/ea_sessions_test.py** - ✅ Uses `get_database_engine()` and `check_table_exists()`

## ⚠️ NEEDS FIXING - Using Old Table (teampact_nmb_sessions)

### Files querying old table directly:
1. **new_pages/project_management/letter_progress_july_cohort.py** - Line 83 ❌
2. **new_pages/project_management/letter_progress_detailed_july_cohort.py** - Line 128 ❌

**Action Required**: Update SQL queries from `teampact_nmb_sessions` to `teampact_sessions_complete`

## ✅ SEPARATE DATA SOURCES (Not TeamPact Sessions)

### Files using Django TA Session API (different data):
1. **new_pages/2025/sessions_2025.py** - Uses `db_api_get_sessions.py`
2. **db_api_get_sessions.py** - Queries `api_tasession` table (Django app)

**Note**: This is a separate system for tracking TA mentor visit sessions, not TeamPact education sessions.

### Files using Django Letter Progress API:
1. **new_pages/project_management/session_quality_review.py** - Calls `http://zazi-izandi.co.za/api/letter-progress/`
2. **new_pages/project_management/letter_progress.py** - Calls `http://zazi-izandi.co.za/api/letter-progress/`
3. **new_pages/project_management/letter_progress_detailed.py** - Calls `http://zazi-izandi.co.za/api/letter-progress/`

**Note**: These call your own Django backend API, not TeamPact API. This is fine.

## ✅ CSV-BASED DATA LOADING (Assessment Data)

### Files using CSV data loaders (not TeamPact sessions):
1. **new_pages/2025/el_assessments.py** - Uses `load_zazi_izandi_east_london_2025_tp()` (CSV)
2. **new_pages/2025/nmb_assessments.py** - Uses `load_zazi_izandi_2025_tp()` (CSV)
3. **new_pages/2025/midline_2025.py** - Uses `load_zazi_izandi_2025()` (CSV)
4. **new_pages/2025/midline_2025_ecd.py** - Uses `load_zazi_izandi_2025()` (CSV)
5. **new_pages/2025/baseline_2025.py** - Uses `load_zazi_izandi_2025()` (CSV)
6. **new_pages/project_management/school_reports.py** - Uses `load_zazi_izandi_2025()` (CSV)
7. **new_pages/home_page.py** - Uses `load_zazi_izandi_2024()` (CSV)
8. **new_pages/Year_Comparisons.py** - Uses multiple CSV loaders (2023, 2024, 2025)
9. **new_pages/Research & Benchmarks.py** - Uses `load_zazi_izandi_2024()` (CSV)
10. **new_pages/2024/** - All use CSV loaders for 2024 data
11. **new_pages/2023/** - All use CSV loaders for 2023 data

**Note**: These are assessment data files (EGRA, baseline, midline, endline), not session tracking data.

## 🔍 API TOKEN CHECKS (Not Actually Calling APIs)

### Files that check for TEAMPACT_API_TOKEN but use CSV data:
1. **new_pages/2025/el_assessments.py** - Has optional API toggle but defaults to CSV
2. **new_pages/2025/nmb_assessments.py** - Has optional API toggle but defaults to CSV
3. **new_pages/2025/east_london_egra.py** - Checks token but appears to use CSV

**Note**: These have API capability built in but default to CSV. No direct API calls in production use.

## ✅ NO DIRECT TEAMPACT API CALLS

### Only authorized API caller:
- **api/teampact_session_api.py** - Contains `fetch_and_save_data()` function
  - Called ONLY by teampact_sessions_2025.py refresh button
  - Data goes to database, not used directly
  - This is the correct pattern ✅

## Action Items

### PRIORITY 1: Update Old Table References
- [ ] Fix `new_pages/project_management/letter_progress_july_cohort.py`
- [ ] Fix `new_pages/project_management/letter_progress_detailed_july_cohort.py`

### Column Name Changes
Both files need to account for:
- Old table: `teampact_nmb_sessions` → New table: `teampact_sessions_complete`
- Column differences already handled by database_utils.py for other fields
- Query structure should remain the same

### Verification
- [ ] Test letter progress pages after updates
- [ ] Verify data loads correctly
- [ ] Check for any missing columns in queries

