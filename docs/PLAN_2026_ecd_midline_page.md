# Plan: 2026 ECD Midline Results Page

**Status:** Implemented 2026-06-09 (reviewed by Codex + independent agent; findings folded in below).
Outstanding: production backfill must be run manually —
`DJANGO_ENV=production python manage.py sync_assessments_2026 --survey-ids 891`
(local dev-DB run verified: 425 rows, zero errors, all grades 'PreR').
**Date:** 2026-06-09

## Goal

A new public Streamlit page "2026 Midline — ECD" comparing ECD baseline (survey 805) against
ECD midline (survey 891), modeled on the primary midline page but much simpler: no cohorts,
no tabs, and **no participant matching** (the baseline survey has no participant IDs).
All comparisons are cross-sectional: baseline distribution vs midline distribution.

## Investigation findings (verified against live API + DB)

1. **Survey 891 is not yet in `assessments_2026`.** The DB has 805 / 815-817 / 880-882 only.
   The Django sync must be extended and run before the page has data.
2. **Survey 891 uses the NEW primary-style API structure**, not the old ECD one:
   - Has `participant_id` + `participant_name` (e.g. 431786) — unlike baseline 805 where
     `participant_id` is empty for all 828 rows.
   - Has `group_id` as a JSON string (e.g. `'[64797]'`) requiring the `GET /groups/{id}`
     lookup; `program_name`/`class_name` are NOT inline (they are inline for 805).
   - Exactly one EGRA grid per response: letters, 60 cells. No nonwords/words sub-tests.
   - 425 responses as of 2026-06-09 (matches TeamPact UI).
3. **Group names follow `"{Center}-PreR-Group {N}"`** (e.g. `"Green Apple ECD-PreR-Group 1"`,
   program `"Green Apple ECD"`). `extract_grade_from_class_name` does not recognize these →
   grade would land `''`. Baseline 805 rows use grade `'PreR'` (824 rows) + 4 literal-string
   `'null'` rows (the ECD baseline page filters those out in SQL).
4. **ECD baseline rows have EMPTY `program_name`/`class_name` in the DB** (all 828 rows).
   So per-center baseline-vs-midline comparison is IMPOSSIBLE; center-level views must be
   midline-only.
5. **Masking** (`data_privacy.mask_dataframe`) is column-name driven (program_name,
   class_name, collected_by, participant_*, first/last name all aliased for unauthenticated
   users). No cohort-style pre-masking derivation needed. Use
   `dataset_key="assessments_2026_ecd"` like the ECD baseline page.
6. **No downstream collisions**: the primary midline page filters
   `language IN ('isiXhosa','English','Afrikaans')`; the ECD baseline page filters
   `assessment_type = 'baseline'`; `compute_school_summaries_2026` reads sessions, not
   assessments; parquet backup is a full-table dump. Adding `language='ECD',
   assessment_type='midline'` rows is isolated.
7. **Midline-side dedup is possible** (891 has participant IDs) even though
   baseline↔midline matching is not.

## Part A — Django sync changes (`Zazi_iZandi_Website_2025`)

File: `api/management/commands/sync_assessments_2026.py`

1. Add to `SURVEY_CONFIG`:
   ```python
   891: {
       'language': 'ECD',
       'assessment_type': 'midline',
       'survey_name': 'ZZ ECD Midline 2026',
       'is_ecd': False,  # NEW structure: participant + group lookup (flatten_nmb_response)
   }
   ```
   `is_ecd: False` is deliberate and the crux of the change: 891 must go down the
   primary-survey path (group lookup), not `flatten_ecd_response`. The 60-cell grid with
   index 0 classifies as `letters` via the existing fallback in `classify_subtest`.
   `DEFAULT_SURVEY_IDS` is computed as "midline and not is_ecd" → becomes
   `[880, 881, 882, 891]`, so the nightly sync picks 891 up automatically (desired — the
   survey is actively collecting).
