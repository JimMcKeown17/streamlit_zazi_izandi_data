# Spec / handoff: "Blending" tab for the 2026 Midline Primary page

**Status:** Reviewed and revised — ready to implement. Design independently reviewed on 2026-06-03 (Codex + a second verification pass against the actual code); all findings folded into §5/§6 below.  Written as a self-contained handoff so a fresh session can implement it without prior conversation context.

**Date:** 2026-06-03 (rev. 2 — review findings folded in)

**Review changelog (rev. 2):** ① midline-only sections must dedup via `latest_assessment_per_phase` — or (chosen here) be driven from the matched set as a single spine; ② mandated a NEW `build_cohort_score_summary` rather than mutating the letters-only `build_cohort_gain_summary`, which is a live dependency of the Treatment tab; ③ added a words-capable EA gain helper; ④ `blending_matched_learners` must set `cohort = baseline_cohort` explicitly (no bare `cohort` exists post-merge); ⑤ the auto-computed `nonwords_change` (≈all-NaN) must be suppressed in every blending view; ⑥ added a `group_track == "Other"` data-quality guard; ⑦ added a track-switcher test matrix and soft (non-equality) count assertions. See §5.4–§6.

---

## 1. Goal

Add a 4th tab — **"Blending"** — to the 2026 Midline Primary Streamlit page. It should answer one question for program staff: **are we succeeding at teaching blending to the groups we put into blending?** "Blending" means progressing from knowing letters to reading words/non-words. So the tab is **words-first** (the real blending indicator), shows **non-words** at midline, and keeps **letters** as a secondary "did they keep gaining" view. Results are **split by cohort** (Treatment vs SEF; control is negligible). Approved structure: **one new Blending tab, cohort-split** (not per-cohort sub-sections, not a SEF-tab add-on).

---

## 2. Project orientation

- **App:** Streamlit data portal ("ZZ Data Portal") for the Zazi iZandi literacy program. Repo root: `/Users/jimmckeown/Development/ZZ Data Site`.
- **Run:** `source venv/bin/activate && streamlit run main.py` (the page is "2026 Midline - Primary School").
- **Stack (verified):** Streamlit **1.51.0**, Plotly **6.3.1**, pandas **2.3.3**. Python venv at `./venv`.
- **The page:** `new_pages/2026/midline_primary_2026.py`.
- **Its data/logic helpers:** `new_pages/2026/midline_primary_helpers_2026.py` (imported in the page via `importlib.import_module("new_pages.2026.midline_primary_helpers_2026")` because the package segment `2026` starts with a digit).
- **Tests:** `tests_and_utils/test_midline_primary_2026.py`, run with `./venv/bin/python -m unittest tests_and_utils.test_midline_primary_2026`. **The repo uses `unittest`, not pytest (pytest is not installed).**
- **Data source:** PostgreSQL table `assessments_2026` (env var `RENDER_DATABASE_URL` in `.env`). Read-only queries are fine and have been authorized by the user. `load_dotenv("<root>/.env")` explicitly when running scripts from stdin (`find_dotenv()` fails there).

### Current state of the page (already implemented and COMMITTED as `d0ac683`; tests passing)
> Note (rev. 2): the cohort-tabs work is now committed (`d0ac683` "…tabs breaking out control groups, treatment, & sef"); the working tree is clean apart from this untracked plan doc. The earlier handoff's "not committed" warning is stale.
The page was just refactored into three cohort tabs. The Blending tab builds on top of that. What already exists:
- **Cohort tabs:** `Treatment (51)` / `Control (53)` / `SEF (10)`, each rendering a shared analysis suite via `render_cohort_analysis(df_g, matched_all, cohort_key, grade)`.
- **Treatment tab extras:** a treatment-vs-control comparison (top) and an outstanding-midline tracker (bottom).
- **Global filters** (Language + Grade, default Grade 1) render once above the tabs. Two derived frames feed everything:
  - `df_lang` = language-filtered, **all grades** (feeds the comparison and outstanding sections — and will feed the Blending tab).
  - `df_g` = `df_lang` + grade filter (feeds the per-cohort suite).
  - `matched_all = helpers.build_matched_assessment_pairs(df_lang)` — built **once**, baseline-anchored.
