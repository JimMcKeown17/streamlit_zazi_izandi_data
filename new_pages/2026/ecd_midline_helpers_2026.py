"""Data helpers for the 2026 ECD midline page (survey 805 baseline vs survey 891 midline).

Everything is CROSS-SECTIONAL: the ECD baseline has no participant IDs, so there is no
learner matching. Per the plan review, all analytic metrics count RAW response rows for
BOTH phases (deduping only the midline would mix units), and unique-learner counts appear
only in operational summaries gated strictly on assessment_type == 'midline' — never on
"has a participant_id", because mask_dataframe back-fills baseline participant_id from
learner names for public users.

The primary-school helpers (midline_primary_helpers_2026) cannot be reused: their
normalizer filters to the three primary languages and their analytics dedupe to the latest
row per participant.
"""

import pandas as pd


PHASE_LABELS = {"baseline": "Baseline", "midline": "Midline"}


def normalize_ecd_assessments(df):
    """Return a clean ECD baseline/midline frame: typed dates and scores, valid phases only.

    Drops literal 'null' grades (4 legacy baseline rows; keeps headline counts consistent
    with the ECD baseline page, which filters them in SQL).
    """
    if df is None or df.empty:
        return pd.DataFrame()

    normalized = df.copy()
    if "assessment_type" not in normalized.columns:
        normalized["assessment_type"] = ""
    normalized["assessment_type"] = normalized["assessment_type"].fillna("").astype(str).str.lower().str.strip()
    normalized = normalized[normalized["assessment_type"].isin(PHASE_LABELS)].copy()

    if "grade" in normalized.columns:
        grade_text = normalized["grade"].fillna("").astype(str).str.strip().str.lower()
        normalized = normalized[grade_text != "null"].copy()

    for date_column in ("response_date", "data_refresh_timestamp"):
        if date_column in normalized.columns:
            normalized[date_column] = pd.to_datetime(normalized[date_column], errors="coerce")

    if "letters_total_correct" in normalized.columns:
        normalized["letters_total_correct"] = pd.to_numeric(normalized["letters_total_correct"], errors="coerce")
    else:
        normalized["letters_total_correct"] = pd.NA

    return normalized


def _phase_frames(df):
    """Yield (phase_label, frame) pairs over the normalized data, in Baseline→Midline order."""
    normalized = normalize_ecd_assessments(df)
    if normalized.empty:
        return []
    return [
        (phase_label, normalized[normalized["assessment_type"] == phase_key])
        for phase_key, phase_label in PHASE_LABELS.items()
    ]


def build_phase_letter_summary(df):
    """Per-phase cross-sectional letters summary over raw response rows.

    Columns: Phase, Assessments, Centers, Mean Letters, Median Letters.
    Baseline rows carry no program_name (legacy survey 805), so baseline Centers is 0.
    """
    rows = []
    for phase_label, frame in _phase_frames(df):
        if frame.empty:
            continue
        letters = frame["letters_total_correct"].dropna()
        centers = 0
        if "program_name" in frame.columns:
            centers = frame["program_name"].fillna("").astype(str).str.strip().replace("", pd.NA).nunique()
        rows.append(
            {
                "Phase": phase_label,
                "Assessments": len(frame),
                "Centers": int(centers),
                "Mean Letters": round(letters.mean(), 1) if not letters.empty else pd.NA,
                "Median Letters": round(letters.median(), 1) if not letters.empty else pd.NA,
            }
        )
    return pd.DataFrame(rows)


def zero_letter_summary(df):
    """Percent of raw response rows scoring 0 letters correct, per phase."""
    rows = []
    for phase_label, frame in _phase_frames(df):
        total = len(frame)
        zero = int((frame["letters_total_correct"] == 0).sum()) if total else 0
        rows.append(
            {
                "Phase": phase_label,
                "Assessments": total,
                "Zero Letters": zero,
                "Percent": round(zero / total * 100, 1) if total else 0,
            }
        )
    return pd.DataFrame(rows)


def benchmark_summary(df, threshold):
    """Percent of raw response rows at/above a letters threshold, per phase."""
    rows = []
    for phase_label, frame in _phase_frames(df):
        total = len(frame)
        above = int((frame["letters_total_correct"] >= threshold).sum()) if total else 0
        rows.append(
            {
                "Phase": phase_label,
                "Assessments": total,
                "At/Above Benchmark": above,
                "Percent": round(above / total * 100, 1) if total else 0,
            }
        )
    return pd.DataFrame(rows)


def build_midline_dimension_summary(df, dimension, threshold=None):
    """Midline-only summary by center (program_name) or assessor (collected_by).

    Counts raw midline response rows; unique_learners uses participant_id, which is safe
    here ONLY because the frame is phase-gated to midline first (baseline participant_id
    is name-derived for public users — see module docstring). When ``threshold`` is given,
    adds at_or_above / percent columns for the letters benchmark.
    """
    normalized = normalize_ecd_assessments(df)
    if normalized.empty or dimension not in normalized.columns:
        return pd.DataFrame()

    midline = normalized[normalized["assessment_type"] == "midline"].copy()
    if midline.empty:
        return pd.DataFrame()

    midline[dimension] = midline[dimension].fillna("").astype(str).str.strip().replace("", "(unknown)")
    if "participant_id" in midline.columns:
        midline["_unique_participant_id"] = (
            midline["participant_id"].fillna("").astype(str).str.strip().replace("", pd.NA)
        )
    else:
        midline["_unique_participant_id"] = pd.NA

    aggregations = {
        "assessments": ("response_id", "count"),
        "unique_learners": ("_unique_participant_id", "nunique"),
        "mean_letters": ("letters_total_correct", "mean"),
    }
    if threshold is not None:
        midline["_at_or_above"] = (midline["letters_total_correct"] >= threshold).astype(int)
        aggregations["at_or_above"] = ("_at_or_above", "sum")

    summary = midline.groupby(dimension, dropna=False).agg(**aggregations).reset_index()
    summary["mean_letters"] = pd.to_numeric(summary["mean_letters"], errors="coerce").round(1)
    for column in ("assessments", "unique_learners", "at_or_above"):
        if column in summary.columns:
            summary[column] = pd.to_numeric(summary[column], errors="coerce").fillna(0).astype(int)
    if threshold is not None:
        summary["percent"] = (summary["at_or_above"] / summary["assessments"] * 100).round(1)

    return summary.sort_values(["assessments", "mean_letters"], ascending=[False, False]).reset_index(drop=True)


def build_daily_assessment_counts(df):
    """Raw response rows captured per day, split by phase (capture volume, repeats count).

    Same output shape as the primary-page helper: date (day-floored Timestamp),
    Phase, assessments. Rows without a parseable response_date are dropped.
    """
    normalized = normalize_ecd_assessments(df)
    if normalized.empty or "response_date" not in normalized.columns:
        return pd.DataFrame()

    dated = normalized.dropna(subset=["response_date"]).copy()
    if dated.empty:
        return pd.DataFrame()

    dated["date"] = dated["response_date"].dt.normalize()
    dated["Phase"] = dated["assessment_type"].map(PHASE_LABELS)
    return (
        dated.groupby(["date", "Phase"], dropna=False)
        .size()
        .reset_index(name="assessments")
        .sort_values("date")
        .reset_index(drop=True)
    )
