# Database Audit — Render PostgreSQL
**Date:** 2025-02-24
**Source:** Live query against production database via `db_audit.py`

## How This Was Collected

Connected directly to Render PostgreSQL using `RENDER_DATABASE_URL` from `.env`.
Queried `information_schema.tables` for all public tables, then ran `COUNT(*)`,
column counts, `pg_total_relation_size()`, and `MAX()` on timestamp columns
for each table individually.

This is **not** inferred from Django models — it's what actually exists in PostgreSQL.

## Full Table Inventory (34 tables)

### Your Data Tables (12 tables, ~225 MB)

```
Table                               Rows      Cols    Size    Latest Data          Status
─────────────────────────────────── ──────── ───── ─────── ──────────────────── ──────────
teampact_sessions_complete          110,255    60   90 MB   2026-02-24 02:02    ACTIVE (cron still running!)
teampact_nmb_sessions                94,026    58   76 MB   2025-10-27 09:14    STALE — last updated Oct 2025
api_teampactsession                  93,257    55   32 MB   2025-10-24 16:20    STALE — last updated Oct 2025
teampact_assessment_endline_2025      9,843    35   13 MB   2025-11-18 12:21    FROZEN — endline complete
teampact_participants                18,244    26    8 MB   2025-11-04 22:27    FROZEN — last synced Nov 2025
api_egralearnerscore                 10,513    68    5 MB   N/A                 HISTORICAL (SurveyCTO 2024)
api_tasession                         3,775    21    4 MB   N/A                 HISTORICAL (SurveyCTO 2024)
api_egraassessment                    1,777    33    3 MB   N/A                 HISTORICAL (SurveyCTO 2024)
api_mentorvisit                          99    31  168 KB   N/A                 HISTORICAL (SurveyCTO 2024)
api_taprofile                           166     5   96 KB   N/A                 LOOKUP TABLE
api_egraresponsedetail                    0     8   24 KB   N/A                 EMPTY (never populated)
whatsapp_messagelog                       1     3   56 KB   N/A                 NEARLY EMPTY
```

### Django Infrastructure Tables (10 tables)

```
Table                               Rows    Size
─────────────────────────────────── ───── ──────
auth_permission                      112   88 KB
django_admin_log                      52   64 KB
django_migrations                     66   32 KB
django_content_type                   28   40 KB
django_session                        11   64 KB
django_site                            2   56 KB
auth_group_permissions                 0   32 KB
auth_group                             0   24 KB
```

### Django Auth / Social / Accounts Tables (12 tables)

```
Table                               Rows    Size
─────────────────────────────────── ───── ──────
accounts_user                          5   64 KB
accounts_userprofile                   5   48 KB
accounts_user_groups                   0   32 KB
accounts_user_user_permissions         0   32 KB
account_emailaddress                   0   56 KB
account_emailconfirmation              0   32 KB
socialaccount_socialapp_sites          1   72 KB
socialaccount_socialapp                1   32 KB
socialaccount_socialtoken              0   40 KB
socialaccount_socialaccount            0   32 KB
assessments_learner                    0   40 KB
assessments_assessmentresult           0   40 KB
assessments_assessmenttype             0   24 KB
assessments_school                     0   24 KB
```

## Key Findings

### 1. Cron job is STILL running and pulling 2026 data into 2025 table
`teampact_sessions_complete` has data up to **2026-02-24**. The nightly sync
is still writing into this table with no year filter. Of the 110,255 rows:
- **109,265 rows** have `session_started_at < 2026-01-01` (2025 data)
- **~990 rows** have `session_started_at >= 2026-01-01` (2026 data mixed in)

### 2. Two legacy session tables can be dropped
- `teampact_nmb_sessions` (94K rows, 76 MB) — superseded by `teampact_sessions_complete`
- `api_teampactsession` (93K rows, 32 MB) — superseded by `teampact_sessions_complete`

Both were last updated Oct 2025. Combined they waste ~108 MB.

### 3. `teampact_assessment_baseline_2025` does NOT exist
The Django models define this table (migration 0025), but it was **never created**
in the production database. The migration may not have been run on Render.

### 4. Several tables are completely empty (0 rows)
- `api_egraresponsedetail` — item-level EGRA details, never populated
- `assessments_learner` — Django assessment app, never used
- `assessments_assessmentresult` — Django assessment app, never used
- `assessments_assessmenttype` — Django assessment app, never used
- `assessments_school` — Django assessment app, never used

### 5. SurveyCTO tables are historical and frozen
These tables have data from 2024 and are no longer being updated:
- `api_tasession` (3,775 rows) — TA teaching sessions
- `api_egraassessment` (1,777 rows) — EGRA assessment headers
- `api_egralearnerscore` (10,513 rows) — individual EGRA scores
- `api_mentorvisit` (99 rows) — mentor visit observations
- `api_taprofile` (166 rows) — TA profile lookup table

## Backups

### Raw DB Table Dumps (`data/parquet/backup/`)

One-to-one exports of every DB table, pre-cleanup. These preserve
the exact data that was in PostgreSQL on 2025-02-24.

```
data/parquet/backup/
├── teampact_sessions_complete_backup.parquet    (110,255 rows — includes 2026 data)
├── teampact_nmb_sessions_backup.parquet         (94,026 rows)
├── api_teampactsession_backup.parquet           (93,257 rows)
├── teampact_assessment_endline_2025_backup.parquet (9,843 rows)
├── teampact_participants_backup.parquet          (18,244 rows)
├── api_tasession_backup.parquet                  (3,775 rows)
├── api_egraassessment_backup.parquet             (1,777 rows)
├── api_egralearnerscore_backup.parquet           (10,513 rows)
├── api_egraresponsedetail_backup.parquet         (0 rows)
├── api_mentorvisit_backup.parquet                (99 rows)
└── api_taprofile_backup.parquet                  (166 rows)
```