- 22 unit tests pass; an `AppTest` run of the page has **0 exceptions** in both masked and authenticated modes.

---

## 3. CRITICAL context & gotchas (read before coding)

### 3.1 The page is PUBLIC and data is masked — derive non-sensitive columns BEFORE masking
`midline_primary_page_26` is in `pages_2026_public` (`main.py:124`). For **unauthenticated** users, `mask_dataframe` (`data_privacy.py`) replaces sensitive columns with **deterministic** aliases. The masked columns include **both `program_name`** (in `SCHOOL_COLUMNS`) **and `class_name`** (in `CLASS_COLUMNS`) → e.g. `program_name` becomes `"School A1B2C3"` and `class_name` becomes `"Class 9F3A21"`.

**Consequence for blending:** the group track ("Blending"/"Letters") lives in `class_name` (e.g. `"Achuma Plaatjies-Blending-Group 1"`). If you parse the track from `class_name` *after* masking, every public user sees aliases with no "Blending"/"Letters" in them → the tab breaks for the public exactly like the cohort bug did.

**The fix (mirror the existing `cohort` pattern):** derive a non-sensitive **`group_track`** column from the **raw** `class_name` inside the cached raw loader, *before* `mask_dataframe`. A plain `group_track` column is not in any masking set, so it survives. Then **carry `group_track` through matched pairs** (add it to `build_matched_assessment_pairs` metadata) so you can select blending learners by `midline_group_track == "Blending"` without ever touching the masked `class_name`.

This is the single most important thing to get right. The same trap already bit the `cohort` column (caught in review) and is fixed there the same way (`add_cohort_column` runs in the raw loader before masking — copy that pattern).

### 3.2 Masking is deterministic (so matching still works)
Aliases are `"{Prefix} {sha1(value)[:6].upper()}"`, i.e. stable per entity. So `participant_id` matching (baseline↔midline) and per-school grouping still work under masking. Caveat: `sha1[:6]` is 24 bits, so across ~8,500 learners there are ~1–2 birthday collisions → the **public** view's aggregate counts can differ from the authenticated view by ~1 learner. Immaterial; don't try to "fix" it here. Authenticated (staff) view is exact.

### 3.3 Streamlit duplicate-element IDs across tabs (empirically tested)
- **Widgets** (`st.radio`, `st.selectbox`, `st.slider`, `st.download_button`) raise `StreamlitDuplicateElementId` if the same widget renders in multiple tabs without a unique `key`. **They MUST be keyed.**
- **Display elements** (`st.metric`, `st.dataframe`) do **not** raise (verified via `AppTest`). The page keys `st.plotly_chart`/`st.dataframe` anyway (cheap, future-proof) and leaves `st.metric` unkeyed (it has no `key` param).
- **Pattern:** every render function takes a `key_prefix` and stamps `key=f"{key_prefix}_{section}_{element}"` on widgets/plotly/dataframe. The Blending tab should use `key_prefix="blending"` (and distinct sub-prefixes if a sub-component repeats an element type). Verify with `AppTest` (see §6) — it executes all tab bodies on one run, so it catches collisions.

### 3.4 Cohort definitions (source of truth)
`data/2026_cohorts.py` holds `treatment_schools` (51), `sef_schools` (10), `control_schools` (53). These match the `/pm` dashboard's `lib/pm/cohorts.ts`. `SAPPHIRE ROAD PRIMARY SCHOOL` was removed from `control_schools` so it classifies as SEF only (sef-first precedence in `classify_cohort`). Helpers already exist: `normalize_school_name`, `classify_cohort`, `add_cohort_column`, `cohort_counts`.

---

## 4. Data facts (verified against the DB — use for sanity checks)

