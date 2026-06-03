# Plan: Cohort tabs + comparisons + outstanding-assessment tracker for 2026 Midline Primary

## Context

`new_pages/2026/midline_primary_2026.py` currently loads **all** primary baseline/midline rows and renders one long sequence of sections, mixing treatment, control, and SEF schools together. Program staff need to (a) analyze each cohort separately, (b) see the headline research result — did treatment schools improve more than control — and (c) know which treatment schools/grades still have outstanding midline assessments so they can dispatch assessors. This change restructures the page into three cohort tabs, adds a treatment-vs-control comparison and an outstanding-assessment tracker to the treatment tab, and ports four proven visualizations from the 2024/2025 pages.

**Cohort source of truth:** `data/2026_cohorts.py`. Its `treatment_schools` (51) and `sef_schools` (10) are byte-identical to the `/pm` dashboard's `lib/pm/cohorts.ts`; it also adds an explicit `control_schools` list. **Required fix:** remove `SAPPHIRE ROAD PRIMARY SCHOOL` from `control_schools` (the only sef∩control overlap) so SEF = 10 (matches the requested "10 SEF schools") and control = 53. This also makes the existing `baseline_2026.py` consistent: its `SCHOOL_COHORT_MAP` merges control **last** (`baseline_2026.py:27-31`), so today it classifies SAPPHIRE ROAD as *Control*; after the removal both pages classify it as SEF. (Side-effect to accept: that one school moves Control→SEF on the baseline page too — correct, since it is SEF-funded.)

**This page is PUBLIC** (`main.py:124`, `pages_2026_public`). Unauthenticated users get `program_name` (and `participant_id`, `collected_by`, `class_name`) replaced by **deterministic** aliases via `mask_dataframe` (`data_privacy.py:105-163`, `program_name` ∈ `SCHOOL_COLUMNS`). Because aliases are stable per entity, matching and per-school grouping survive masking, but **cohort classification must be derived from the raw, unmasked `program_name` before masking** (see Data loading).

**Stack (verified):** Streamlit 1.51.0, Plotly 6.3.1, pandas 2.3.3 (`key=` supported on plotly_chart/dataframe/download_button).

**Verified against the DB (read-only aggregate counts):** unique learners by cohort×phase — Treatment baseline 3789 / midline 2792 / matched 2596; Control 2914 / 567 / 462; SEF 1658 / 1320 / 1279. Comparison **will populate** (control midline early: 8 of 42 control schools). Outstanding treatment ≈ 1193. Zero blank `participant_id`s. Unmapped (→ "other", surfaced for triage): `Isaac Booi Senior Primary School`, `Molefe Senior Primary School`, a blank `program_name`, `Masinyusane` (test).

## Design decisions (confirmed with user)

- **Tabs:** Treatment / Control / SEF — each renders the same full analysis suite filtered to its cohort. Treatment additionally gets the comparison (top) and outstanding tracker (bottom).
- **New charts to port (into the shared suite → all three tabs):** zero-letter learners, benchmark % by school, EA performance (avg gain per EA), gender breakdown of gains.
- **Treatment-vs-control comparison (treatment tab):** avg letter gain by grade, % at benchmark baseline→midline, summary table, gain-distribution overlay.
- **Outstanding tracker (treatment tab):** school×grade counts table + bar chart + downloadable learner list.

## Data loading & masking (CRITICAL — addresses 2nd-review Critical)

Mirror the established `baseline_2026.py:70` pattern: compute the cohort column **inside the cached raw loader, before masking**.
- `_load_primary_midline_raw()` (cached) → `normalize_primary_assessments(df)` → `helpers.add_cohort_column(df)` (classifies on raw `program_name`; adds non-sensitive `cohort ∈ {treatment,sef,control,other}`). `mask_dataframe` does not touch a `cohort` column, so it survives.
- `load_primary_midline_data()` stays `mask_dataframe(_load_primary_midline_raw(), dataset_key="assessments_2026")`.
- `participant_id` is masked but **deterministic**, so baseline↔midline matching still works for public users (aliases replace display labels only). `grade`/`gender`/`cohort` are not masked.
- **Carry `cohort` through matched pairs** (add to metadata) so `baseline_cohort`/`midline_cohort` come from the carried column — never re-derived from a (possibly masked) `program_name`.

## Matching & cohort anchoring (addresses Codex #1/#2/#5)

- **Row-level `cohort`** drives descriptive single-phase sections (phase scores, cross-sectional benchmark, completion). Counts activity at the assessing school.
- **Baseline-anchored matched pairs** drive all matched sections (gains, school change, EA, gender, comparison, outstanding). Build matched **once** on the language-filtered frame, tag `baseline_cohort`/`midline_cohort` (carried), and **anchor on `baseline_cohort`** so cross-cohort movers neither vanish from both tabs nor get falsely flagged outstanding.
- **Comparison benchmark uses matched pairs** (same learners both phases) → comparable; the per-cohort descriptive benchmark stays cross-sectional and is **captioned as such**.

