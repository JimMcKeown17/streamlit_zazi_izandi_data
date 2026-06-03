import importlib
import re

import pandas as pd


PRIMARY_LANGUAGES = ("isiXhosa", "English", "Afrikaans")
PHASE_LABELS = {"baseline": "Baseline", "midline": "Midline"}
SCORE_COLUMNS = (
    "letters_total_correct",
    "nonwords_total_correct",
    "words_total_correct",
)
CHANGE_COLUMNS = {
    "letters_total_correct": "letters_change",
    "nonwords_total_correct": "nonwords_change",
    "words_total_correct": "words_change",
}


_cohorts = importlib.import_module("data.2026_cohorts")


def normalize_school_name(value):
    """Normalise a school name for cohort matching: strip, collapse whitespace, uppercase."""
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value).strip()).upper()


TREATMENT_SCHOOLS = {normalize_school_name(name) for name in _cohorts.treatment_schools}
SEF_SCHOOLS = {normalize_school_name(name) for name in _cohorts.sef_schools}
CONTROL_SCHOOLS = {normalize_school_name(name) for name in _cohorts.control_schools}


def classify_cohort(program_name):
    """Return 'treatment', 'sef', 'control', or 'other' for a school name.

    SEF takes precedence so the (now removed) SAPPHIRE ROAD overlap always resolves to SEF,
    and this matches whatever ordering the baseline page uses once the overlap is gone.
    """
    name = normalize_school_name(program_name)
    if not name:
        return "other"
    if name in SEF_SCHOOLS:
        return "sef"
    if name in TREATMENT_SCHOOLS:
        return "treatment"
    if name in CONTROL_SCHOOLS:
        return "control"
    return "other"


def add_cohort_column(df):
    """Add a non-sensitive 'cohort' column derived from the raw program_name.

    Must be called BEFORE mask_dataframe: for unauthenticated users program_name is
    replaced with an alias, so cohort cannot be derived after masking.
    """
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()
    out = df.copy()
    if "program_name" in out.columns:
        out["cohort"] = out["program_name"].map(classify_cohort)
    else:
        out["cohort"] = "other"
    return out


def cohort_counts():
    """Return the defined size of each cohort (post-precedence) for tab labels."""
    return {
        "treatment": len(TREATMENT_SCHOOLS),
        "sef": len(SEF_SCHOOLS),
        "control": len(CONTROL_SCHOOLS),
    }


def normalize_primary_assessments(df):
    """Return a clean primary-school baseline/midline assessment frame."""
    if df is None or df.empty:
        return pd.DataFrame()

    normalized = df.copy()
    if "participant_id" not in normalized.columns:
        normalized["participant_id"] = ""
    if "assessment_type" not in normalized.columns:
        normalized["assessment_type"] = ""

    normalized["participant_id"] = normalized["participant_id"].fillna("").astype(str).str.strip()
    normalized["assessment_type"] = normalized["assessment_type"].fillna("").astype(str).str.lower().str.strip()

    if "language" in normalized.columns:
        normalized = normalized[normalized["language"].isin(PRIMARY_LANGUAGES)].copy()
    normalized = normalized[normalized["assessment_type"].isin(PHASE_LABELS)].copy()

    for date_column in ("response_date", "data_refresh_timestamp"):
        if date_column in normalized.columns:
            normalized[date_column] = pd.to_datetime(normalized[date_column], errors="coerce")

    for score_column in SCORE_COLUMNS:
        if score_column in normalized.columns:
            normalized[score_column] = pd.to_numeric(normalized[score_column], errors="coerce")
        else:
            normalized[score_column] = pd.NA

    normalized = fill_missing_midline_grades_from_baseline(normalized)

    return normalized