### Well-Named 2025 Backups (`data/parquet/2025/`)

Human-readable backups organized by cohort and data type.
This is the canonical backup location for all 2025 data.

```
data/parquet/2025/
│
│  COHORT 1 — NMB Schools (Jan–Jun 2025, SurveyCTO EGRA form)
│  Source: load_zazi_izandi_2025() → df_full, split by date cutoff 2025-04-15
│  ──────────────────────────────────────────────────────────────────────────
├── 2025_baseline_nmb_cohort1.parquet                  4,417 rows   Initial assessments (before Apr 15)
├── 2025_midline_nmb_cohort1.parquet                   2,296 rows   Midline assessments (Apr 15+)
│
│  COHORT 1 — ECD Centers (Jan–Jun 2025, SurveyCTO EGRA form)
│  Source: load_zazi_izandi_2025() → df_ecd, split by date cutoff 2025-04-15
│  ──────────────────────────────────────────────────────────────────────────
├── 2025_baseline_ecd.parquet                            442 rows   ECD initial assessments (before Apr 15)
├── 2025_midline_ecd.parquet                             359 rows   ECD midline assessments (Apr 15+)
├── 2025_endline_ecd.parquet                             309 rows   ECD endline (TeamPact survey 723)
│
│  COHORT 2 — NMB Schools (Jul–Nov 2025, TeamPact API)
│  ──────────────────────────────────────────────────────────────────────────
├── 2025_sessions_cohort2.parquet                    109,265 rows   Session attendance (2025 only, no 2026 leak)
├── 2025_baseline_assessments_cohort2_nmb.parquet     13,196 rows   NMB baseline (surveys 575/576/578)
├── 2025_endline_assessments_cohort2.parquet           9,843 rows   NMB endline from DB (with cohort flags)
├── 2025_endline_assessments_cohort2_nmb_csv.parquet   3,677 rows   NMB endline from CSV (surveys 725/726/727)
│
│  EAST LONDON (2025, TeamPact API)
│  ──────────────────────────────────────────────────────────────────────────
├── 2025_assessments_east_london.parquet               3,736 rows   EL assessments (surveys 644/646/647)
│
│  SHARED
│  ──────────────────────────────────────────────────────────────────────────
└── 2025_participants.parquet                         18,244 rows   All TeamPact participants
```

**Notes:**
- Cohort 1 NMB + ECD data all comes from the same SurveyCTO EGRA form export.
  The pages use `load_zazi_izandi_2025()` which returns `(df_full, df_ecd)`.
  Baseline vs midline is split by a `2025-04-15` date cutoff within the pages.
- `2025_endline_assessments_cohort2.parquet` is from the DB table
  `teampact_assessment_endline_2025` which includes calculated cohort fields
  (`cohort_session_range`, `flag_moving_too_fast`, `flag_same_letter_groups`).
- `2025_endline_assessments_cohort2_nmb_csv.parquet` is the raw CSV survey
  export without those calculated fields.

### Well-Named 2024 Backups (`data/parquet/2024/`)

```
data/parquet/2024/
│
│  ZZ 1.0 — Main Cohort (16 schools, ~1,899 children)
│  Source: SurveyCTO EGRA assessments + session tracking
│  ──────────────────────────────────────────────────────────────────────────
├── 2024_baseline_zz1.parquet                 1,899 rows   ZZ 1.0 baseline assessments
├── 2024_midline_zz1.parquet                  1,899 rows   ZZ 1.0 midline assessments
├── 2024_endline_zz1.parquet                  1,887 rows   ZZ 1.0 endline assessments
├── 2024_sessions_zz1.parquet                 1,899 rows   ZZ 1.0 session tracking
│
│  ZZ 2.0 — Word Reading Cohort (522 children)
│  Source: SurveyCTO EGRA assessments
│  ──────────────────────────────────────────────────────────────────────────
├── 2024_baseline_zz2.parquet                   522 rows   ZZ 2.0 baseline assessments
└── 2024_endline_zz2.parquet                    502 rows   ZZ 2.0 endline assessments
```

### Well-Named 2023 Backups (`data/parquet/2023/`)

```
data/parquet/2023/
├── 2023_endline_assessments.parquet          1,897 rows   Endline assessments
└── 2023_sessions.parquet                     1,899 rows   Session tracking
```

### Working Files (`data/parquet/raw/`)

These are what the Streamlit pages actually read from:

```
data/parquet/raw/
├── 2025_sessions.parquet              (109,265 rows — same as 2025_sessions_cohort2)
├── 2025_assessment_endline.parquet    (9,843 rows — same as 2025_endline_assessments_cohort2)
├── 2023_endline.parquet               (historical — also in 2023/)
├── 2023_sessions.parquet              (historical — also in 2023/)
├── 2024_baseline.parquet              (historical — also in 2024/ as zz1)
├── 2024_baseline2.parquet             (historical — also in 2024/ as zz2)
├── 2024_endline.parquet               (historical — also in 2024/ as zz1)
├── 2024_endline2.parquet              (historical — also in 2024/ as zz2)
├── 2024_midline.parquet               (historical — also in 2024/ as zz1)
└── 2024_sessions.parquet              (historical — also in 2024/ as zz1)
```
