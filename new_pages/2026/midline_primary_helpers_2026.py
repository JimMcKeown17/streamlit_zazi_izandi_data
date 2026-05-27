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

    for column in ("language", "grade", "program_name", "class_name"):
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