def fill_missing_midline_grades_from_baseline(df):
    """Fill blank midline grades from the learner's baseline row when available."""
    if df.empty or "grade" not in df.columns:
        return df

    filled = df.copy()
    baseline = filled[
        (filled["assessment_type"] == "baseline")
        & (filled["participant_id"] != "")
        & (filled["grade"].fillna("").astype(str).str.strip() != "")
    ].copy()
    if baseline.empty:
        return filled

    sort_columns = [col for col in ("response_date", "data_refresh_timestamp", "response_id") if col in baseline.columns]
    if sort_columns:
        baseline = baseline.sort_values(sort_columns)
    grade_map = baseline.drop_duplicates("participant_id", keep="last").set_index("participant_id")["grade"]

    grade_text = filled["grade"].fillna("").astype(str).str.strip()
    missing_midline_grade = (filled["assessment_type"] == "midline") & (grade_text == "")
    filled.loc[missing_midline_grade, "grade"] = filled.loc[missing_midline_grade, "participant_id"].map(grade_map)
    return filled


def latest_assessment_per_phase(df):
    """Keep only each learner's latest response per assessment phase."""
    normalized = normalize_primary_assessments(df)
    if normalized.empty:
        return normalized

    normalized = normalized[normalized["participant_id"] != ""].copy()
    if normalized.empty:
        return normalized

    sort_columns = [col for col in ("response_date", "data_refresh_timestamp", "response_id") if col in normalized.columns]
    if sort_columns:
        normalized = normalized.sort_values(sort_columns)

    return normalized.drop_duplicates(["participant_id", "assessment_type"], keep="last").copy()


def build_matched_assessment_pairs(df):
    """Merge latest baseline and midline rows by TeamPact participant_id."""
    latest = latest_assessment_per_phase(df)
    if latest.empty:
        return pd.DataFrame()

    metadata_columns = [
        "response_id",
        "language",
        "grade",
        "program_name",
        "class_name",
        "collected_by",
        "gender",
        "cohort",
        "response_date",
    ]
    available_metadata = [column for column in metadata_columns if column in latest.columns]
    columns = ["participant_id"] + available_metadata + list(SCORE_COLUMNS)

    baseline = latest[latest["assessment_type"] == "baseline"][columns].copy()
    midline = latest[latest["assessment_type"] == "midline"][columns].copy()

    if baseline.empty or midline.empty:
        return pd.DataFrame()

    baseline = baseline.rename(
        columns={column: f"baseline_{column}" for column in available_metadata + list(SCORE_COLUMNS)}
    )
    midline = midline.rename(
        columns={column: f"midline_{column}" for column in available_metadata + list(SCORE_COLUMNS)}
    )

    matched = baseline.merge(midline, on="participant_id", how="inner")
    for score_column, change_column in CHANGE_COLUMNS.items():
        matched[change_column] = matched[f"midline_{score_column}"] - matched[f"baseline_{score_column}"]

    for column in ("language", "grade", "program_name", "class_name", "gender"):
        midline_column = f"midline_{column}"
        baseline_column = f"baseline_{column}"
        if midline_column in matched.columns and baseline_column in matched.columns:
            midline_values = matched[midline_column].replace("", pd.NA)
            baseline_values = matched[baseline_column].replace("", pd.NA)
            matched[column] = midline_values.combine_first(baseline_values)

    return matched


def build_phase_score_summary(df, dimensions, score_col, agg="mean"):
    """Summarise a score by phase and return baseline/midline/change columns."""
    latest = latest_assessment_per_phase(df)
    if latest.empty or score_col not in latest.columns:
        return pd.DataFrame()

    dimensions = list(dimensions)
    grouped = (
        latest.dropna(subset=[score_col])
        .groupby(dimensions + ["assessment_type"], dropna=False)[score_col]
        .agg(agg)
        .reset_index()
    )
    if grouped.empty:
        return pd.DataFrame()

    grouped["assessment_type"] = grouped["assessment_type"].map(PHASE_LABELS)
    summary = grouped.pivot_table(
        index=dimensions,
        columns="assessment_type",
        values=score_col,
        aggfunc="first",
    ).reset_index()
    summary.columns.name = None

    for phase_label in PHASE_LABELS.values():
        if phase_label not in summary.columns:
            summary[phase_label] = pd.NA

    summary["Change"] = summary["Midline"] - summary["Baseline"]
    for column in ("Baseline", "Midline", "Change"):
        summary[column] = pd.to_numeric(summary[column], errors="coerce").round(1)

    return summary