2. Teach `extract_grade_from_class_name` to recognize PreR groups: hyphen-segment check for
   `prer` (mirroring how `"{EA}-{Letters|Blending}-Group {N}"` is handled in the data site),
   returning `'PreR'` — consistent with baseline 805's grade value. Plain substring
   `'pre-r' in name` is rejected because it would also match e.g. "Pre-Reading".
3. Update the module docstring survey table.
4. Update `api/tests_midline_sync_2026.py`: `DEFAULT_SURVEY_IDS` assertion becomes
   `[880, 881, 882, 891]`; add assertions for 891's config; add a PreR grade-extraction
   test. Run the Django test suite for that module.
5. Run the backfill: `python manage.py sync_assessments_2026 --survey-ids 891`
   (additive insert keyed on response_id; NO --full-refresh). ~5 response pages +
   ~107 group lookups ≈ 1 min. Verify row count / grade / program_name in DB afterwards.

## Part B — Data site page (`ZZ Data Site`)

### New file: `new_pages/2026/ecd_midline_helpers_2026.py`
Pure-pandas, streamlit-free, empty-safe helpers (testable like the primary ones):

- `normalize_ecd_assessments(df)` — parse dates, numeric letters columns, lowercase
  assessment_type, drop literal `'null'` grades (keeps headline counts consistent with the
  ECD baseline page).
- `dedupe_midline_per_learner(df)` — keep all baseline rows (no IDs to dedupe on) but only
  each learner's latest midline row (participant_id exists at midline). Used for analytic
  metrics; completion counts stay raw.
