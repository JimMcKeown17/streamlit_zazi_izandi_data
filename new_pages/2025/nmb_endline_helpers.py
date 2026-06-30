"""Pure helpers for the 2025 NMB endline cohort analysis pages (extracted for testability).

These pages auto-run display_*() on import, so all testable logic lives here instead.
"""
import pandas as pd

EAS_TO_EXCLUDE = [
    'Sinoxolo Sani', 'Thulani Mthombeni', 'Asanda Betsha', 'Lizalithetha Mhlobo',
    'Siphosethu Mampangashe', 'Hlumela Ntloko', 'Lerato Njovane', 'Ntombizine Goqwana',
    'Zikhona Tshakweni', 'Lucia Jacobs', 'Khahliso Sabasaba', 'Lithemba Mdunyelwa',
    'Raeesa Ishmael', 'Kanyisa Matshaya',
]
_STALE_MERGE_COLS = ["Baseline Score", "Improvement", "Improvement %", "has_baseline_match"]


def _match_key(name_series, grade_series, program_series):
    return (
        name_series.fillna("").astype(str).str.lower().str.strip()
        + "_" + grade_series.fillna("").astype(str).str.strip()
        + "_" + program_series.fillna("").astype(str).str.strip()
    )


def _prep_baseline(baseline_df):
    baseline = baseline_df.copy()
    baseline["Baseline Score"] = baseline["Total cells correct - EGRA Letters"]
    full_name = baseline["Learner First Name"].fillna("") + " " + baseline["Learner Surname"].fillna("")
    baseline["Match Key"] = _match_key(full_name, baseline["Grade"], baseline["Program Name"])
    return baseline.drop_duplicates("Match Key", keep="first")


def _prep_endline(endline_df):
    # Idempotent: drop any baseline/improvement columns from a previously-merged frame.
    endline = endline_df.drop(columns=[c for c in _STALE_MERGE_COLS if c in endline_df.columns]).copy()
    endline["Endline Score"] = endline["Total cells correct - EGRA Letters"]
    endline["Learner Full Name"] = endline["Participant Name"]
    endline["Match Key"] = _match_key(endline["Participant Name"], endline["Grade"], endline["Program Name"])
    return endline


def _dedupe_endline_latest(endline_df):
    """One endline row per learner: keep the latest Response Date per participant_id.

    The export has re-assessments (one learner has 13 rows); collapsing prevents them inflating
    matched-pair metrics. Guarded: if participant_id is absent, returns the frame unchanged.
    """
    if "participant_id" not in endline_df.columns:
        return endline_df
    endline = endline_df.copy()
    if "Response Date" in endline.columns:
        endline = endline.sort_values("Response Date")
    return endline.drop_duplicates("participant_id", keep="last")


def match_baseline_to_endline(baseline_df, endline_df):
    """INNER-match one baseline + latest endline per learner (name+grade+school key). Empty-safe."""
    if baseline_df is None or endline_df is None or baseline_df.empty or endline_df.empty:
        return pd.DataFrame()
    baseline = _prep_baseline(baseline_df)
    endline = _prep_endline(_dedupe_endline_latest(endline_df))
    keep = ["Match Key", "Baseline Score"] + (["Learner EMIS"] if "Learner EMIS" in baseline.columns else [])
    matched = endline.merge(baseline[keep], on="Match Key", how="inner", validate="m:1")
    matched["Improvement"] = matched["Endline Score"] - matched["Baseline Score"]
    matched["Improvement %"] = ((matched["Improvement"] / matched["Baseline Score"]) * 100).round(1)
    matched["Improvement %"] = matched["Improvement %"].replace([float("inf"), float("-inf")], pd.NA)
    return matched


def merge_baseline_onto_endline_left(baseline_df, endline_df):
    """LEFT-join baseline onto ALL endline rows (deduped key, no fan-out). Preserves the _exclude
    contract: Endline Score, Baseline Score (NaN if unmatched), Improvement, has_baseline_match."""
    if baseline_df is None or baseline_df.empty or endline_df is None or endline_df.empty:
        return endline_df
    baseline = _prep_baseline(baseline_df)
    endline = _prep_endline(endline_df)
    merged = endline.merge(baseline[["Match Key", "Baseline Score"]], on="Match Key", how="left", validate="m:1")
    merged["Improvement"] = merged["Endline Score"] - merged["Baseline Score"]
    merged["has_baseline_match"] = merged["Baseline Score"].notna()
    return merged


def apply_outlier_exclusions(df, baseline_df=None):
    """Add outlier-exclusion flags (moved from the _exclude page so it is testable).
    Excludes Grade 1 baseline >= 40; score decline of 10+ (needs Improvement); fixed EA list."""
    df = df.copy()
    df['exclude_high_baseline'] = False
    df['exclude_score_decline'] = False
    df['exclude_ea'] = False
    if 'Baseline Score' in df.columns:
        df['exclude_high_baseline'] = (df['Grade'] == 'Grade 1') & (df['Baseline Score'] >= 40)
    if 'Improvement' in df.columns:
        df['exclude_score_decline'] = (df['Improvement'].notna()) & (df['Improvement'] <= -10)
    df['exclude_ea'] = df['Collected By'].isin(EAS_TO_EXCLUDE)
    df['exclude_outlier'] = df['exclude_high_baseline'] | df['exclude_score_decline'] | df['exclude_ea']
    return df


def build_grade_comparison_rows(baseline_scores, endline_by_grade, grades):
    """Baseline-vs-endline rows per grade, skipping grades with no endline data (no KeyError,
    no fabricated 0 endline). improvement keeps its real sign; render formats with '{:+.1f}'."""
    rows = []
    for grade in grades:
        if grade not in endline_by_grade:
            continue
        baseline = baseline_scores.get(grade)
        if baseline is None:
            continue
        endline = endline_by_grade[grade]
        improvement = endline - baseline
        pct = (improvement / baseline * 100) if baseline else 0
        rows.append({"grade": grade, "baseline": baseline, "endline": endline,
                     "improvement": improvement, "pct_improvement": pct})
    return rows


def build_baseline_endline_chart_rows(comparison_rows, baseline_label, endline_label):
    """Long-format {Grade, Period, Score} rows for the grouped bar chart, built only from
    comparison_rows so grades absent from endline are never shown as 0 bars."""
    chart_rows = []
    for row in comparison_rows:
        chart_rows.append({"Grade": row["grade"], "Period": baseline_label, "Score": row["baseline"]})
        chart_rows.append({"Grade": row["grade"], "Period": endline_label, "Score": row["endline"]})
    return chart_rows


def dedupe_latest_per_learner(df):
    """One row per learner (latest Response Date per participant_id), for learner-level by-grade
    means like the comparison chart. Thin public wrapper over _dedupe_endline_latest; empty- and
    missing-participant_id-safe (returns df unchanged when participant_id is absent)."""
    return _dedupe_endline_latest(df)