def build_midline_completion_summary(df, dimension):
    """Count collected midline assessment response rows by school or assessor."""
    normalized = normalize_primary_assessments(df)
    if normalized.empty or dimension not in normalized.columns:
        return pd.DataFrame()

    midline = normalized[normalized["assessment_type"] == "midline"].copy()
    if midline.empty:
        return pd.DataFrame()

    for column in (dimension, "participant_id", "program_name", "collected_by", "language"):
        if column in midline.columns:
            midline[column] = midline[column].fillna("").astype(str).str.strip()

    midline[dimension] = midline[dimension].replace("", "(unknown)")
    midline["_completed_assessment"] = 1
    if "participant_id" in midline.columns:
        midline["_unique_participant_id"] = midline["participant_id"].replace("", pd.NA)

    aggregations = {"assessments_completed": ("_completed_assessment", "sum")}
    if "_unique_participant_id" in midline.columns:
        aggregations["unique_learners"] = ("_unique_participant_id", "nunique")
    if "response_date" in midline.columns:
        aggregations["latest_response"] = ("response_date", "max")
    if dimension != "program_name" and "program_name" in midline.columns:
        aggregations["schools"] = ("program_name", lambda values: values.replace("", pd.NA).nunique())
    if dimension != "collected_by" and "collected_by" in midline.columns:
        aggregations["eas"] = ("collected_by", lambda values: values.replace("", pd.NA).nunique())
    if "language" in midline.columns:
        aggregations["languages"] = ("language", lambda values: values.replace("", pd.NA).nunique())

    summary = midline.groupby(dimension, dropna=False).agg(**aggregations).reset_index()
    for column in ("assessments_completed", "unique_learners", "schools", "eas", "languages"):
        if column in summary.columns:
            summary[column] = pd.to_numeric(summary[column], errors="coerce").fillna(0).astype(int)
    if "latest_response" in summary.columns:
        summary["latest_response"] = pd.to_datetime(summary["latest_response"], errors="coerce")

    return summary.sort_values(["assessments_completed", "unique_learners"], ascending=[False, False])


def build_school_gain_summary(matched):
    """Summarise matched-learner gains by school, language, and grade."""
    if matched is None or matched.empty:
        return pd.DataFrame()

    required = {"program_name", "language", "grade", "letters_change"}
    if not required.issubset(matched.columns):
        return pd.DataFrame()

    summary = (
        matched.groupby(["program_name", "language", "grade"], dropna=False)
        .agg(
            matched_learners=("participant_id", "nunique"),
            baseline_letters=("baseline_letters_total_correct", "mean"),
            midline_letters=("midline_letters_total_correct", "mean"),
            letters_change=("letters_change", "mean"),
            nonwords_change=("nonwords_change", "mean"),
            words_change=("words_change", "mean"),
        )
        .reset_index()
    )

    for column in (
        "baseline_letters",
        "midline_letters",
        "letters_change",
        "nonwords_change",
        "words_change",
    ):
        summary[column] = pd.to_numeric(summary[column], errors="coerce").round(1)

    return summary.sort_values(["matched_learners", "letters_change"], ascending=[False, False])


def benchmark_summary(df, grade, threshold):
    """Return baseline/midline benchmark rates for the latest rows per learner."""
    latest = latest_assessment_per_phase(df)
    if latest.empty:
        return pd.DataFrame()

    grade_df = latest[latest["grade"] == grade].copy()
    if grade_df.empty:
        return pd.DataFrame()

    rows = []
    for phase_key, phase_label in PHASE_LABELS.items():
        phase_df = grade_df[grade_df["assessment_type"] == phase_key]
        total = len(phase_df)
        above = int((phase_df["letters_total_correct"] >= threshold).sum()) if total else 0
        rows.append(
            {
                "Phase": phase_label,
                "Learners": total,
                "At/Above Benchmark": above,
                "Percent": round((above / total * 100), 1) if total else 0,
            }
        )
    return pd.DataFrame(rows)