- `build_phase_letter_summary(df)` — per phase: n, mean, median letters (cross-sectional).
- `zero_letter_summary(df)` — % scoring 0 letters per phase.
- `benchmark_summary(df, threshold)` — % at/above threshold per phase.
- `benchmark_by_center_summary(df, threshold)` — midline-only, by program_name
  (baseline has no center info — finding #4).
- `build_center_midline_summary(df)` — midline assessments, unique learners, mean letters
  by center.
- `build_ea_midline_summary(df, min_assessments)` — midline assessments + mean letters by
  collector (outlier-flagging view, like the ECD baseline page's collector section).
- `build_daily_assessment_counts(df)` — same shape as the primary helper (which can't be
  reused: it filters to the three primary languages).

### New file: `new_pages/2026/ecd_midline_2026.py`
Single-column page (no tabs), sections:

1. Title + caption: surveys 805 vs 891; explicit note that baseline had no participant IDs
   so results are cross-sectional group-level comparisons, and that midline is in progress
   (n caveat). Data-freshness caption.
2. **Summary metrics**: baseline n, midline n (deduped learners + raw), centers at midline,
   mean letters baseline vs midline, letters improvement (cross-sectional delta).
3. **Letters: Baseline vs Midline** — grouped bar (Mean/Median toggle) + overlaid
   distribution histogram (the main "improvement" visual without matching).
4. **Benchmark movement** — threshold slider (default 20, step 5; flagged as an open
   question), % at/above per phase.
5. **Zero-letter learners** — % with 0 letters, baseline vs midline.
6. **Centers (midline)** — per-center mean letters + benchmark % (h-bar, RdYlGn) + table.
7. **EA snapshot (midline)** — assessments + mean letters per collector, min-n slider.
8. **Midline completion** — counts + unique learners by center and by EA (mirrors the
   primary completion section, midline side only).
9. **Assessments captured per day** — baseline grey / midline blue, same as the chart just
   added to the primary page.
10. **Export** — raw data expander + CSV download.

Styling/conventions: `@st.cache_data(ttl=3600)` raw loader + `mask_dataframe` wrapper,
`fmt_int`/`fmt_float`, phase colors Baseline `#9aa4b2` / Midline `#1f5cc4`, ECD accent
`#9467bd`, unique `key=` per element.

SQL: `WHERE language = 'ECD' AND assessment_type IN ('baseline', 'midline')`
(picks up 805 + 891 once synced; letters columns only).

### Registration: `main.py`
`st.Page("new_pages/2026/ecd_midline_2026.py", icon="🏫", title="2026 Midline — ECD",
url_path="ecd_midline_26")`, appended to `pages_2026_public` (the ECD baseline page is
public).

### Tests: `tests_and_utils/test_ecd_midline_2026.py`
unittest, mirroring `test_midline_primary_2026.py`: normalization (null-grade drop, date
coercion), midline dedup (latest per participant, baseline untouched), phase summary,
zero-letter %, benchmark %, center/EA summaries, daily counts, empty-safety for all.

## Part C — Documentation

- `docs/TEAMPACT_API_ASSESSMENT_MAPPING_2026.md`: add survey 891 to the table; note that it
  follows **Path A** (group lookup) despite being ECD, and the PreR grade rule.
- `docs/DATA_SOURCES_DOCUMENTATION.md`: add the new page + its query to the page mappings.

## Review outcomes (Codex + independent agent, 2026-06-09)

Both reviewers verified the load-bearing claims (sync routing, grade-rule necessity,
classify_subtest fallback, masking model, isolation analysis) against code and DB.
Verdict: implement with changes. Decisions taken:

1. **No dedup anywhere in analytics** (Codex, high): deduping midline but not baseline
   (which has no IDs) mixes units in every cross-sectional comparison. All analytic metrics
   use RAW response rows for BOTH phases. Unique-learner counts appear only in the
   operational completion section, and that logic gates strictly on
   `assessment_type == 'midline'` — never on "has a participant_id", because for public
   users `mask_dataframe` back-fills baseline participant_id from learner names
   (`data_privacy.py` `_build_identifier_series`). Test locks this with baseline rows
   carrying fake IDs. (`dedupe_midline_per_learner` is dropped from the helper list.)
2. **Headline delta demoted** (agent, high): midline is ~52% collected, fieldwork moves
   center by center, and baseline rows carry no center identifiers, so the cross-sectional
   delta is composition-biased and uncorrectable until collection completes. The summary
   row shows baseline mean and midline mean; the "improvement" delta lives in the letters
   section with a caption explaining the bias and why it cannot be re-weighted. The
   distribution overlay is the lead visual.
3. **`sync_assessment_cells_2026` side effect accepted** (both reviewers): it imports
   `DEFAULT_SURVEY_IDS`, so 891 joins the nightly cell sync. Verified benign-to-useful:
   891 takes the letters/60-cell path and current cell consumers filter to primary
   languages. Documented in both commands' docstrings.
4. **Benchmark default = 10** (not 20): Django's `GRADE_BENCHMARKS` uses 10 for Grade R,
   and with a 2.8-letter baseline mean a 20-default renders the section degenerate.
   Slider stays for exploration.
5. **PreR segment check placed FIRST** in `extract_grade_from_class_name` (before the
   `'grade r'` substring check) so a center name containing "Grade R" can't shadow it.
   Negative tests for "Pre-Reading"-style names.
6. **Django test renamed** (no longer "primary midline only") and 891 appended after 882 in
   `SURVEY_CONFIG` so the insertion-order-sensitive `DEFAULT_SURVEY_IDS` assertion stays
   deterministic.
7. **SQL pinned to `survey_id IN (805, 891)`** so future ECD surveys can't silently leak in.
8. **`table_of_contents.py`**: add the ECD midline entry AND the missing primary midline
   entry to the 2026 section.
9. **Scope trim**: standalone EA-outlier section dropped; mean letters folds into the
   completion-by-EA table. Final sections: summary metrics, letters baseline-vs-midline
   (bars + distribution overlay), benchmark movement, zero-letter, centers (midline-only),
   completion (by center / by EA), daily capture, export.
10. **Known limitations documented on-page/docs**: 891 rows have blank gender (the
    primary-style flatten path doesn't extract it; baseline ECD had it from free text);
    nightly pickup of 891 assumes the scheduler invokes `sync_assessments_2026` without
    `--survey-ids` (host cron not verifiable from these repos — confirm with Jim).