## Filter scope (addresses 2nd-review Important: outstanding hidden by default Grade 1)

Global filters render once above the tabs: **Language** (default All) + **Grade** (default Grade 1, unchanged for analytical focus). Then:
- `df_lang` = language-only (ALL grades) → feeds the **comparison** and **outstanding** sections (operational; must not hide Grade R/2).
- `df_g` = `df_lang` + grade filter → feeds the per-cohort analytical suite (drill by grade as today).
- The **outstanding** section gets **its own grade control defaulting to "All grades"**; the comparison's single-grade benchmark sub-view gets its own grade selector; its by-grade gain view spans all grades.

## Architecture / `main()` flow

```
df = load_primary_midline_data()             # raw loader already added 'cohort' pre-mask
render_data_freshness(df); render_unmapped_caption(df)
lang, grade = render_global_filters(df)
df_lang = apply_language_filter(df, lang)            # all grades
df_g    = apply_grade_filter(df_lang, grade)         # default Grade 1
matched_all = helpers.build_matched_assessment_pairs(df_lang)   # all grades; carries baseline_cohort
counts = helpers.cohort_counts(df)                   # post-precedence school counts
tab_t, tab_c, tab_s = st.tabs([f"Treatment ({counts['treatment']})",
                               f"Control ({counts['control']})",
                               f"SEF ({counts['sef']})"])
with tab_t: render_treatment_tab(df_lang, df_g, matched_all)
with tab_c: render_cohort_analysis(df_g, matched_all, "control")
with tab_s: render_cohort_analysis(df_g, matched_all, "sef")
```
`render_cohort_analysis(df_g, matched_all, ck)`: `df_cohort = df_g[cohort==ck]`; `matched = matched_all[baseline_cohort==ck]` then narrow to the global grade; optional per-tab school filter (cohort-scoped) narrows both; then the full suite (existing sections + the 4 new ones).
`render_treatment_tab(df_lang, df_g, matched_all)`: `render_treatment_vs_control_section(df_lang, matched_all)` → suite via `render_cohort_analysis(df_g, matched_all, "treatment")` → `render_outstanding_section(df_lang)`.

### Widget-/element-key strategy (addresses Codex #7)

Thread `key_prefix` (cohort key) into every render fn; keys are `f"{key_prefix}_{section}_{element}"`, adding the distinguishing dimension where an element type repeats (e.g. `render_completion_tab`, called twice per cohort, → `f"{key_prefix}_completion_{dimension}_chart"`/`_table`). Key every radio/selectbox/slider/download_button/plotly_chart/dataframe. Comparison/outstanding use `treatment_cmp`/`treatment_out`.

## Data layer — `new_pages/2026/midline_primary_helpers_2026.py`

Reuse as-is: `normalize_primary_assessments`, `latest_assessment_per_phase`, `build_phase_score_summary`, `build_midline_completion_summary`, `build_school_gain_summary`, `benchmark_summary`, `unmatched_midline_learners`.