- **Group naming convention:** `class_name` = `"{EA name}-{Letters|Blending}-Group {N}"`, e.g. `"Achuma Plaatjies-Blending-Group 1"`. An EA runs both tracks (e.g. Achuma has Blending-Group 1–2 *and* Letters-Group 1–6).
- **Blending-group learners at midline** (midline `class_name` contains "blend"): **Treatment 317, SEF 136, Control 14**. Matched (have a baseline too): **Treatment 306, SEF 136, Control 14**. Control is negligible — show it only if present, with a note.
- **Word reading (matched blending learners), baseline → midline mean:** Treatment **16.0 → 26.7**, SEF **17.5 → 26.6**, Control 7.0 → 9.8. This is the headline success signal.
- **Non-words:** baseline is **NULL** across all cohorts (only captured at midline — EGRA stop-rule / instrument difference). Midline mean ≈ 22 (Treatment 22.6, SEF 22.2). **Show non-words as a midline level/distribution only; do NOT compute or imply a non-word gain.**
- **Letters (matched blending learners), baseline → midline mean:** Treatment 46.3 → 54.9, SEF 46.2 → 52.6 (Control 38.9 → 33.4, n=14 noisy). Blending learners enter already strong on letters (they qualified by knowing them), so letters is a secondary "held/grew" view.
- **Alternative track signal:** `sessions_2026.is_blending` (boolean) — 10,649 blending sessions, 95 distinct blending groups across 34 schools; agrees 100% with the `class_name` "-Blending-" convention on the True side. **Not used** by this design (the midline `class_name` track needs no join and ties directly to assessed scores), but noted in case a future "blending exposure from sessions" view is wanted.
- **Recommendation-based alternative:** `grouping_logic_2026.py` (`assign_groups_2026`, `BLENDING_THRESHOLD = 30`) computes who *should* be blending from baseline `letters_total_correct > 30`. That's the baseline recommendation (used on the baseline page's Grouping QA tab); this tab instead uses the **observed** midline group track. Not needed here.

---

## 5. Design