def unmatched_midline_learners(df):
    """Return latest midline rows with no latest baseline partner."""
    latest = latest_assessment_per_phase(df)
    if latest.empty:
        return pd.DataFrame()

    baseline_ids = set(latest[latest["assessment_type"] == "baseline"]["participant_id"])
    midline = latest[latest["assessment_type"] == "midline"].copy()
    return midline[~midline["participant_id"].isin(baseline_ids)].copy()


def zero_letter_summary(df, grade):
    """Percent of learners with zero letters correct, per phase, for a grade."""
    latest = latest_assessment_per_phase(df)
    if latest.empty:
        return pd.DataFrame()
    grade_df = latest[latest["grade"] == grade]
    if grade_df.empty:
        return pd.DataFrame()

    rows = []
    for phase_key, phase_label in PHASE_LABELS.items():
        phase_df = grade_df[grade_df["assessment_type"] == phase_key]
        total = len(phase_df)
        zero = int((phase_df["letters_total_correct"] == 0).sum()) if total else 0
        rows.append(
            {
                "Phase": phase_label,
                "Learners": total,
                "Zero Letters": zero,
                "Percent": round((zero / total * 100), 1) if total else 0,
            }
        )
    return pd.DataFrame(rows)


def benchmark_by_school_summary(df, grade, threshold, phase="midline"):
    """Percent of learners at/above a letter threshold per school, for one grade and phase."""
    latest = latest_assessment_per_phase(df)
    if latest.empty:
        return pd.DataFrame()

    subset = latest[(latest["grade"] == grade) & (latest["assessment_type"] == phase)].copy()
    if subset.empty:
        return pd.DataFrame()

    subset["_at_or_above"] = (subset["letters_total_correct"] >= threshold).astype(int)
    summary = (
        subset.groupby("program_name", dropna=False)
        .agg(learners=("participant_id", "nunique"), at_or_above=("_at_or_above", "sum"))
        .reset_index()
    )
    summary["at_or_above"] = summary["at_or_above"].astype(int)
    summary["percent"] = (summary["at_or_above"] / summary["learners"] * 100).round(1)
    return summary.sort_values("percent", ascending=False).reset_index(drop=True)


def build_ea_gain_summary(matched, min_learners=5):
    """Mean letter gain per assessing EA (midline collector), filtered to a minimum sample."""
    if matched is None or matched.empty or "midline_collected_by" not in matched.columns:
        return pd.DataFrame()

    summary = (
        matched.groupby("midline_collected_by", dropna=False)
        .agg(matched_learners=("participant_id", "nunique"), letters_change=("letters_change", "mean"))
        .reset_index()
        .rename(columns={"midline_collected_by": "ea"})
    )
    summary["letters_change"] = pd.to_numeric(summary["letters_change"], errors="coerce").round(1)
    summary = summary[summary["matched_learners"] >= min_learners]
    return summary.sort_values("letters_change", ascending=False).reset_index(drop=True)


def build_gender_gain_summary(matched):
    """Mean letter gain by gender (empty frame if no gender data is present)."""
    if matched is None or matched.empty or "gender" not in matched.columns:
        return pd.DataFrame()

    gendered = matched.copy()
    gendered["gender"] = gendered["gender"].fillna("").astype(str).str.strip()
    gendered = gendered[gendered["gender"] != ""]
    if gendered.empty:
        return pd.DataFrame()

    summary = (
        gendered.groupby("gender", dropna=False)
        .agg(matched_learners=("participant_id", "nunique"), letters_change=("letters_change", "mean"))
        .reset_index()
    )
    summary["letters_change"] = pd.to_numeric(summary["letters_change"], errors="coerce").round(1)
    return summary.sort_values("matched_learners", ascending=False).reset_index(drop=True)