Add / change (pure, no DB):
1. `normalize_school_name` — strip + collapse internal whitespace + upper (Codex #6). Used for all cohort membership tests + the school filter. (Superset of baseline's `normalize_school_key`; recommend baseline adopt it later.)
2. Cohort lists via `importlib.import_module("data.2026_cohorts")`; sets built with `normalize_school_name`. `classify_cohort(name)` order sef→treatment→control→"other" (after the SAPPHIRE ROAD removal there is no overlap, so precedence is moot and matches baseline). `add_cohort_column(df)` (called in the raw loader, pre-mask). `cohort_counts(df)` → post-precedence unique-school counts. Module-load assertion: SAPPHIRE ROAD → sef only.
3. `build_matched_assessment_pairs`: add `"gender"` **and** `"cohort"` to `metadata_columns`; add `gender` to the `combine_first` loop so a plain `gender` exists (Codex #4); `baseline_cohort`/`midline_cohort` come from the carried `cohort` (Critical + Codex #2).
4. `zero_letter_summary(df, grade)`.
5. `benchmark_by_school_summary(df, grade, threshold, phase="midline")`.
6. `build_ea_gain_summary(matched, min_learners=5)` (per `midline_collected_by`).
7. `build_gender_gain_summary(matched)`.
8. `outstanding_midline_by_school_grade(df_lang)` — on `latest_assessment_per_phase`, treatment baseline learners keyed by **baseline** school×grade; `midline` = has any midline anywhere; `outstanding`/`percent_complete` from the same baseline-ID denominator (Codex #2/#5).
9. `outstanding_baseline_learners(df_lang)` — learner-level treatment baseline rows with no midline anywhere.
10. `build_cohort_gain_summary(matched)` — by `baseline_cohort`×`grade` → mean gain + n.
11. `benchmark_by_cohort_matched(matched, grade, threshold)` — matched pairs, per `baseline_cohort`×phase, using `baseline_/midline_letters_total_correct` + n (Codex #1).

## UI layer — `new_pages/2026/midline_primary_2026.py`

- Refactor existing renderers to take `key_prefix` and key all widgets/charts; add a "cross-sectional" caption to `render_benchmark_section`.
- Split `apply_filters` → `render_global_filters(df)` (Language+Grade above tabs) + `render_school_filter(df_cohort, key_prefix)` (cohort-scoped; returns school or None).
- New renderers (Plotly Express, existing style): `render_zero_letter_section`, `render_benchmark_by_school_section` (RdYlGn), `render_ea_performance_section` (top/bottom, n in hover, min-learners slider), `render_gender_section` (`st.info` if empty), `render_treatment_vs_control_section(df_lang, matched_all)` (gain-by-grade grouped bar color=baseline_cohort; matched benchmark bars; summary table; gain overlay; per-cohort n + "control midline still in progress" caption), `render_outstanding_section(df_lang)` (own all-grades grade control; school×grade table sorted by outstanding; bar of outstanding by school; download of `outstanding_baseline_learners`).

## Caveats

- **SAPPHIRE ROAD**: required removal from `control_schools` → SEF 10 / control 53, baseline consistent; assertion enforces sef-only.
- **Gender sparsity**: 2026 primary `gender` largely empty; section degrades to info message.
- **Control midline early**: ~567 learners/8 schools; comparison shows n + progress caption; guards empty cohorts.
- **Public masking**: cohort derived pre-mask; public users see stable aliases for school/EA/learner labels (matching/grouping still correct); staff see real names.
- **Unmapped/movers**: "other" schools excluded + named in caption; cross-cohort movers handled via baseline anchoring.

## Files

- **Modify (major):** `new_pages/2026/midline_primary_2026.py`.
- **Modify (additions):** `new_pages/2026/midline_primary_helpers_2026.py` (items 1–11).
- **Modify (required, 1 line):** `data/2026_cohorts.py` — delete `SAPPHIRE ROAD PRIMARY SCHOOL` from `control_schools`.
- **Extend (existing pattern):** `tests_and_utils/test_midline_primary_2026.py` — add `unittest` cases (no pytest, no new folder), run `./venv/bin/python -m unittest tests_and_utils/test_midline_primary_2026.py`.
- **Optional:** note cohort tabs in `docs/DATA_SOURCES_DOCUMENTATION.md`.

## Verification

1. **Unit (offline, no DB):** `./venv/bin/python -m unittest tests_and_utils/test_midline_primary_2026.py` — existing 3 pass + new cases: classify/normalize; **`cohort` survives `mask_dataframe(..., authenticated=False)` while `program_name` is aliased**; matched carries `cohort` + `gender`; baseline-anchored mover excluded from outstanding; outstanding on baseline IDs; `build_cohort_gain_summary` & `benchmark_by_cohort_matched` math.
2. **App:** `streamlit run main.py` → "2026 Midline - Primary School": three tabs, no duplicate-ID errors, independent controls; post-precedence tab counts; SAPPHIRE ROAD under SEF only; treatment tab = comparison(top)/suite/outstanding(bottom); outstanding shows all grades by default; new charts render or info-message when sparse.
3. **Logged-out check (the critical path):** open the page without authenticating → cohort tabs still populate (aliased labels), comparison/outstanding non-empty.
4. Global Language/Grade affect the analytical suite; default grade still Grade 1; comparison/outstanding span all grades.

## Revisions log

**After Codex review:** H1 comparison benchmark on matched pairs; H2/M5 build matched once, baseline-anchored, outstanding on baseline IDs vs any-midline; H3 post-precedence `cohort_counts` + assertion; M4 `gender` in metadata + combine loop; M6 `normalize_school_name`; M7 cohort+section+dimension keys; L8 standalone tests.
**After 2nd review:** Critical — derive `cohort` pre-mask (mirror `baseline_2026.py`), carry through matched pairs (public-user correctness). Important — comparison/outstanding use language-filtered all-grade data + own grade control (don't hide Grade R/2 behind default Grade 1). Moderate — extend existing `tests_and_utils/...` unittest suite (no pytest). Moderate — SAPPHIRE ROAD removal elevated to required for cross-page consistency with `baseline_2026.py`.
