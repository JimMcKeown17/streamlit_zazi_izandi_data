# Data Sources Documentation

**Last Updated:** March 3, 2026

This document provides a comprehensive overview of all data sources used in the Zazi iZandi Data Portal, organized by page and data loading method.

---

## Table of Contents
1. [Database Tables Summary](#database-tables-summary)
2. [Data Loading Functions by Source](#data-loading-functions-by-source)
3. [Page-by-Page Data Sources](#page-by-page-data-sources)
4. [Architecture Notes](#architecture-notes)

---

## Database Tables Summary

### Primary Application Tables

#### 1. **teampact_sessions_complete** ✅ (Current Production)
- **Purpose**: Main table for TeamPact education session data (auto-updated nightly via cron job)
- **Data Type**: Session attendance, participation, letters taught, EA performance
- **Update Frequency**: Nightly via Django management command
- **Used By Pages**:
  - 2025 Sessions NMB (Cohort 2)
  - 2025 Sessions BCM (Cohort 2)
  - Project Management: Letter Progress pages
  - Project Management: Quality check pages (Same Letter Groups, Moving Too Fast)
  - Literacy Coach Mentor Agent

#### 2. **teampact_nmb_sessions** ⚠️ (Legacy - Being Phased Out)
- **Purpose**: Original table for TeamPact session data
- **Status**: Being phased out; replaced by `teampact_sessions_complete`
- **Still Referenced By**:
  - `api/teampact_session_api.py` (API sync script - legacy)
  - Some test files

#### 3. **assessments_2026** ✅ (Current Production — 2026)
- **Purpose**: 2026 EGRA baseline assessment data synced from TeamPact API
- **Data Type**: Letter knowledge, nonword reading, word reading scores per learner
- **Survey IDs**: 815 (isiXhosa), 816 (Afrikaans), 817 (English), 805 (ECD)
- **Update Frequency**: Nightly via Django management command (`sync_assessments_2026`)
- **Key Mapping**: NMB surveys require a two-step API process — survey responses provide `group_id`, then `GET /groups/{id}` resolves `class_name` and `program_name`. Grade is derived from `class_name` via substring matching.
- **Used By Pages**:
  - 2026 Baseline Primary Schools
  - 2026 ECD Baseline
- **Detailed mapping docs**: [`docs/TEAMPACT_API_ASSESSMENT_MAPPING_2026.md`](docs/TEAMPACT_API_ASSESSMENT_MAPPING_2026.md)

#### 4. **assessment_cells_2026** ✅ (Current Production — 2026)
- **Purpose**: Individual cell-level EGRA results (one row per letter/word per assessment)
- **Data Type**: cell_id, cell_index, status (correct/incorrect/incomplete), time_taken
- **Update Frequency**: Synced alongside `assessments_2026`
- **Used By Pages**:
  - 2026 Baseline Primary Schools (letter-level analysis)

#### 5. **sessions_2026** ✅ (Current Production — 2026)
- **Purpose**: 2026 EA teaching session data
- **Data Type**: Session attendance, letters taught, participant counts
- **Update Frequency**: Nightly via `nightly_sync_2026`
- **Used By Pages**:
  - 2026 Sessions
  - 2026 Letter Progress

#### 6. **mentor_visits_2026** ✅ (Current Production — 2026)
- **Purpose**: 2026 mentor observation visit data
- **Survey ID**: 824
- **Update Frequency**: Nightly via `sync_mentor_visits_2026.py`
- **Used By Pages**:
  - 2026 Mentor Visits

#### 7. **teampact_assessment_endline_2025** (2025)
- **Purpose**: Endline assessment data for 2025 NMB Cohort 2
- **Data Type**: EGRA assessment results, cohort analysis data
- **Update Frequency**: Loaded from database (populated by Django)
- **Used By Pages**:
  - 2025 Endline NMB (Cohort 2)
  - 2025 Baseline NMB (Cohort 2) - for comparison

#### 8. **api_tasession**
- **Purpose**: Django app table for TA mentor visit sessions (separate from TeamPact education sessions)
- **Data Type**: TA mentor observation and visit data
- **Used By**: 
  - 2025 Sessions page (early implementation tracking)
  - `db_api_get_sessions.py`

#### 9. **api_teampactsession**
- **Purpose**: Django app table (appears to be another session-related table)
- **Used By**: Database inspection scripts only

### PostgreSQL System Tables (Metadata)
- **information_schema.tables** - For checking table existence
- **pg_stat_user_tables** - For database statistics and inspection

---

## Data Loading Functions by Source

### 📊 Database Sources

| Function | Table | Data Type | Update Method |
|----------|-------|-----------|---------------|
| `load_assessments_2026()` | assessments_2026 | 2026 baseline assessments | Nightly via `sync_assessments_2026` |
| `load_sessions_2026()` | sessions_2026 | 2026 session data | Nightly via `nightly_sync_2026` |
| `load_mentor_visits_2026()` | mentor_visits_2026 | 2026 mentor visits | Nightly via `sync_mentor_visits_2026` |
| `load_session_data_from_db()` | teampact_sessions_complete | Session data | Nightly cron job |
| `load_endline_from_db()` (nmb_assessments.py) | teampact_assessment_endline_2025 | Endline assessments | Django management |
| `load_endline_from_db()` (nmb_endline_cohort_analysis.py) | teampact_assessment_endline_2025 | Endline assessments | Django management |
| `get_ta_sessions()` | api_tasession | TA mentor visits | Django app |

### 🌐 API Sources (TeamPact)

| Function | Survey IDs | Languages | Purpose | Status |
|----------|-----------|-----------|---------|--------|
| `load_zazi_izandi_2025_tp_api()` | 575, 578, 576 | Xhosa, English, Afrikaans | NMB Baseline 2025 | Available but CSV preferred |
| `load_zazi_izandi_nmb_2025_endline_tp()` | 725, 726, 727 | Xhosa, English, Afrikaans | NMB Endline 2025 | Available but database preferred |
| `load_zazi_izandi_east_london_2025_tp_api()` | 644, 646, 647 | Xhosa, English, Afrikaans | BCM Baseline 2025 | Available but CSV preferred |

### 📁 CSV/Excel Sources

#### TeamPact CSV Exports
| Function | Files | Purpose |
|----------|-------|---------|
| `load_zazi_izandi_2025_tp()` | survey575/578/576 (3 CSV files) | NMB Baseline 2025 |
| `load_zazi_izandi_nmb_2025_endline_tp_csv()` | survey725/726/727 (3 CSV files) | NMB Endline 2025 |
| `load_zazi_izandi_east_london_2025_tp()` | survey644/646/647 (3 CSV files) | BCM Baseline 2025 |
| `load_zazi_izandi_ecd_endline()` | survey723 (1 CSV file) | ECD Endline 2025 |
| `load_mentor_visits_2025_tp()` | survey612 (1 CSV file) | Mentor Visit Tracker |

#### SurveyCTO CSV Exports
| Function | Files | Purpose |
|----------|-------|---------|
| `load_zazi_izandi_2025()` | 2 CSV files | 2025 Midline/Baseline (Cohort 1) |

#### Excel Files
| Function | Files | Purpose |
|----------|-------|---------|
| `load_zazi_izandi_new_schools_2024()` | 1 Excel file | 2024 New Schools Endline |
| `load_zazi_izandi_2024()` | 6 Excel files (or Parquet) | 2024 All assessments |
| `load_zazi_izandi_2023()` | 2 Excel files (or Parquet) | 2023 All assessments |

**Note**: 2024 and 2023 data prefer Parquet files (10-50x faster) but fall back to Excel if Parquet unavailable.

---

## Page-by-Page Data Sources

### 🏠 Home Pages
| Page | Data Source | Loading Function | Source Type |
|------|-------------|------------------|-------------|
| Home | 2024 data | `load_zazi_izandi_2024()` | Parquet/Excel |
| Table of Contents | None (navigation only) | N/A | N/A |

---

### 📅 2023 Results

| Page | Data Source | Loading Function | Source Type |
|------|-------------|------------------|-------------|
| 2023 Results | 2023 assessments & sessions | `load_zazi_izandi_2023()` | Parquet/Excel |

---

### 📅 2024 Results

| Page | Data Source | Loading Function | Source Type |
|------|-------------|------------------|-------------|
| 2024 Letter Knowledge | 2024 assessments | `load_zazi_izandi_2024()` | Parquet/Excel |
| 2024 Word Reading | 2024 assessments | `load_zazi_izandi_2024()` | Parquet/Excel |
| 2024 New Schools | New schools endline | `load_zazi_izandi_new_schools_2024()` | Excel |
| 2024 Session Analysis | 2024 sessions | `load_zazi_izandi_2024()` | Parquet/Excel |

---

### 📅 2026 Results

| Page | Data Source | Loading Function | Source Type | Notes |
|------|-------------|------------------|-------------|-------|
| 2026 Baseline Primary Schools | **Database** | `load_assessments_2026()` / direct SQL | PostgreSQL (`assessments_2026`) | Surveys 815/816/817; grade derived from class_name via group API; includes Grouping QA tab with 2026-specific grouping logic and CSV export including group assignments |
| 2026 ECD Baseline | **Database** | Direct SQL on `assessments_2026` | PostgreSQL | Survey 805; grade from free-text answer |
| 2026 Sessions | **Database** | `load_sessions_2026()` | PostgreSQL (`sessions_2026`) | Auto-updated nightly |
| 2026 Letter Progress | **Database** | Direct SQL on `sessions_2026` | PostgreSQL | Grade derived from class_name |
| 2026 Mentor Visits | **Database** | `load_mentor_visits_2026()` | PostgreSQL (`mentor_visits_2026`) | Survey 824 |

**Key 2026 mapping detail:** NMB assessment surveys (815/816/817) do NOT include class_name or program_name in the API response. These are resolved via a second API call (`GET /groups/{group_id}`). See [`docs/TEAMPACT_API_ASSESSMENT_MAPPING_2026.md`](docs/TEAMPACT_API_ASSESSMENT_MAPPING_2026.md) for full details.

---

### 📅 2025 Results (Public Access)

| Page | Data Source | Loading Function | Source Type | Notes |
|------|-------------|------------------|-------------|-------|
| 2025 Baseline NMB (Cohort 1) | SurveyCTO exports | `load_zazi_izandi_2025()` | CSV | Jan-Jun cohort |
| 2025 Midline NMB (Cohort 1) | SurveyCTO exports | `load_zazi_izandi_2025()` | CSV | Jan-Jun cohort |
| 2025 ECD NMB Results | ECD-specific + midline | `load_zazi_izandi_ecd_endline()` + `load_zazi_izandi_2025()` | CSV | Combined ECD data |

---

### 📅 2025 Results (Internal Access)

| Page | Data Source | Loading Function | Source Type | Notes |
|------|-------------|------------------|-------------|-------|
| 2025 Baseline NMB (Cohort 2) | **Database** | `load_endline_from_db()` | PostgreSQL | Actually shows endline data |
| 2025 Endline NMB (Cohort 2) | **Database** | `load_endline_from_db()` | PostgreSQL | Cohort analysis |
| 2025 Baseline BCM (Cohort 2) | TeamPact CSV exports | `load_zazi_izandi_east_london_2025_tp()` | CSV | East London data |
| 2025 Sessions NMB (Cohort 2) | **Database** | `load_session_data_from_db()` | PostgreSQL | Auto-updated nightly |
| 2025 Sessions BCM (Cohort 2) | **Database** | `load_session_data_from_db()` | PostgreSQL | Auto-updated nightly |
| 2025 Mentor Visits (Cohort 2) | Merged CSV | `load_mentor_visits_2025_tp()` + merge | CSV | Old + new surveys merged |

---

### 🔬 Research & Benchmarks (Public)

| Page | Data Source | Loading Function | Source Type |
|------|-------------|------------------|-------------|
| Research & Benchmarks | 2024 assessments | `load_zazi_izandi_2024()` | Parquet/Excel |

---

### 🔬 Research & Benchmarks (Internal)

| Page | Data Source | Loading Function | Source Type |
|------|-------------|------------------|-------------|
| Zazi Bot (AI Assistant) | Context-based | Various | Multiple sources |
| Year Comparisons | 2023, 2024, 2025 data | Multiple loaders | Parquet/Excel/CSV |

---

### 🎯 Project Management (Internal Only)

| Page | Data Source | Loading Function | Source Type | Notes |
|------|-------------|------------------|-------------|-------|
| Letter Progress (Cohort 2) | **Database** | Direct SQL query | PostgreSQL | `teampact_sessions_complete` |
| Letter Progress Detailed (Cohort 2) | **Database** | Direct SQL query | PostgreSQL | `teampact_sessions_complete` |
| Check: Same Letter Groups | **Database** | Direct SQL query | PostgreSQL | `teampact_sessions_complete` |
| Check: Moving Too Fast | **Database** | Direct SQL query | PostgreSQL | `teampact_sessions_complete` |
| 2025 Mentor Visits (Cohort 2) | Mentor visit CSV | `load_mentor_visits_2025_tp()` | CSV | Observation data |

---

## Architecture Notes

### Data Flow Evolution

#### Phase 1: Manual CSV/Excel (2023-2024)
- All data loaded from locally stored CSV/Excel files
- Manual exports from SurveyCTO and TeamPact
- Files committed to repository

#### Phase 2: API Integration (Mid-2025)
- API functions created for TeamPact data
- Optional API toggle in some pages
- Still defaults to CSV for stability

#### Phase 3: Database Integration (Oct 2025)
**Sessions Data:**
1. Django management command fetches from TeamPact API nightly
2. Stores in `teampact_sessions_complete` table
3. Render cron job runs command automatically
4. Streamlit pages read from database (no manual refresh needed)

**Assessment Data:**
1. Endline assessments loaded into `teampact_assessment_endline_2025`
2. Includes cohort analysis and quality flags
3. Pages read directly from database

#### Phase 4: Performance Optimization (Nov 2024)
- Converted 2023 & 2024 Excel files to Parquet format
- 10-50x faster loading times
- Automatic fallback to Excel if Parquet unavailable

---

### Current Best Practices

1. **Assessment Data (2026 Baseline)**
   - ✅ Use database (`assessments_2026` / `assessment_cells_2026`)
   - ✅ Auto-synced nightly via `sync_assessments_2026`
   - ✅ Grade, class_name, program_name resolved via group_id lookup at sync time
   - ❌ Don't call TeamPact API directly from Streamlit pages

2. **Sessions Data (2026)**
   - ✅ Use database (`sessions_2026`)
   - ✅ Auto-updates nightly via `nightly_sync_2026`
   - ❌ Don't use manual API calls

3. **Mentor Visits (2026)**
   - ✅ Use database (`mentor_visits_2026`)
   - ✅ Auto-synced nightly

4. **Sessions Data (2025 Cohort 2)**
   - ✅ Use database (`teampact_sessions_complete`)
   - ✅ Auto-updates nightly
   - ❌ Don't use manual API calls or CSV exports

5. **Assessment Data (2025 Cohort 2 Endline)**
   - ✅ Use database (`teampact_assessment_endline_2025`)
   - ❌ Don't use CSV exports (database is source of truth)

6. **Assessment Data (2025 Cohort 1 & Cohort 2 Baseline)**
   - ✅ Use CSV exports from TeamPact/SurveyCTO
   - ⚠️ API available but CSV preferred for stability

7. **Historical Data (2023-2024)**
   - ✅ Use Parquet files when available
   - ✅ Automatic fallback to Excel
   - ✅ Fast loading with caching

---

### Database Table Relationships

```
assessments_2026 (2026 Assessment Data)
├── Used by: 2026 Baseline Primary Schools page
├── Used by: 2026 ECD Baseline page
├── Mapping: group_id → GET /groups/{id} → class_name + program_name
├── Grade: Derived from class_name (NMB) or free-text answer (ECD)
└── Updated: Nightly via sync_assessments_2026

assessment_cells_2026 (2026 Cell-Level Results)
├── Used by: 2026 Baseline letter-level analysis
├── Linked to: assessments_2026 via response_id
└── Updated: Nightly via sync_assessments_2026

sessions_2026 (2026 Session Data)
├── Used by: 2026 Sessions page
├── Used by: 2026 Letter Progress pages
└── Updated: Nightly via nightly_sync_2026

mentor_visits_2026 (2026 Mentor Visit Data)
├── Used by: 2026 Mentor Visits page
└── Updated: Nightly via sync_mentor_visits_2026

teampact_sessions_complete (Session Data)
├── Used by: Session analysis pages
├── Used by: Letter progress tracking
├── Used by: Quality check tools
└── Updated: Nightly via cron job

teampact_assessment_endline_2025 (Assessment Data)
├── Used by: Endline analysis pages
├── Used by: Cohort analysis pages
└── Updated: Via Django management command

api_tasession (TA Visits - Separate System)
├── Used by: Early implementation tracking
└── Updated: Via Django app directly
```

---

### File Locations

#### CSV Files
- `data/` - SurveyCTO exports
- `data/Teampact/` - TeamPact survey exports
- `data/mentor_visit_tracker/` - Mentor observation data

#### Excel Files
- `data/*.xlsx` - Assessment databases (2023-2024)

#### Parquet Files (Optimized)
- `data/parquet/raw/` - Working files read by Streamlit pages (2023-2024 optimized copies)
- `data/parquet/2023/` - Well-named 2023 backups
- `data/parquet/2024/` - Well-named 2024 backups (ZZ 1.0 + ZZ 2.0)
- `data/parquet/2025/` - Well-named 2025 backups (Cohort 1, Cohort 2, ECD, East London)
- `data/parquet/backup/` - Raw DB table dumps from Feb 2025 audit

---

### Environment Variables Required

| Variable | Purpose | Required For |
|----------|---------|--------------|
| `TEAMPACT_API_TOKEN` | TeamPact API access | API functions (optional use) |
| `RENDER_DATABASE_URL` | PostgreSQL connection | All database access |
| `DATABASE_URL` | Django database | TA session tracking |

---

## Summary Statistics

**Total Database Tables Used:** 9
- assessments_2026 (2026 primary)
- assessment_cells_2026 (2026 cell-level)
- sessions_2026 (2026 primary)
- mentor_visits_2026 (2026 primary)
- teampact_sessions_complete (2025 primary)
- teampact_assessment_endline_2025 (2025 primary)
- teampact_nmb_sessions (legacy)
- api_tasession (separate system)
- api_teampactsession (inspection only)

**Total Data Loading Functions:** 15+
- Database: 7 functions (3 new for 2026)
- API: 3 functions (available but not primary use)
- CSV/Excel: 9 functions

**Pages Using Database:** 13+ pages (all 2026 + 2025 Cohort 2 + Project Management)

**Pages Using CSV/Excel:** 11 pages (2023, 2024, 2025 Cohort 1)

---

## Migration Status

### ✅ Completed Migrations
- [x] Sessions data moved from CSV to database (2025)
- [x] Nightly auto-update implemented (2025)
- [x] Endline assessment data moved to database (2025)
- [x] 2023/2024 data converted to Parquet format (10.7x faster loading)
- [x] 2026 assessment data synced via `sync_assessments_2026` with group_id resolution
- [x] 2026 session data synced via `nightly_sync_2026`
- [x] 2026 mentor visit data synced via `sync_mentor_visits_2026`

### ⚠️ Pending Updates
- [ ] Remove references to `teampact_nmb_sessions` (legacy table, superseded by `teampact_sessions_complete`)
- [ ] Drop legacy tables: `teampact_nmb_sessions` (76 MB), `api_teampactsession` (32 MB) — both stale since Oct 2025
- [ ] Consolidate API functions (currently optional, rarely used)

---

**Document Maintained By:** Data Team
**Review Frequency:** Quarterly or when major changes occur

**Related Documentation:**
- [`docs/TEAMPACT_API_ASSESSMENT_MAPPING_2026.md`](TEAMPACT_API_ASSESSMENT_MAPPING_2026.md) — Detailed 2026 API field mapping