def outstanding_midline_by_school_grade(df):
    """Treatment baseline learners still missing a midline, summarised by baseline school and grade.

    Outstanding = a learner with a treatment baseline and no midline ANYWHERE (so a learner who
    moved cohorts and was re-assessed elsewhere is not falsely flagged). percent_complete uses the
    baseline-learner denominator.
    """
    if df is None or len(df) == 0:
        return pd.DataFrame()
    frame = df if "cohort" in df.columns else add_cohort_column(df)
    latest = latest_assessment_per_phase(frame)
    if latest.empty:
        return pd.DataFrame()

    midline_ids = set(latest[latest["assessment_type"] == "midline"]["participant_id"])
    baseline = latest[(latest["assessment_type"] == "baseline") & (latest["cohort"] == "treatment")].copy()
    if baseline.empty:
        return pd.DataFrame()

    baseline["_has_midline"] = baseline["participant_id"].isin(midline_ids).astype(int)
    summary = (
        baseline.groupby(["program_name", "grade"], dropna=False)
        .agg(baseline_learners=("participant_id", "nunique"), midline_learners=("_has_midline", "sum"))
        .reset_index()
    )
    summary["midline_learners"] = summary["midline_learners"].astype(int)
    summary["outstanding"] = summary["baseline_learners"] - summary["midline_learners"]
    summary["percent_complete"] = (summary["midline_learners"] / summary["baseline_learners"] * 100).round(1)
    return summary.sort_values(["outstanding", "baseline_learners"], ascending=[False, False]).reset_index(drop=True)


def outstanding_baseline_learners(df):
    """Learner-level treatment baseline rows whose learner has no midline assessment anywhere."""
    if df is None or len(df) == 0:
        return pd.DataFrame()
    frame = df if "cohort" in df.columns else add_cohort_column(df)
    latest = latest_assessment_per_phase(frame)
    if latest.empty:
        return pd.DataFrame()

    midline_ids = set(latest[latest["assessment_type"] == "midline"]["participant_id"])
    baseline = latest[(latest["assessment_type"] == "baseline") & (latest["cohort"] == "treatment")].copy()
    return baseline[~baseline["participant_id"].isin(midline_ids)].copy()


def build_cohort_gain_summary(matched):
    """Mean letter gain by baseline cohort and grade (treatment-vs-control comparison)."""
    if matched is None or matched.empty:
        return pd.DataFrame()
    required = {"baseline_cohort", "grade", "letters_change"}
    if not required.issubset(matched.columns):
        return pd.DataFrame()

    summary = (
        matched.groupby(["baseline_cohort", "grade"], dropna=False)
        .agg(
            matched_learners=("participant_id", "nunique"),
            baseline_letters=("baseline_letters_total_correct", "mean"),
            midline_letters=("midline_letters_total_correct", "mean"),
            letters_change=("letters_change", "mean"),
        )
        .reset_index()
        .rename(columns={"baseline_cohort": "cohort"})
    )
    for column in ("baseline_letters", "midline_letters", "letters_change"):
        summary[column] = pd.to_numeric(summary[column], errors="coerce").round(1)
    return summary


def benchmark_by_cohort_matched(matched, grade, threshold):
    """Percent at/above a letter threshold for the SAME matched learners, by baseline cohort and phase."""
    if matched is None or matched.empty or "baseline_cohort" not in matched.columns:
        return pd.DataFrame()

    grade_df = matched[matched["grade"] == grade]
    if grade_df.empty:
        return pd.DataFrame()

    rows = []
    for cohort_key, group in grade_df.groupby("baseline_cohort", dropna=False):
        total = len(group)
        for phase_key, phase_label in PHASE_LABELS.items():
            column = f"{phase_key}_letters_total_correct"
            above = int((group[column] >= threshold).sum()) if total and column in group.columns else 0
            rows.append(
                {
                    "cohort": cohort_key,
                    "Phase": phase_label,
                    "Learners": total,
                    "At/Above Benchmark": above,
                    "Percent": round((above / total * 100), 1) if total else 0,
                }
            )
    return pd.DataFrame(rows)