### 5.1 Placement & data feed
- A 4th `st.tabs` entry **"Blending"** after Treatment/Control/SEF in `main()`.
- It uses **`df_lang`** (language-filtered, **all grades**) and **`matched_all`**, plus **its own grade control defaulting to "All grades"** (blending spans Grade 1 and 2; don't let the global default Grade-1 hide Grade 2). This mirrors how the outstanding tracker and comparison sections already work.
- Cohort is a **color split** (Treatment vs SEF; include control only if rows exist, with a caption).

### 5.2 Identifying blending learners (the safe way)
- Add `group_track` to the raw loader (before masking) from raw `class_name`. (Named `group_track` to mirror `cohort`; it is safe under masking because masking is an exact-match miss on `GROUP_COLUMNS = {"group", "group_name"}`, and the §6 masking-survival test guards this. If you'd rather be immune to a future maintainer adding it to that set, `learning_track` is an equally fine name — just keep it consistent everywhere.)
- Carry `group_track` through `build_matched_assessment_pairs` → `baseline_group_track`, `midline_group_track`.
- **A blending learner = `midline_group_track == "Blending"`** (they were in a blending group at midline). Cohort = `baseline_cohort` (anchored, consistent with the rest of the page). The midline anchor is deliberate: a learner who was in Letters at baseline and Blending at midline IS a blending learner (the success path); a learner who left blending by midline is not. Lock this direction with the track-switcher tests in §6.
- **Single matched spine (denominator — chosen design):** build the blending subset ONCE via `blending_matched_learners(matched_all)` and drive EVERY analytic section from it — word gain, non-words midline level, letters, attainment, by-school, by-EA, and counts. Non-words/attainment are midline levels that live directly on the matched rows (`midline_nonwords_total_correct`, `midline_words_total_correct`), and "# blending groups" = `nunique()` of `midline_class_name` (correct even when masked — aliasing is deterministic, so distinct counts are preserved). This keeps n consistent across the whole tab and never re-derives an analytic subset from `df_lang`. Trade-off: it omits the ~11 treatment learners who have a midline blending row but no matched baseline (≈317 midline vs ≈306 matched) — surface that as a one-line caption, not a section.
- **If you ever derive a subset from `df_lang`** (only the §5.5 data-quality captions do): you MUST call `latest_assessment_per_phase(df_lang)` first, then filter `assessment_type == "midline"` AND `group_track == "Blending"`. Filtering raw `df_lang` directly mixes baseline+midline rows and double-counts repeat responses.

### 5.3 Sections (words-first)
1. **Summary** — per cohort: # blending groups, # matched blending learners, headline avg **word** gain. (`st.metric`s; counts.)
2. **Word reading gain (headline)** — grouped bar of baseline vs midline mean words, Treatment vs SEF; plus a by-grade variant. The "did blending work?" chart.
3. **Word attainment** — % of blending learners reading ≥ N words at midline (threshold slider, keyed) + a distribution/overlay of word gains by cohort.
4. **Non-words (midline only)** — midline non-word mean/distribution by cohort, with an explicit "baseline not captured" caption. **No gain.** ⚠️ The matched frame carries an auto-computed `nonwords_change` that is ≈all-NaN (baseline non-words is NULL); never display it. Use `midline_nonwords_total_correct` only.
5. **Letters (secondary)** — baseline→midline letters for blending learners, by cohort.
6. **By school & EA** — **word** gains per blending school and per EA (top/bottom), so staff see where blending is landing. Use `build_school_gain_summary` for the school data, but render a **words-focused** table — do NOT reuse `render_school_section` verbatim, as it surfaces the misleading "Non-words Change" (= NaN) column. The per-EA view needs the new words-capable EA helper (§5.4); `build_ea_gain_summary` as-is would silently fall back to letters gains.
7. **Export** — matched blending learners via `st.download_button` (keyed): words baseline/midline/change, letters baseline/midline/change, and non-words **midline level only** (not a change).
8. **Data-quality caption** — a `st.caption` with the count of latest midline rows whose `group_track == "Other"` (unparseable `class_name`, hence excluded from the blending subset). Surfacing this number guards against silently undercounting blending learners.

Empty-state guards everywhere (`st.info`) for sparse/zero cohorts (e.g. control).

### 5.4 New / changed helpers (in `midline_primary_helpers_2026.py`, all pure, TDD'd)
- `group_track_from_name(name)` → `"Blending"` / `"Letters"` / `"Other"`. Whitespace/case-robust (reuse `normalize_school_name`-style cleaning). Prefer parsing the hyphen-delimited middle segment of the `"{EA}-{Letters|Blending}-Group {N}"` convention rather than a bare whole-string substring match, so an EA name that happens to contain "letter"/"blend" can't misclassify; fall back to substring only if the segment is absent. Anything without a recognizable track → `"Other"`.
- `add_group_track_column(df)` → adds `group_track` from `class_name`. **Call in the raw loader, before masking**, right after `add_cohort_column`.
- **Modify `build_matched_assessment_pairs`:** add `"group_track"` to the `metadata_columns` list (yielding `baseline_group_track` / `midline_group_track`). It already carries `cohort`, `gender`, etc. the same way — **add one list item only; do not touch the merge or the post-merge coalesce loop.** That coalesce loop intentionally creates bare columns only for `language/grade/program_name/class_name/gender`, so there is NO bare `group_track` (nor bare `cohort`) — always reference `midline_group_track` / `baseline_cohort` explicitly.
- `blending_matched_learners(matched_all)` → subset where `midline_group_track == "Blending"`. Because no bare `cohort` exists post-merge, **explicitly set `cohort = baseline_cohort`** in this helper (don't assume it's there) and test it. Empty-safe (`matched_all` may be empty or missing the column → return an empty frame).
- **Add a NEW `build_cohort_score_summary(matched, score_col)`** → by `baseline_cohort`(×`grade`): baseline mean / midline mean / gain / n for the given score column. ⚠️ **Do NOT generalize or mutate `build_cohort_gain_summary`** — its letters-only output contract (`baseline_letters` / `midline_letters` / `letters_change`) is consumed live by the Treatment-vs-Control section (`midline_primary_2026.py:630`, hover at `:641`, rename table at `:679`); changing it would break that tab. The new helper is purely additive and leaves the existing tabs untouched.
- **Add a words-capable EA gain helper** — either a new `build_ea_score_gain_summary(matched, change_col, min_learners)`, or generalize `build_ea_gain_summary` to take a `change_col` defaulting to `"letters_change"` so existing callers are unaffected. The blending by-EA view passes `"words_change"`.
- Reuse `build_school_gain_summary` (already returns `words_change`) for the per-school data; render it words-first (see §5.3 #6).

### 5.5 Page wiring (`midline_primary_2026.py`)
- Raw loader (`_load_primary_midline_raw`): `... normalize → add_cohort_column → add_group_track_column` (then the existing `load_primary_midline_data` masks it).
- `main()`: change the 3-tuple `tab_treatment, tab_control, tab_sef = st.tabs([...3...])` to a **4-tuple** with a `"Blending"` label after SEF; add `with tab_blending: render_blending_tab(df_lang, matched_all)`. (Don't forget to widen the unpacking — a 3-target unpack of 4 tabs raises `ValueError`.)
- New `render_blending_tab(df_lang, matched_all)` orchestrates the sections with `key_prefix="blending"`. **All analytics** (gains, levels, attainment, by-school, by-EA, counts) come from a subset derived ONCE via `helpers.blending_matched_learners(matched_all)` — the single matched spine (§5.2). `df_lang` is used ONLY for the two data-quality captions, and only after `latest_assessment_per_phase(...)` + `assessment_type == "midline"` dedup — never filtered raw.
- Two data-quality captions near the top: (a) count of latest midline rows with `group_track == "Other"` (excluded, unparseable `class_name`); (b) the ~N midline-blending learners with no matched baseline (≈317 vs ≈306), as a one-line footnote.
- The tab owns **its own grade control defaulting to "All grades"** (blending spans Grade 1 and 2); since it ignores the global Grade filter, mirror `render_outstanding_section`'s clarifying caption so users aren't confused.
- Follow the existing chart style (Plotly Express; `COHORT_COLORS = {"treatment": "#1f5cc4", "control": "#9aa4b2", "sef": "#2ca02c"}`; cohort order treatment, sef[, control]).

---

## 6. Verification

1. **Unit (no DB)** — extend `tests_and_utils/test_midline_primary_2026.py` (`unittest`, not pytest):
   - `group_track_from_name`: "X-Blending-Group 1" → "Blending"; "X-Letters-Group 2" → "Letters"; "Grade 1 - School" / blank / None → "Other"; case/whitespace variants.
   - `add_group_track_column` adds the column; **`group_track` survives `mask_dataframe(..., authenticated=False)`** while `class_name` is aliased (this is the key regression test — mirror the existing `cohort`-survives-masking test).
   - `group_track_from_name` does not misclassify an EA name containing "blend"/"letter" (segment-parse case), on top of the basic Blending/Letters/Other cases.
   - matched pairs carry `baseline_group_track` / `midline_group_track`.
   - `blending_matched_learners` selects only midline-Blending learners AND sets `cohort = baseline_cohort` explicitly (assert the column exists and equals the *baseline* cohort, not the midline one).
   - **track-switcher matrix** (locks the midline-anchored filter direction): baseline Letters / midline Blending → included, cohort = baseline; baseline Blending / midline Letters → excluded; baseline Blending / midline Other → excluded; baseline Blending / midline Blending → included.
   - NEW `build_cohort_score_summary(matched, "words_total_correct")` math on a small synthetic frame; PLUS a regression assertion that `build_cohort_gain_summary`'s output columns are unchanged (guards against accidentally mutating the shared letters-only helper).
   - the words-capable EA helper returns `words_change` when asked and still defaults to `letters_change` for existing callers.
   - the `group_track == "Other"` data-quality count is computed correctly on a synthetic frame.
   - Run: `./venv/bin/python -m unittest tests_and_utils.test_midline_primary_2026` → all pass.
2. **Headless app** — `AppTest` (no browser), both auth states:
   ```python
   from streamlit.testing.v1 import AppTest
   at = AppTest.from_file("new_pages/2026/midline_primary_2026.py", default_timeout=300)
   # at.session_state["user"] = "tester"   # authenticated run
   at.run()
   assert not at.exception           # no duplicate-ID / KeyError across all 4 tabs
   ```
   Run unauthenticated (masked) AND authenticated. Expect **0 exceptions** both ways and the Blending summary metrics to be non-empty. Treat the §4 figures (treatment ≈ 306 / SEF ≈ 136 matched blending learners; word means ≈16 → ≈27) as **soft sanity checks, not equality assertions** — the DB is live and still growing (control midline in progress), so exact counts drift. Assert "non-empty and in a plausible range," never `== 306`.
3. **Manual:** `streamlit run main.py` → "2026 Midline - Primary School" → Blending tab: 4 tabs present, controls independent, words-first sections render, non-words labeled midline-only, cohort split visible.

---

## 7. Key files & reusable functions

- `new_pages/2026/midline_primary_2026.py` — the page. Reuse: `render_cohort_analysis`, `render_global_filters`, `apply_language_filter`/`apply_grade_filter`, `fmt_int`/`fmt_float`, `COHORT_COLORS`, `GRADE_ORDER`, `LANGUAGE_COLORS`, the `key_prefix` convention.
- `new_pages/2026/midline_primary_helpers_2026.py` — reuse: `normalize_school_name`, `classify_cohort`, `add_cohort_column`, `cohort_counts`, `normalize_primary_assessments`, `latest_assessment_per_phase`, `build_matched_assessment_pairs` (carries `cohort`/`gender`; matched columns include `baseline_/midline_{letters,nonwords,words}_total_correct`, `{letters,nonwords,words}_change`, `baseline_cohort`/`midline_cohort`, `grade`, `language`, `program_name`, `class_name`), `build_school_gain_summary` (has `words_change`), `benchmark_by_cohort_matched`, `build_cohort_gain_summary`.
- `data/2026_cohorts.py` — cohort lists.
- `data_privacy.py` — `mask_dataframe`; note `SCHOOL_COLUMNS` (incl. `program_name`) and `CLASS_COLUMNS` (incl. `class_name`) are masked; `is_authenticated()`.
- `tests_and_utils/test_midline_primary_2026.py` — extend here (`unittest`).
- `grouping_logic_2026.py` — `BLENDING_THRESHOLD=30`, `assign_groups_2026` (recommendation-based track; reference only).
- `sessions_2026` table — `is_blending` boolean (alternative signal; reference only).
- Companion plan for the already-built cohort tabs: `docs/PLAN_2026_midline_primary_cohort_tabs.md`.

---

## 8. Suggested implementation order
1. TDD `group_track_from_name` (incl. segment-parse + EA-name-collision cases) → `add_group_track_column` → masking-survival test.
2. Add `"group_track"` to `build_matched_assessment_pairs` metadata (one list item); TDD matched carries `baseline_/midline_group_track`; TDD `blending_matched_learners` (selects midline-Blending, sets `cohort = baseline_cohort`) including the track-switcher matrix.
3. TDD the NEW `build_cohort_score_summary(matched, score_col)` and the words-capable EA helper; add the regression test that `build_cohort_gain_summary`'s columns are unchanged.
4. Wire `add_group_track_column` into the raw loader (right after `add_cohort_column`, before masking).
5. Build `render_blending_tab(df_lang, matched_all)` + sections off the single matched spine; suppress `nonwords_change`; add the "Other" + unmatched-baseline QA captions and the grade-control caption; widen `main()` to a 4-tuple `st.tabs`; key everything with `key_prefix="blending"`.
6. Run unit tests; run `AppTest` (masked + authed) to 0 exceptions with soft count checks; manual smoke.
