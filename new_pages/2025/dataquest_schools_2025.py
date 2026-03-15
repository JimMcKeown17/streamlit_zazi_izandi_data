from collections import Counter

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

from data_loader import (
    load_assessments_endline_2025,
    load_sessions_2025,
    load_zazi_izandi_2025_tp,
)
from process_teampact_data import process_teampact_data


# Keep this list aligned with teampact_sessions_2025.py
SELECTED_SCHOOLS_LIST = [
    "Aaron Gqadu Primary School",
    "Ben Sinuka Primary School",
    "Coega Primary School",
    "Dumani Primary School",
    "Ebongweni Public Primary School",
    "Elufefeni Primary School",
    "Empumalanga Primary School",
    "Enkululekweni Primary School",
    "Esitiyeni Public Primary School",
    "Fumisukoma Primary School",
    "Ilinge Primary School",
    "Isaac Booi Senior Primary School",
    "James Ntungwana Primary School",
    "Jarvis Gqamlana Public Primary School",
    "Joe Slovo Primary School",
    "Little Flower Primary School",
    "Magqabi Primary School",
    "Mjuleni Junior Primary School",
    "Mngcunube Primary School",
    "Molefe Senior Primary School",
    "Noninzi Luzipho Primary School",
    "Ntlemeza Primary School",
    "Phindubuye Primary School",
    "Seyisi Primary School",
    "Sikhothina Primary School",
    "Soweto-On-Sea Primary School",
    "Stephen Nkomo Senior Primary School",
    "W B Tshume Primary School",
]

GRADE_OPTIONS = ["All Grades", "Grade R", "Grade 1", "Grade 2"]
COMPARATOR_NON_DQ = "Non-DataQuest schools"
COMPARATOR_OVERALL = "Overall (includes DataQuest)"
COHORT_ORDER = ["0-10", "11-20", "21-30", "31-40", "41+"]
LETTER_SEQUENCE = [
    "a", "e", "i", "o", "u", "b", "l", "m", "k", "p",
    "s", "h", "z", "n", "d", "y", "f", "w", "v", "x",
    "g", "t", "q", "r", "c", "j",
]


def normalize_series(text_series: pd.Series) -> pd.Series:
    return text_series.fillna("").astype(str).str.strip().str.lower()


def create_child_key(
    name_series: pd.Series,
    school_series: pd.Series,
    class_series: pd.Series,
) -> pd.Series:
    normalized_name = normalize_series(name_series)
    normalized_school = normalize_series(school_series)
    normalized_class = normalize_series(class_series)
    return normalized_name + "|" + normalized_school + "|" + normalized_class


def is_dataquest_school(school_series: pd.Series) -> pd.Series:
    selected_lower = {school.lower() for school in SELECTED_SCHOOLS_LIST}
    return normalize_series(school_series).isin(selected_lower)


def get_population_labels(comparator_mode: str) -> tuple[str, str]:
    if comparator_mode == COMPARATOR_OVERALL:
        return "DataQuest", "Overall"
    return "DataQuest", "Non-DataQuest"


def build_population_comparison(
    dataframe: pd.DataFrame,
    school_column_name: str,
    comparator_mode: str,
) -> tuple[pd.DataFrame, str]:
    dataframe = dataframe.copy()
    dataquest_label, comparator_label = get_population_labels(comparator_mode)
    dataquest_mask = is_dataquest_school(dataframe[school_column_name])

    dataquest_df = dataframe[dataquest_mask].copy()
    dataquest_df["Population"] = dataquest_label

    if comparator_mode == COMPARATOR_OVERALL:
        comparator_df = dataframe.copy()
    else:
        comparator_df = dataframe[~dataquest_mask].copy()
    comparator_df["Population"] = comparator_label

    combined_df = pd.concat([dataquest_df, comparator_df], ignore_index=True)
    return combined_df, comparator_label


@st.cache_data(ttl=3600)
def build_matched_baseline_endline_data(
    endline_dataframe: pd.DataFrame,
    baseline_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    if endline_dataframe.empty or baseline_dataframe.empty:
        return pd.DataFrame()

    baseline_prepared_df = baseline_dataframe.copy()
    baseline_prepared_df["Learner Full Name"] = (
        baseline_prepared_df["Learner First Name"].fillna("").astype(str).str.strip()
        + " "
        + baseline_prepared_df["Learner Surname"].fillna("").astype(str).str.strip()
    ).str.strip()
    baseline_prepared_df["Baseline Score"] = baseline_prepared_df["Total cells correct - EGRA Letters"]
    if "Response Date" in baseline_prepared_df.columns:
        baseline_prepared_df["Response Date"] = pd.to_datetime(
            baseline_prepared_df["Response Date"],
            errors="coerce",
        )
    baseline_prepared_df["Match Key"] = (
        normalize_series(baseline_prepared_df["Learner Full Name"])
        + "|"
        + baseline_prepared_df["Grade"].fillna("").astype(str).str.strip()
        + "|"
        + normalize_series(baseline_prepared_df["Program Name"])
    )
    baseline_prepared_df = baseline_prepared_df.sort_values(
        "Response Date",
        ascending=False,
        na_position="last",
    )
    baseline_prepared_df = baseline_prepared_df.drop_duplicates(subset=["Match Key"], keep="first")

    endline_prepared_df = endline_dataframe.copy()
    endline_prepared_df["Learner Full Name"] = endline_prepared_df["Participant Name"]
    endline_prepared_df["Endline Score"] = endline_prepared_df["Total cells correct - EGRA Letters"]
    endline_prepared_df["Match Key"] = (
        normalize_series(endline_prepared_df["Learner Full Name"])
        + "|"
        + endline_prepared_df["Grade"].fillna("").astype(str).str.strip()
        + "|"
        + normalize_series(endline_prepared_df["Program Name"])
    )
    endline_prepared_df = endline_prepared_df.sort_values(
        "Response Date",
        ascending=False,
        na_position="last",
    )
    endline_prepared_df = endline_prepared_df.drop_duplicates(subset=["Match Key"], keep="first")

    matched_df = endline_prepared_df.merge(
        baseline_prepared_df[["Match Key", "Baseline Score", "Learner EMIS"]],
        on="Match Key",
        how="left",
    )
    matched_df["has_baseline_match"] = matched_df["Baseline Score"].notna()
    matched_df["Improvement"] = matched_df["Endline Score"] - matched_df["Baseline Score"]
    return matched_df


@st.cache_data(ttl=3600)
def load_endline_data_2025() -> pd.DataFrame:
    dataframe = load_assessments_endline_2025()
    dataframe = dataframe[dataframe["assessment_type"] == "endline"].copy()

    rename_map = {
        "program_name": "Program Name",
        "class_name": "Class Name",
        "collected_by": "Collected By",
        "response_date": "Response Date",
        "first_name": "First Name",
        "last_name": "Last Name",
        "gender": "Gender",
        "grade": "Grade",
        "language": "Language",
        "total_correct": "Total cells correct - EGRA Letters",
    }
    dataframe = dataframe.rename(columns=rename_map)
    dataframe["Response Date"] = pd.to_datetime(dataframe["Response Date"], errors="coerce")

    if "data_refresh_timestamp" in dataframe.columns:
        dataframe["data_refresh_timestamp"] = pd.to_datetime(
            dataframe["data_refresh_timestamp"],
            errors="coerce",
        )

    dataframe["Participant Name"] = (
        dataframe["First Name"].fillna("").astype(str).str.strip()
        + " "
        + dataframe["Last Name"].fillna("").astype(str).str.strip()
    ).str.strip()
    dataframe["Has Quality Flags"] = (
        dataframe["flag_moving_too_fast"] | dataframe["flag_same_letter_groups"]
    )
    dataframe["Both Flags"] = (
        dataframe["flag_moving_too_fast"] & dataframe["flag_same_letter_groups"]
    )
    dataframe["child_key"] = create_child_key(
        dataframe["Participant Name"],
        dataframe["Program Name"],
        dataframe["Class Name"],
    )
    return dataframe


@st.cache_data(ttl=3600)
def load_baseline_data_2025() -> pd.DataFrame:
    try:
        baseline_xhosa_df, baseline_english_df, baseline_afrikaans_df = load_zazi_izandi_2025_tp()
        if baseline_xhosa_df is None:
            return pd.DataFrame()

        baseline_df = process_teampact_data(
            baseline_xhosa_df,
            baseline_english_df,
            baseline_afrikaans_df,
        )
        if baseline_df.empty:
            return baseline_df

        if "Response Date" in baseline_df.columns:
            baseline_df["Response Date"] = pd.to_datetime(
                baseline_df["Response Date"],
                errors="coerce",
            )
        return baseline_df
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_sessions_data_2025() -> pd.DataFrame:
    dataframe = load_sessions_2025()
    dataframe["session_started_at"] = pd.to_datetime(dataframe["session_started_at"], errors="coerce")
    dataframe = dataframe[dataframe["session_started_at"].notna()].copy()
    dataframe["session_date"] = dataframe["session_started_at"].dt.date
    dataframe["session_week"] = dataframe["session_started_at"].dt.to_period("W")
    dataframe["child_key"] = create_child_key(
        dataframe["participant_name"],
        dataframe["program_name"],
        dataframe["class_name"],
    )
    return dataframe


@st.cache_data(ttl=3600)
def build_endline_child_lookup(endline_dataframe: pd.DataFrame) -> pd.DataFrame:
    sorted_endline = endline_dataframe.sort_values("Response Date", ascending=False).copy()
    lookup_columns = [
        "child_key",
        "Grade",
        "session_count_total",
        "cohort_session_range",
        "Program Name",
        "Class Name",
        "Response Date",
    ]
    lookup_df = sorted_endline[lookup_columns].drop_duplicates(subset=["child_key"], keep="first")
    return lookup_df


@st.cache_data(ttl=3600)
def build_child_dosage_data(
    sessions_dataframe: pd.DataFrame,
    endline_lookup_df: pd.DataFrame,
) -> pd.DataFrame:
    child_grouped = sessions_dataframe.groupby("participant_id", as_index=False).agg(
        total_sessions=("session_id", "nunique"),
        days_attended=("session_date", "nunique"),
        weeks_attended=("session_week", "nunique"),
        child_name=("participant_name", "first"),
        school_name=("program_name", "first"),
        class_name=("class_name", "first"),
        school_type=("school_type", "first"),
        latest_session=("session_started_at", "max"),
    )
    child_grouped["avg_sessions_per_week"] = (
        child_grouped["total_sessions"] / child_grouped["weeks_attended"].clip(lower=1)
    ).round(2)
    child_grouped["sessions_per_active_day"] = (
        child_grouped["total_sessions"] / child_grouped["days_attended"].clip(lower=1)
    ).round(2)
    child_grouped["child_key"] = create_child_key(
        child_grouped["child_name"],
        child_grouped["school_name"],
        child_grouped["class_name"],
    )

    child_grouped = child_grouped.merge(
        endline_lookup_df[["child_key", "Grade", "session_count_total", "cohort_session_range"]],
        on="child_key",
        how="left",
    )
    child_grouped["has_endline_match"] = child_grouped["Grade"].notna()
    child_grouped["is_dataquest"] = is_dataquest_school(child_grouped["school_name"])
    return child_grouped


@st.cache_data(ttl=3600)
def build_group_dosage_data(
    sessions_dataframe: pd.DataFrame,
    child_dosage_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    group_metrics = sessions_dataframe.groupby(["program_name", "class_name"], as_index=False).agg(
        total_sessions=("session_id", "nunique"),
        active_days=("session_date", "nunique"),
        active_weeks=("session_week", "nunique"),
        unique_eas=("user_name", "nunique"),
    )
    group_metrics["sessions_per_active_day"] = (
        group_metrics["total_sessions"] / group_metrics["active_days"].clip(lower=1)
    ).round(2)
    group_metrics["sessions_per_active_week"] = (
        group_metrics["total_sessions"] / group_metrics["active_weeks"].clip(lower=1)
    ).round(2)
    group_metrics["group_key"] = (
        group_metrics["program_name"].fillna("").astype(str).str.strip()
        + " | "
        + group_metrics["class_name"].fillna("").astype(str).str.strip()
    )

    matched_children = child_dosage_dataframe[child_dosage_dataframe["has_endline_match"]].copy()
    grade_by_group = (
        matched_children.groupby(["school_name", "class_name", "Grade"])
        .size()
        .reset_index(name="matched_children")
        .sort_values("matched_children", ascending=False)
        .drop_duplicates(["school_name", "class_name"], keep="first")
    )
    count_by_group = (
        matched_children.groupby(["school_name", "class_name"], as_index=False)
        .agg(
            matched_children=("participant_id", "nunique"),
            median_endline_sessions=("session_count_total", "median"),
        )
    )

    group_metrics = group_metrics.merge(
        grade_by_group[["school_name", "class_name", "Grade"]],
        left_on=["program_name", "class_name"],
        right_on=["school_name", "class_name"],
        how="left",
    ).drop(columns=["school_name"])

    group_metrics = group_metrics.merge(
        count_by_group,
        left_on=["program_name", "class_name"],
        right_on=["school_name", "class_name"],
        how="left",
    ).drop(columns=["school_name"])

    group_metrics["matched_children"] = group_metrics["matched_children"].fillna(0).astype(int)
    group_metrics["is_dataquest"] = is_dataquest_school(group_metrics["program_name"])
    return group_metrics


@st.cache_data(ttl=3600)
def build_session_content_data(
    sessions_dataframe: pd.DataFrame,
    endline_lookup_df: pd.DataFrame,
) -> pd.DataFrame:
    participant_grade = sessions_dataframe[
        ["session_id", "child_key", "program_name", "class_name"]
    ].copy()
    participant_grade = participant_grade.merge(
        endline_lookup_df[["child_key", "Grade", "session_count_total"]],
        on="child_key",
        how="left",
    )

    session_grade = (
        participant_grade.dropna(subset=["Grade"])
        .groupby(["session_id", "Grade"])
        .size()
        .reset_index(name="grade_count")
        .sort_values("grade_count", ascending=False)
        .drop_duplicates("session_id", keep="first")
    )
    session_endline_session_count = (
        participant_grade.groupby("session_id", as_index=False)
        .agg(median_endline_sessions=("session_count_total", "median"))
    )

    session_level = sessions_dataframe.sort_values("session_started_at").drop_duplicates(
        "session_id",
        keep="last",
    )
    content_df = session_level[
        [
            "session_id",
            "session_started_at",
            "session_date",
            "program_name",
            "class_name",
            "letters_taught",
            "num_letters_taught",
        ]
    ].copy()
    content_df = content_df.merge(
        session_grade[["session_id", "Grade"]],
        on="session_id",
        how="left",
    )
    content_df = content_df.merge(
        session_endline_session_count,
        on="session_id",
        how="left",
    )
    content_df["is_dataquest"] = is_dataquest_school(content_df["program_name"])
    content_df["letters_taught"] = content_df["letters_taught"].fillna("").astype(str).str.strip()
    content_df["has_letters_taught"] = content_df["letters_taught"] != ""
    return content_df


def apply_endline_filters(
    endline_dataframe: pd.DataFrame,
    selected_grade: str,
    only_11_plus: bool,
) -> pd.DataFrame:
    filtered_df = endline_dataframe.copy()
    if selected_grade != "All Grades":
        filtered_df = filtered_df[filtered_df["Grade"] == selected_grade].copy()
    if only_11_plus:
        filtered_df = filtered_df[filtered_df["session_count_total"] >= 11].copy()
    return filtered_df


def apply_matched_filters(
    dataframe: pd.DataFrame,
    selected_grade: str,
    only_11_plus: bool,
    grade_column_name: str = "Grade",
    endline_session_column_name: str = "session_count_total",
) -> pd.DataFrame:
    filtered_df = dataframe.copy()
    if selected_grade != "All Grades":
        filtered_df = filtered_df[filtered_df[grade_column_name] == selected_grade].copy()
    if only_11_plus:
        filtered_df = filtered_df[filtered_df[endline_session_column_name] >= 11].copy()
    return filtered_df


def classify_group_session_band(total_sessions: float) -> str:
    if total_sessions <= 10:
        return "0-10"
    if total_sessions <= 20:
        return "11-20"
    if total_sessions <= 30:
        return "21-30"
    if total_sessions <= 40:
        return "31-40"
    return "41+"


def explode_letters(content_dataframe: pd.DataFrame) -> pd.DataFrame:
    token_rows: list[dict] = []
    for _, row in content_dataframe.iterrows():
        tokens = [token.strip().lower() for token in str(row["letters_taught"]).split(",") if token.strip()]
        for token in tokens:
            token_rows.append({"Population": row["Population"], "Letter": token})
    return pd.DataFrame(token_rows)


def build_safe_linear_trend(
    x_series: pd.Series,
    y_series: pd.Series,
    point_count: int = 100,
) -> tuple[np.ndarray, np.ndarray] | None:
    numeric_x_series = pd.to_numeric(x_series, errors="coerce")
    numeric_y_series = pd.to_numeric(y_series, errors="coerce")
    valid_mask = np.isfinite(numeric_x_series) & np.isfinite(numeric_y_series)

    valid_x_values = numeric_x_series[valid_mask]
    valid_y_values = numeric_y_series[valid_mask]
    if len(valid_x_values) < 2 or valid_x_values.nunique() < 2:
        return None

    try:
        slope, intercept = np.polyfit(
            valid_x_values.to_numpy(),
            valid_y_values.to_numpy(),
            1,
        )
    except (np.linalg.LinAlgError, ValueError, FloatingPointError):
        return None
    if not np.isfinite(slope) or not np.isfinite(intercept):
        return None

    x_line_values = np.linspace(
        float(valid_x_values.min()),
        float(valid_x_values.max()),
        point_count,
    )
    y_line_values = slope * x_line_values + intercept
    if not np.all(np.isfinite(y_line_values)):
        return None
    return x_line_values, y_line_values


def render_cohort_performance_reference_chart(
    endline_dataframe: pd.DataFrame,
    baseline_dataframe: pd.DataFrame,
    comparator_mode: str,
    key_prefix: str,
) -> None:
    st.divider()
    st.markdown("### Cohort Performance Analysis")
    st.markdown("**Key Question:** Do more sessions lead to better EGRA performance?")
    st.info(
        "How to interpret this section: `Endline Score` charts show where learners finished, "
        "`Baseline` charts show where they started, and `Improvement` charts show the change. "
        "A cohort can improve a lot but still have a lower endline score if it started lower."
    )

    toggle_col_left, toggle_col_right = st.columns([1, 3])
    with toggle_col_left:
        use_mean = st.toggle(
            "Show Mean (instead of Median)",
            value=False,
            key=f"{key_prefix}_cohort_mean_toggle",
        )

    stat_method = "mean" if use_mean else "median"
    stat_label = "Mean" if use_mean else "Median"

    cohort_df = endline_dataframe[
        endline_dataframe["cohort_session_range"].notna()
        & (endline_dataframe["cohort_session_range"] != "")
    ].copy()
    if cohort_df.empty:
        st.warning("No cohort data available for this filter selection.")
        return

    cohort_df["cohort_session_range"] = pd.Categorical(
        cohort_df["cohort_session_range"],
        categories=COHORT_ORDER,
        ordered=True,
    )

    cohort_stats = (
        cohort_df.groupby("cohort_session_range")
        .agg(
            score=("Total cells correct - EGRA Letters", stat_method),
            count=("response_id", "count"),
        )
        .reset_index()
        .rename(columns={"cohort_session_range": "Cohort"})
        .sort_values("Cohort")
    )

    chart = px.bar(
        cohort_stats,
        x="Cohort",
        y="score",
        title=f"{stat_label} EGRA Scores by Session Cohort",
        labels={"score": f"{stat_label} Correct Letters", "Cohort": "Session Cohort"},
        color="score",
        color_continuous_scale="Viridis",
    )
    chart.update_traces(
        text=[f"{score:.1f}<br>n={count}" for score, count in zip(cohort_stats["score"], cohort_stats["count"])],
        textposition="outside",
    )
    st.plotly_chart(
        chart,
        use_container_width=True,
        key=f"{key_prefix}_cohort_performance_chart",
    )

    st.markdown("#### Cohort Improvement (Matched Learners)")
    st.caption(
        "Method: Name + grade + school matching between baseline and endline, then "
        "learner-level improvement is aggregated by endline cohort."
    )

    matched_df = build_matched_baseline_endline_data(endline_dataframe, baseline_dataframe)
    if matched_df.empty:
        st.warning("No matched baseline-endline data is available for improvement charts.")
        return

    matched_only_df = matched_df[matched_df["has_baseline_match"]].copy()
    if matched_only_df.empty:
        st.warning("No matched learners found for the current filters.")
        return

    compare_endline_df, comparator_label = build_population_comparison(
        endline_dataframe,
        "Program Name",
        comparator_mode,
    )
    compare_matched_df, _ = build_population_comparison(
        matched_only_df,
        "Program Name",
        comparator_mode,
    )

    coverage_df = (
        compare_endline_df.groupby("Population", as_index=False)
        .agg(total_endline=("response_id", "count"))
        .merge(
            compare_matched_df.groupby("Population", as_index=False).agg(matched=("response_id", "count")),
            on="Population",
            how="left",
        )
    )
    coverage_df["matched"] = coverage_df["matched"].fillna(0).astype(int)
    coverage_df["match_rate_pct"] = (
        coverage_df["matched"] / coverage_df["total_endline"].clip(lower=1) * 100
    ).round(1)
    st.dataframe(coverage_df, hide_index=True, use_container_width=True)

    matched_cohort_df = compare_matched_df[
        compare_matched_df["cohort_session_range"].notna()
        & (compare_matched_df["cohort_session_range"] != "")
    ].copy()
    if matched_cohort_df.empty:
        st.warning("No cohort data is available in the matched sample.")
        return

    cohort_coverage_df = (
        compare_matched_df.groupby("Population", as_index=False)
        .agg(matched_total=("response_id", "count"))
        .merge(
            matched_cohort_df.groupby("Population", as_index=False).agg(with_cohort=("response_id", "count")),
            on="Population",
            how="left",
        )
    )
    cohort_coverage_df["with_cohort"] = cohort_coverage_df["with_cohort"].fillna(0).astype(int)
    cohort_coverage_df["without_cohort"] = cohort_coverage_df["matched_total"] - cohort_coverage_df["with_cohort"]
    cohort_coverage_df["cohort_coverage_pct"] = (
        cohort_coverage_df["with_cohort"] / cohort_coverage_df["matched_total"].clip(lower=1) * 100
    ).round(1)
    st.caption("`n` labels on bars use matched learners with a cohort assignment only.")
    st.dataframe(cohort_coverage_df, hide_index=True, use_container_width=True)

    improvement_by_cohort_df = (
        matched_cohort_df.groupby(["Population", "cohort_session_range"], as_index=False)
        .agg(
            improvement=("Improvement", stat_method),
            learners=("response_id", "count"),
        )
        .rename(columns={"cohort_session_range": "Cohort"})
    )
    improvement_by_cohort_df["n_label"] = improvement_by_cohort_df["learners"].apply(lambda value: f"n={value}")
    improvement_by_cohort_df["Cohort"] = pd.Categorical(
        improvement_by_cohort_df["Cohort"],
        categories=COHORT_ORDER,
        ordered=True,
    )
    improvement_by_cohort_df = improvement_by_cohort_df.sort_values(["Cohort", "Population"])

    improvement_chart = px.bar(
        improvement_by_cohort_df,
        x="Cohort",
        y="improvement",
        color="Population",
        text="n_label",
        barmode="group",
        title=f"{stat_label} Improvement by Cohort (Endline - Baseline)",
        labels={"improvement": f"{stat_label} Improvement (Letters)"},
    )
    improvement_chart.add_hline(y=0, line_dash="dash", line_color="#475569")
    improvement_chart.update_traces(textposition="outside")
    st.plotly_chart(
        improvement_chart,
        use_container_width=True,
        key=f"{key_prefix}_cohort_matched_improvement_chart",
    )

    st.markdown("#### Cohort Baseline (Matched Sample)")
    st.caption(
        "Helper chart: baseline cohort medians for the same matched sample used above. "
        "Use this to check whether higher-dosage cohorts started from lower baseline scores."
    )
    baseline_by_cohort_df = (
        matched_cohort_df.groupby(["Population", "cohort_session_range"], as_index=False)
        .agg(
            baseline_score=("Baseline Score", stat_method),
            learners=("response_id", "count"),
        )
        .rename(columns={"cohort_session_range": "Cohort"})
    )
    baseline_by_cohort_df["Cohort"] = pd.Categorical(
        baseline_by_cohort_df["Cohort"],
        categories=COHORT_ORDER,
        ordered=True,
    )
    baseline_by_cohort_df = baseline_by_cohort_df.sort_values(["Cohort", "Population"])
    baseline_cohort_chart = px.bar(
        baseline_by_cohort_df,
        x="Cohort",
        y="baseline_score",
        color="Population",
        barmode="group",
        title=f"{stat_label} Baseline Score by Cohort (Matched Sample)",
        labels={"baseline_score": f"{stat_label} Baseline Correct Letters"},
    )
    baseline_cohort_chart.update_traces(
        text=[f"n={count}" for count in baseline_by_cohort_df["learners"]],
        textposition="outside",
    )
    st.plotly_chart(
        baseline_cohort_chart,
        use_container_width=True,
        key=f"{key_prefix}_cohort_baseline_chart",
    )

    st.markdown("#### Cohort Improvement (Aggregate Shift)")
    st.caption(
        "Method: Uses the same matched cohort sample, but compares baseline and endline "
        "distribution-level cohort scores (not per-learner deltas)."
    )

    aggregate_shift_df = (
        matched_cohort_df.groupby(["Population", "cohort_session_range"], as_index=False)
        .agg(
            baseline_score=("Baseline Score", stat_method),
            endline_score=("Endline Score", stat_method),
            learners=("response_id", "count"),
        )
        .rename(columns={"cohort_session_range": "Cohort"})
    )
    aggregate_shift_df["Cohort"] = pd.Categorical(
        aggregate_shift_df["Cohort"],
        categories=COHORT_ORDER,
        ordered=True,
    )
    aggregate_shift_df = aggregate_shift_df.sort_values(["Population", "Cohort"])

    aggregate_shift_long_df = aggregate_shift_df.melt(
        id_vars=["Population", "Cohort", "learners"],
        value_vars=["baseline_score", "endline_score"],
        var_name="Period",
        value_name="Score",
    )
    aggregate_shift_long_df["Period"] = aggregate_shift_long_df["Period"].map(
        {"baseline_score": "Baseline", "endline_score": "Endline"}
    )

    aggregate_shift_chart = px.bar(
        aggregate_shift_long_df,
        x="Cohort",
        y="Score",
        color="Period",
        barmode="group",
        facet_col="Population",
        title=f"{stat_label} Baseline vs Endline by Cohort (Matched Sample)",
        labels={"Score": f"{stat_label} Correct Letters"},
        category_orders={"Period": ["Baseline", "Endline"]},
        color_discrete_map={"Baseline": "#94a3b8", "Endline": "#2563eb"},
    )
    st.plotly_chart(
        aggregate_shift_chart,
        use_container_width=True,
        key=f"{key_prefix}_cohort_aggregate_shift_chart",
    )


def render_population_tab(
    endline_dataframe: pd.DataFrame,
    child_dosage_dataframe: pd.DataFrame,
    group_dosage_dataframe: pd.DataFrame,
    comparator_mode: str,
) -> None:
    st.subheader("Population and Coverage Checks")

    endline_compare_df, comparator_label = build_population_comparison(
        endline_dataframe,
        "Program Name",
        comparator_mode,
    )
    child_compare_df, _ = build_population_comparison(
        child_dosage_dataframe,
        "school_name",
        comparator_mode,
    )
    group_compare_df, _ = build_population_comparison(
        group_dosage_dataframe,
        "program_name",
        comparator_mode,
    )

    dataquest_endline = endline_compare_df[endline_compare_df["Population"] == "DataQuest"]
    comparator_endline = endline_compare_df[endline_compare_df["Population"] == comparator_label]
    dataquest_child = child_compare_df[child_compare_df["Population"] == "DataQuest"]
    comparator_child = child_compare_df[child_compare_df["Population"] == comparator_label]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("DataQuest Endline Learners", f"{len(dataquest_endline):,}")
    with col2:
        st.metric(f"{comparator_label} Endline Learners", f"{len(comparator_endline):,}")
    with col3:
        st.metric("DataQuest Session Learners", f"{dataquest_child['participant_id'].nunique():,}")
    with col4:
        st.metric(
            f"{comparator_label} Session Learners",
            f"{comparator_child['participant_id'].nunique():,}",
        )

    coverage_col1, coverage_col2, coverage_col3 = st.columns(3)
    with coverage_col1:
        st.metric("DataQuest Schools in Endline", f"{dataquest_endline['Program Name'].nunique():,}")
    with coverage_col2:
        st.metric("DataQuest Schools in Sessions", f"{dataquest_child['school_name'].nunique():,}")
    with coverage_col3:
        matched_pct = (
            dataquest_child["has_endline_match"].mean() * 100
            if len(dataquest_child) > 0
            else 0
        )
        st.metric("Session Learners Matched to Endline", f"{matched_pct:.1f}%")

    available_endline_schools = {
        school_name.lower()
        for school_name in dataquest_endline["Program Name"].dropna().unique()
    }
    available_session_schools = {
        school_name.lower()
        for school_name in dataquest_child["school_name"].dropna().unique()
    }
    missing_endline = [
        school_name
        for school_name in SELECTED_SCHOOLS_LIST
        if school_name.lower() not in available_endline_schools
    ]
    missing_sessions = [
        school_name
        for school_name in SELECTED_SCHOOLS_LIST
        if school_name.lower() not in available_session_schools
    ]

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**DataQuest schools missing in endline data**")
        if missing_endline:
            st.dataframe(pd.DataFrame({"School": missing_endline}), hide_index=True, use_container_width=True)
        else:
            st.success("All schools in the DataQuest list appear in endline data.")
    with col_b:
        st.markdown("**DataQuest schools missing in sessions data**")
        if missing_sessions:
            st.dataframe(pd.DataFrame({"School": missing_sessions}), hide_index=True, use_container_width=True)
        else:
            st.success("All schools in the DataQuest list appear in sessions data.")

    st.divider()
    grade_mix_df = (
        endline_compare_df.groupby(["Population", "Grade"], as_index=False)
        .size()
        .rename(columns={"size": "Learners"})
    )
    grade_mix_df["Grade"] = pd.Categorical(
        grade_mix_df["Grade"],
        categories=["Grade R", "Grade 1", "Grade 2"],
        ordered=True,
    )
    grade_mix_df = grade_mix_df.sort_values(["Grade", "Population"])

    grade_chart = px.bar(
        grade_mix_df,
        x="Grade",
        y="Learners",
        color="Population",
        barmode="group",
        title="Grade Composition: DataQuest vs Comparator",
    )
    grade_chart.update_traces(text=grade_mix_df["Learners"], textposition="outside")
    st.plotly_chart(grade_chart, use_container_width=True)

    cohort_df = endline_compare_df[
        endline_compare_df["cohort_session_range"].notna()
        & (endline_compare_df["cohort_session_range"] != "")
    ].copy()
    if not cohort_df.empty:
        cohort_summary = (
            cohort_df.groupby(["Population", "cohort_session_range"], as_index=False)
            .size()
            .rename(columns={"size": "Learners", "cohort_session_range": "Cohort"})
        )
        cohort_summary["Cohort"] = pd.Categorical(
            cohort_summary["Cohort"],
            categories=COHORT_ORDER,
            ordered=True,
        )
        cohort_summary = cohort_summary.sort_values(["Cohort", "Population"])
        cohort_chart = px.bar(
            cohort_summary,
            x="Cohort",
            y="Learners",
            color="Population",
            barmode="group",
            title="Cohort Composition: DataQuest vs Comparator",
        )
        st.plotly_chart(cohort_chart, use_container_width=True)

    school_count_df = (
        group_compare_df.groupby("Population", as_index=False)
        .agg(
            schools=("program_name", "nunique"),
            groups=("group_key", "nunique"),
        )
        .sort_values("Population")
    )
    st.dataframe(school_count_df, hide_index=True, use_container_width=True)


def render_learning_outcomes_tab(
    endline_dataframe: pd.DataFrame,
    baseline_dataframe: pd.DataFrame,
    comparator_mode: str,
) -> None:
    st.subheader("Learning Outcomes (Letters)")
    compare_df, comparator_label = build_population_comparison(
        endline_dataframe,
        "Program Name",
        comparator_mode,
    )
    if compare_df.empty:
        st.warning("No endline records match the selected filters.")
        return

    col_toggle, col_slider = st.columns([1, 1])
    with col_toggle:
        show_mean = st.toggle("Use mean instead of median", value=False, key="dq_outcome_mean_toggle")
    with col_slider:
        benchmark = st.slider("Benchmark threshold", min_value=20, max_value=50, value=40, step=5)
    stat_method = "mean" if show_mean else "median"
    stat_label = "Mean" if show_mean else "Median"

    summary = (
        compare_df.groupby("Population", as_index=False)
        .agg(
            learners=("response_id", "count"),
            score_stat=("Total cells correct - EGRA Letters", stat_method),
        )
        .sort_values("Population")
    )

    dataquest_score = summary.loc[summary["Population"] == "DataQuest", "score_stat"]
    comparator_score = summary.loc[summary["Population"] == comparator_label, "score_stat"]
    delta_score = (
        float(dataquest_score.iloc[0] - comparator_score.iloc[0])
        if len(dataquest_score) > 0 and len(comparator_score) > 0
        else 0.0
    )

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("DataQuest Learners", f"{len(compare_df[compare_df['Population'] == 'DataQuest']):,}")
    with metric_col2:
        st.metric(f"DataQuest {stat_label} Score", f"{dataquest_score.iloc[0]:.1f}" if len(dataquest_score) else "0.0")
    with metric_col3:
        st.metric(
            f"Gap vs {comparator_label}",
            f"{delta_score:+.1f} letters",
            delta=f"{stat_label.lower()} difference",
            delta_color="off",
        )

    if not baseline_dataframe.empty:
        baseline_compare_df, _ = build_population_comparison(
            baseline_dataframe,
            "Program Name",
            comparator_mode,
        )

        baseline_population_stat = (
            baseline_compare_df.groupby("Population", as_index=False)
            .agg(score=("Total cells correct - EGRA Letters", stat_method))
            .assign(Period="Baseline")
        )
        endline_population_stat = (
            compare_df.groupby("Population", as_index=False)
            .agg(score=("Total cells correct - EGRA Letters", stat_method))
            .assign(Period="Endline")
        )
        population_period_df = pd.concat(
            [baseline_population_stat, endline_population_stat],
            ignore_index=True,
        )
        population_period_df["Population"] = pd.Categorical(
            population_period_df["Population"],
            categories=["DataQuest", comparator_label],
            ordered=True,
        )
        population_period_df = population_period_df.sort_values(["Population", "Period"])

        baseline_endline_population_chart = px.bar(
            population_period_df,
            x="Population",
            y="score",
            color="Period",
            barmode="group",
            title=f"{stat_label} Letters: Baseline vs Endline by Cohort",
            labels={"score": f"{stat_label} Correct Letters"},
            category_orders={"Period": ["Baseline", "Endline"]},
            color_discrete_map={"Baseline": "#94a3b8", "Endline": "#2563eb"},
        )
        st.plotly_chart(baseline_endline_population_chart, use_container_width=True)

        baseline_grade_stat = (
            baseline_compare_df.groupby(["Population", "Grade"], as_index=False)
            .agg(score=("Total cells correct - EGRA Letters", stat_method))
            .assign(Period="Baseline")
        )
        endline_grade_stat = (
            compare_df.groupby(["Population", "Grade"], as_index=False)
            .agg(score=("Total cells correct - EGRA Letters", stat_method))
            .assign(Period="Endline")
        )
        grade_period_df = pd.concat([baseline_grade_stat, endline_grade_stat], ignore_index=True)
        grade_period_df["Grade"] = pd.Categorical(
            grade_period_df["Grade"],
            categories=["Grade R", "Grade 1", "Grade 2"],
            ordered=True,
        )
        grade_period_df["Population"] = pd.Categorical(
            grade_period_df["Population"],
            categories=["DataQuest", comparator_label],
            ordered=True,
        )
        grade_period_df = grade_period_df.sort_values(["Population", "Grade", "Period"])

        baseline_endline_grade_chart = px.bar(
            grade_period_df,
            x="Grade",
            y="score",
            color="Period",
            barmode="group",
            facet_col="Population",
            title=f"{stat_label} Letters by Grade: Baseline vs Endline",
            labels={"score": f"{stat_label} Correct Letters"},
            category_orders={"Period": ["Baseline", "Endline"]},
            color_discrete_map={"Baseline": "#94a3b8", "Endline": "#2563eb"},
        )
        st.plotly_chart(baseline_endline_grade_chart, use_container_width=True)
    else:
        st.warning("Baseline data is unavailable, so baseline-vs-endline charts cannot be displayed.")

    grade_stat_df = (
        compare_df.groupby(["Population", "Grade"], as_index=False)
        .agg(
            score=("Total cells correct - EGRA Letters", stat_method),
            learners=("response_id", "count"),
        )
    )
    grade_stat_df["Grade"] = pd.Categorical(
        grade_stat_df["Grade"],
        categories=["Grade R", "Grade 1", "Grade 2"],
        ordered=True,
    )
    grade_stat_df = grade_stat_df.sort_values(["Grade", "Population"])

    grade_chart = px.bar(
        grade_stat_df,
        x="Grade",
        y="score",
        color="Population",
        barmode="group",
        title=f"{stat_label} EGRA Score by Grade",
        labels={"score": f"{stat_label} Correct Letters"},
    )
    grade_chart.update_traces(
        text=[f"n={count}" for count in grade_stat_df["learners"]],
        textposition="outside",
    )
    st.plotly_chart(grade_chart, use_container_width=True)

    benchmark_df = (
        compare_df.assign(above_benchmark=compare_df["Total cells correct - EGRA Letters"] > benchmark)
        .groupby(["Population", "Grade"], as_index=False)
        .agg(
            total=("response_id", "count"),
            above=("above_benchmark", "sum"),
            zero_letters=("Total cells correct - EGRA Letters", lambda values: (values == 0).sum()),
        )
    )
    benchmark_df["pct_above"] = (benchmark_df["above"] / benchmark_df["total"] * 100).round(1)
    benchmark_df["pct_zero"] = (benchmark_df["zero_letters"] / benchmark_df["total"] * 100).round(1)

    benchmark_chart = px.bar(
        benchmark_df,
        x="Grade",
        y="pct_above",
        color="Population",
        barmode="group",
        title=f"Percent Above {benchmark} Letters by Grade",
        labels={"pct_above": "Percent Above Benchmark"},
    )
    benchmark_chart.update_traces(
        text=[f"{value:.1f}%" for value in benchmark_df["pct_above"]],
        textposition="outside",
    )
    st.plotly_chart(benchmark_chart, use_container_width=True)

    zero_chart = px.bar(
        benchmark_df,
        x="Grade",
        y="pct_zero",
        color="Population",
        barmode="group",
        title="Zero-Letter Learner Share by Grade",
        labels={"pct_zero": "Percent of Learners with Zero Letters"},
    )
    st.plotly_chart(zero_chart, use_container_width=True)

    cohort_df = compare_df[
        compare_df["cohort_session_range"].notna()
        & (compare_df["cohort_session_range"] != "")
    ].copy()
    if not cohort_df.empty:
        cohort_stat_df = (
            cohort_df.groupby(["Population", "cohort_session_range"], as_index=False)
            .agg(
                score=("Total cells correct - EGRA Letters", stat_method),
                learners=("response_id", "count"),
            )
            .rename(columns={"cohort_session_range": "Cohort"})
        )
        cohort_stat_df["Cohort"] = pd.Categorical(
            cohort_stat_df["Cohort"],
            categories=COHORT_ORDER,
            ordered=True,
        )
        cohort_stat_df = cohort_stat_df.sort_values(["Cohort", "Population"])

        cohort_chart = px.bar(
            cohort_stat_df,
            x="Cohort",
            y="score",
            color="Population",
            barmode="group",
            title=f"{stat_label} EGRA Score by Session Cohort",
            labels={"score": f"{stat_label} Correct Letters"},
        )
        cohort_chart.update_traces(
            text=[f"n={count}" for count in cohort_stat_df["learners"]],
            textposition="outside",
        )
        st.plotly_chart(cohort_chart, use_container_width=True)

    st.dataframe(
        benchmark_df.sort_values(["Grade", "Population"]),
        hide_index=True,
        use_container_width=True,
    )


def render_child_dosage_tab(
    child_dosage_dataframe: pd.DataFrame,
    endline_dataframe: pd.DataFrame,
    baseline_dataframe: pd.DataFrame,
    comparator_mode: str,
) -> None:
    st.subheader("Learner Dosage (Child Level)")
    compare_df, comparator_label = build_population_comparison(
        child_dosage_dataframe,
        "school_name",
        comparator_mode,
    )
    if compare_df.empty:
        st.warning("No child dosage records match the selected filters.")
        return

    summary_df = (
        compare_df.groupby("Population", as_index=False)
        .agg(
            learners=("participant_id", "nunique"),
            avg_sessions=("total_sessions", "mean"),
            median_sessions=("total_sessions", "median"),
            avg_weekly=("avg_sessions_per_week", "mean"),
            median_weekly=("avg_sessions_per_week", "median"),
            pct_2_plus_weekly=("avg_sessions_per_week", lambda values: (values >= 2).mean() * 100),
            pct_3_plus_weekly=("avg_sessions_per_week", lambda values: (values >= 3).mean() * 100),
        )
        .round(2)
    )
    st.dataframe(summary_df, hide_index=True, use_container_width=True)

    histogram_chart = px.histogram(
        compare_df,
        x="total_sessions",
        color="Population",
        barmode="overlay",
        opacity=0.6,
        title="Distribution of Sessions per Learner",
        labels={"total_sessions": "Total Sessions"},
    )
    st.plotly_chart(histogram_chart, use_container_width=True)

    weekly_box = px.box(
        compare_df,
        x="Population",
        y="avg_sessions_per_week",
        color="Population",
        title="Average Sessions per Week by Population",
        labels={"avg_sessions_per_week": "Average Sessions per Week"},
    )
    st.plotly_chart(weekly_box, use_container_width=True)

    bands_df = compare_df.copy()
    bands_df["Band"] = pd.cut(
        bands_df["total_sessions"],
        bins=[-1, 5, 15, 30, 10_000],
        labels=["0-5", "6-15", "16-30", "31+"],
    )
    bands_df = bands_df[bands_df["Band"].notna()].copy()
    band_summary = (
        bands_df.groupby(["Population", "Band"], observed=True)
        .agg(learners=("participant_id", "nunique"))
        .reset_index()
    )
    population_totals = band_summary.groupby("Population", as_index=False).agg(total=("learners", "sum"))
    band_summary = band_summary.merge(population_totals, on="Population", how="left")
    band_summary["pct"] = (band_summary["learners"] / band_summary["total"] * 100).round(1)

    band_chart = px.bar(
        band_summary,
        x="Band",
        y="pct",
        color="Population",
        barmode="group",
        title="Learner Session Intensity Bands",
        labels={"pct": "Percent of Learners"},
    )
    band_chart.update_traces(text=[f"{value:.1f}%" for value in band_summary["pct"]], textposition="outside")
    st.plotly_chart(band_chart, use_container_width=True)

    dataquest_avg = summary_df.loc[summary_df["Population"] == "DataQuest", "avg_sessions"]
    comparator_avg = summary_df.loc[summary_df["Population"] == comparator_label, "avg_sessions"]
    if len(dataquest_avg) and len(comparator_avg):
        st.info(
            "DataQuest learners average "
            f"{dataquest_avg.iloc[0]:.2f} sessions versus {comparator_avg.iloc[0]:.2f} in {comparator_label}."
        )

    render_cohort_performance_reference_chart(
        endline_dataframe=endline_dataframe,
        baseline_dataframe=baseline_dataframe,
        comparator_mode=comparator_mode,
        key_prefix="learner_dosage",
    )


def render_school_grade_improvement_dosage_analysis(
    endline_dataframe: pd.DataFrame,
    baseline_dataframe: pd.DataFrame,
    comparator_mode: str,
    key_prefix: str,
) -> None:
    st.divider()
    st.markdown("### School + Grade Improvement and Dosage")
    st.caption(
        "School-grade unit analysis only (no learner name matching). Improvement is calculated "
        "as baseline-to-endline score change for each school-grade unit."
    )
    st.info(
        "Interpretation tip: the cohort and dosage charts in this section use school-grade units, "
        "not individual learners. In the correlation chart, each point is one school-grade unit; "
        "larger points mean more learners in that unit."
    )
    st.info(
        "Read the charts in sequence: coverage -> cohort improvement -> dosage bands -> correlation. "
        "If higher-dosage cohorts also show higher improvement and positive correlation, that supports "
        "a dosage-improvement relationship at school-grade level."
    )

    if endline_dataframe.empty or baseline_dataframe.empty:
        st.warning("Baseline or endline data is unavailable for school-grade analysis.")
        return

    compare_endline_df, _ = build_population_comparison(
        endline_dataframe,
        "Program Name",
        comparator_mode,
    )
    compare_baseline_df, _ = build_population_comparison(
        baseline_dataframe,
        "Program Name",
        comparator_mode,
    )

    compare_endline_df = compare_endline_df[compare_endline_df["Grade"].notna()].copy()
    compare_baseline_df = compare_baseline_df[compare_baseline_df["Grade"].notna()].copy()
    if compare_endline_df.empty or compare_baseline_df.empty:
        st.warning("No school-grade records available after filtering.")
        return

    endline_score_column_name = (
        "Total cells correct - EGRA Letters"
        if "Total cells correct - EGRA Letters" in compare_endline_df.columns
        else "Endline Score"
    )
    baseline_score_column_name = (
        "Total cells correct - EGRA Letters"
        if "Total cells correct - EGRA Letters" in compare_baseline_df.columns
        else "Baseline Score"
    )
    required_endline_columns = {
        "Program Name",
        "Grade",
        "session_count_total",
        "cohort_session_range",
        endline_score_column_name,
    }
    required_baseline_columns = {"Program Name", "Grade", baseline_score_column_name}
    if not required_endline_columns.issubset(compare_endline_df.columns):
        st.error(
            "Endline school-grade analysis is missing required columns: "
            f"{sorted(required_endline_columns - set(compare_endline_df.columns))}"
        )
        return
    if not required_baseline_columns.issubset(compare_baseline_df.columns):
        st.error(
            "Baseline school-grade analysis is missing required columns: "
            f"{sorted(required_baseline_columns - set(compare_baseline_df.columns))}"
        )
        return

    stat_col_left, stat_col_right = st.columns([1, 3])
    with stat_col_left:
        use_mean = st.toggle(
            "Use Mean",
            value=False,
            key=f"{key_prefix}_stat_toggle",
        )
    stat_method = "mean" if use_mean else "median"
    stat_label = "Mean" if use_mean else "Median"

    endline_units_df = (
        compare_endline_df.groupby(["Population", "Program Name", "Grade"], as_index=False)
        .agg(
            endline_learners=(endline_score_column_name, "count"),
            endline_score=(endline_score_column_name, stat_method),
            dosage_score=("session_count_total", stat_method),
            cohort_mode=(
                "cohort_session_range",
                lambda values: values.mode().iloc[0]
                if len(values.mode()) > 0
                else "",
            ),
        )
        .round(2)
    )
    baseline_units_df = (
        compare_baseline_df.groupby(["Population", "Program Name", "Grade"], as_index=False)
        .agg(
            baseline_learners=(baseline_score_column_name, "count"),
            baseline_score=(baseline_score_column_name, stat_method),
        )
        .round(2)
    )

    school_grade_df = endline_units_df.merge(
        baseline_units_df,
        on=["Population", "Program Name", "Grade"],
        how="inner",
    )
    if school_grade_df.empty:
        st.warning("No overlapping school-grade units found between baseline and endline.")
        return
    school_grade_df["improvement_score"] = (
        school_grade_df["endline_score"] - school_grade_df["baseline_score"]
    ).round(2)
    school_grade_df["School Grade"] = school_grade_df["Program Name"] + " | " + school_grade_df["Grade"].astype(str)

    coverage_df = (
        endline_units_df.groupby("Population", as_index=False)
        .agg(endline_school_grade_units=("Program Name", "count"))
        .merge(
            school_grade_df.groupby("Population", as_index=False).agg(
                overlapping_units=("Program Name", "count")
            ),
            on="Population",
            how="left",
        )
    )
    coverage_df["overlapping_units"] = coverage_df["overlapping_units"].fillna(0).astype(int)
    coverage_df["unit_overlap_pct"] = (
        coverage_df["overlapping_units"] / coverage_df["endline_school_grade_units"].clip(lower=1) * 100
    ).round(1)
    st.dataframe(coverage_df, hide_index=True, use_container_width=True)

    metric_col1, metric_col2, metric_col3 = st.columns(3)
    with metric_col1:
        st.metric("School-Grade Units", f"{len(school_grade_df):,}")
    with metric_col2:
        st.metric(
            f"{stat_label} Improvement (All Units)",
            f"{school_grade_df['improvement_score'].median():+.1f} letters",
        )
    with metric_col3:
        st.metric(
            f"{stat_label} Dosage (All Units)",
            f"{school_grade_df['dosage_score'].median():.1f} sessions",
        )

    cohort_units_df = school_grade_df[
        school_grade_df["cohort_mode"].notna()
        & (school_grade_df["cohort_mode"] != "")
    ].copy()
    if not cohort_units_df.empty:
        cohort_summary_df = (
            cohort_units_df.groupby(["Population", "cohort_mode"], as_index=False)
            .agg(
                improvement=("improvement_score", stat_method),
                school_grade_units=("School Grade", "count"),
            )
            .rename(columns={"cohort_mode": "Cohort"})
        )
        cohort_summary_df["Cohort"] = pd.Categorical(
            cohort_summary_df["Cohort"],
            categories=COHORT_ORDER,
            ordered=True,
        )
        cohort_summary_df = cohort_summary_df.sort_values(["Cohort", "Population"])

        cohort_chart = px.bar(
            cohort_summary_df,
            x="Cohort",
            y="improvement",
            color="Population",
            barmode="group",
            title=f"{stat_label} School-Grade Improvement by Cohort",
            labels={"improvement": f"{stat_label} Improvement (Letters)"},
        )
        cohort_chart.update_traces(
            text=[f"units={count}" for count in cohort_summary_df["school_grade_units"]],
            textposition="outside",
        )
        cohort_chart.add_hline(y=0, line_dash="dash", line_color="#475569")
        st.plotly_chart(
            cohort_chart,
            use_container_width=True,
            key=f"{key_prefix}_cohort_chart",
        )

    school_grade_df["Dosage Band"] = school_grade_df["dosage_score"].apply(classify_group_session_band)
    dosage_band_df = (
        school_grade_df.groupby(["Population", "Dosage Band"], as_index=False)
        .agg(school_grade_units=("School Grade", "count"))
    )
    dosage_band_df["Dosage Band"] = pd.Categorical(
        dosage_band_df["Dosage Band"],
        categories=COHORT_ORDER,
        ordered=True,
    )
    dosage_band_df = dosage_band_df.sort_values(["Dosage Band", "Population"])

    dosage_band_chart = px.bar(
        dosage_band_df,
        x="Dosage Band",
        y="school_grade_units",
        color="Population",
        barmode="group",
        title="School-Grade Unit Distribution by Dosage Band",
        labels={"school_grade_units": "Number of School-Grade Units"},
    )
    st.plotly_chart(
        dosage_band_chart,
        use_container_width=True,
        key=f"{key_prefix}_dosage_band_chart",
    )

    correlation_rows: list[dict] = []
    for population_name, population_df in school_grade_df.groupby("Population"):
        correlation_value = (
            population_df["dosage_score"].corr(population_df["improvement_score"])
            if population_df["dosage_score"].nunique() > 1
            and population_df["improvement_score"].nunique() > 1
            else pd.NA
        )
        correlation_rows.append({"Population": population_name, "correlation": correlation_value})
    correlation_df = pd.DataFrame(correlation_rows)
    correlation_df["correlation"] = pd.to_numeric(correlation_df["correlation"], errors="coerce").round(3)

    correlation_chart = px.scatter(
        school_grade_df,
        x="dosage_score",
        y="improvement_score",
        color="Population",
        size="endline_learners",
        hover_data=["Program Name", "Grade", "endline_learners", "baseline_learners", "cohort_mode"],
        title="Correlation View: Improvement vs Dosage (School-Grade Units)",
        labels={
            "dosage_score": f"{stat_label} Dosage (Sessions)",
            "improvement_score": f"{stat_label} Improvement (Letters)",
            "cohort_mode": "Dominant Cohort",
        },
    )
    population_line_colors = {
        "DataQuest": "#1d4ed8",
        "Non-DataQuest": "#7dd3fc",
        "Overall": "#111827",
    }
    for population_name, population_df in school_grade_df.groupby("Population"):
        population_trend = build_safe_linear_trend(
            population_df["dosage_score"],
            population_df["improvement_score"],
        )
        if population_trend is None:
            continue
        x_line_values, y_line_values = population_trend
        correlation_chart.add_trace(
            go.Scatter(
                x=x_line_values,
                y=y_line_values,
                mode="lines",
                name=f"{population_name} Trend",
                line={
                    "color": population_line_colors.get(population_name, "#111827"),
                    "width": 2,
                    "dash": "dash",
                },
                hovertemplate="Dosage: %{x:.2f}<br>Trend Improvement: %{y:.2f}<extra></extra>",
            )
        )
    correlation_chart.add_hline(y=0, line_dash="dash", line_color="#475569")
    st.plotly_chart(
        correlation_chart,
        use_container_width=True,
        key=f"{key_prefix}_correlation_chart",
    )
    st.dataframe(correlation_df, hide_index=True, use_container_width=True)

    detail_columns = [
        "Population",
        "Program Name",
        "Grade",
        "baseline_learners",
        "endline_learners",
        "baseline_score",
        "endline_score",
        "improvement_score",
        "dosage_score",
        "cohort_mode",
    ]
    detail_df = school_grade_df[detail_columns].rename(
        columns={
            "Program Name": "School",
            "Grade": "Grade",
            "baseline_learners": "Baseline Learners",
            "endline_learners": "Endline Learners",
            "baseline_score": f"Baseline ({stat_label})",
            "endline_score": f"Endline ({stat_label})",
            "improvement_score": f"Improvement ({stat_label})",
            "dosage_score": f"Dosage ({stat_label})",
            "cohort_mode": "Dominant Cohort",
        }
    )
    detail_df = detail_df.sort_values(["Population", f"Improvement ({stat_label})"], ascending=[True, False])
    st.dataframe(detail_df, hide_index=True, use_container_width=True, height=420)


def render_starting_level_vs_dosage_tab(
    endline_dataframe: pd.DataFrame,
    baseline_dataframe: pd.DataFrame,
    comparator_mode: str,
) -> None:
    st.subheader("Starting Level vs Dosage")
    st.info(
        "This tab helps test whether lower-starting school-grade units received higher dosage, "
        "and whether improvement patterns differ by both starting level and dosage."
    )

    if endline_dataframe.empty or baseline_dataframe.empty:
        st.warning("Baseline or endline data is unavailable for this analysis.")
        return

    compare_endline_df, _ = build_population_comparison(
        endline_dataframe,
        "Program Name",
        comparator_mode,
    )
    compare_baseline_df, _ = build_population_comparison(
        baseline_dataframe,
        "Program Name",
        comparator_mode,
    )

    compare_endline_df = compare_endline_df[compare_endline_df["Grade"].notna()].copy()
    compare_baseline_df = compare_baseline_df[compare_baseline_df["Grade"].notna()].copy()
    if compare_endline_df.empty or compare_baseline_df.empty:
        st.warning("No school-grade records available after filters.")
        return

    endline_score_column_name = (
        "Total cells correct - EGRA Letters"
        if "Total cells correct - EGRA Letters" in compare_endline_df.columns
        else "Endline Score"
    )
    baseline_score_column_name = (
        "Total cells correct - EGRA Letters"
        if "Total cells correct - EGRA Letters" in compare_baseline_df.columns
        else "Baseline Score"
    )
    required_endline_columns = {
        "Program Name",
        "Grade",
        "session_count_total",
        endline_score_column_name,
    }
    required_baseline_columns = {"Program Name", "Grade", baseline_score_column_name}
    if not required_endline_columns.issubset(compare_endline_df.columns):
        st.error(
            "Endline analysis is missing required columns: "
            f"{sorted(required_endline_columns - set(compare_endline_df.columns))}"
        )
        return
    if not required_baseline_columns.issubset(compare_baseline_df.columns):
        st.error(
            "Baseline analysis is missing required columns: "
            f"{sorted(required_baseline_columns - set(compare_baseline_df.columns))}"
        )
        return

    stat_col_left, stat_col_right = st.columns([1, 3])
    with stat_col_left:
        use_mean = st.toggle(
            "Use Mean",
            value=False,
            key="starting_level_stat_toggle",
        )
    with stat_col_right:
        baseline_band_method = st.radio(
            "Baseline banding method",
            options=["Quintiles", "Fixed bands"],
            index=0,
            horizontal=True,
            key="starting_level_band_method",
        )
    stat_method = "mean" if use_mean else "median"
    stat_label = "Mean" if use_mean else "Median"

    endline_units_df = (
        compare_endline_df.groupby(["Population", "Program Name", "Grade"], as_index=False)
        .agg(
            endline_learners=(endline_score_column_name, "count"),
            endline_score=(endline_score_column_name, stat_method),
            dosage_score=("session_count_total", stat_method),
        )
        .round(2)
    )
    baseline_units_df = (
        compare_baseline_df.groupby(["Population", "Program Name", "Grade"], as_index=False)
        .agg(
            baseline_learners=(baseline_score_column_name, "count"),
            baseline_score=(baseline_score_column_name, stat_method),
        )
        .round(2)
    )
    school_grade_df = endline_units_df.merge(
        baseline_units_df,
        on=["Population", "Program Name", "Grade"],
        how="inner",
    )
    if school_grade_df.empty:
        st.warning("No overlapping school-grade units found between baseline and endline.")
        return
    school_grade_df["improvement_score"] = (
        school_grade_df["endline_score"] - school_grade_df["baseline_score"]
    ).round(2)
    school_grade_df["dosage_band"] = school_grade_df["dosage_score"].apply(classify_group_session_band)

    if baseline_band_method == "Quintiles":
        school_grade_df["baseline_band"] = pd.qcut(
            school_grade_df["baseline_score"],
            q=5,
            duplicates="drop",
        ).astype(str)
    else:
        baseline_band_bins = [-1, 5, 10, 20, 30, 1000]
        baseline_band_labels = ["0-5", "6-10", "11-20", "21-30", "31+"]
        school_grade_df["baseline_band"] = pd.cut(
            school_grade_df["baseline_score"],
            bins=baseline_band_bins,
            labels=baseline_band_labels,
            include_lowest=True,
        ).astype(str)

    # 1) Baseline distribution by dosage band
    st.info(
        "Chart 1 - Baseline by Dosage Band: If lower baseline medians cluster in higher dosage bands, "
        "that suggests lower-starting units were prioritized for more sessions."
    )
    baseline_distribution_chart = px.box(
        school_grade_df,
        x="dosage_band",
        y="baseline_score",
        color="Population",
        category_orders={"dosage_band": COHORT_ORDER},
        title=f"{stat_label} Baseline Score by Dosage Band (School-Grade Units)",
        labels={
            "dosage_band": "Dosage Band",
            "baseline_score": f"{stat_label} Baseline Score",
        },
    )
    st.plotly_chart(
        baseline_distribution_chart,
        use_container_width=True,
        key="starting_level_baseline_distribution_chart",
    )

    # 2) Interaction heatmap with value toggle
    heatmap_col_left, heatmap_col_right = st.columns([1, 3])
    with heatmap_col_left:
        heatmap_value = st.radio(
            "Heatmap value",
            options=["Median improvement", "Unit count"],
            index=0,
            key="starting_level_heatmap_value",
        )

    interaction_df = (
        school_grade_df.groupby(["Population", "baseline_band", "dosage_band"], as_index=False)
        .agg(
            units=("Program Name", "count"),
            baseline_score=("baseline_score", stat_method),
            dosage_score=("dosage_score", stat_method),
            improvement_score=("improvement_score", stat_method),
        )
    )
    st.info(
        "Chart 2 - Baseline x Dosage Heatmap: Rows are starting-level bands and columns are dosage bands. "
        "For `Median improvement`, darker cells mean higher gains. For `Unit count`, darker cells mean more units. "
        "Blank cells mean no units in that combination."
    )
    interaction_df["dosage_band"] = pd.Categorical(
        interaction_df["dosage_band"],
        categories=COHORT_ORDER,
        ordered=True,
    )
    interaction_df = interaction_df.sort_values(["Population", "baseline_band", "dosage_band"])

    for population_name in sorted(interaction_df["Population"].dropna().unique()):
        population_interaction_df = interaction_df[interaction_df["Population"] == population_name].copy()
        if population_interaction_df.empty:
            continue

        value_column_name = "improvement_score" if heatmap_value == "Median improvement" else "units"
        value_title = (
            f"{stat_label} Improvement (Letters)"
            if heatmap_value == "Median improvement"
            else "School-Grade Unit Count"
        )
        heatmap_matrix_df = population_interaction_df.pivot(
            index="baseline_band",
            columns="dosage_band",
            values=value_column_name,
        )
        if heatmap_value == "Unit count":
            heatmap_matrix_df = heatmap_matrix_df.fillna(0)
        if heatmap_matrix_df.empty:
            continue

        heatmap_chart = px.imshow(
            heatmap_matrix_df,
            text_auto=".1f" if heatmap_value == "Median improvement" else "d",
            aspect="auto",
            title=f"{population_name}: Baseline Band x Dosage Band ({value_title})",
            labels={
                "x": "Dosage Band",
                "y": "Baseline Band",
                "color": value_title,
            },
            color_continuous_scale="Blues",
        )
        st.plotly_chart(
            heatmap_chart,
            use_container_width=True,
            key=f"starting_level_heatmap_{population_name}_{heatmap_value.replace(' ', '_')}",
        )

    # 3) Faceted scatter with per-facet trend lines
    st.info(
        "Chart 3 - Improvement vs Dosage Scatter: Each point is a school-grade unit; larger points have more learners. "
        "A positive dashed trend within a population indicates higher dosage is generally associated with higher improvement."
    )
    scatter_chart = px.scatter(
        school_grade_df,
        x="dosage_score",
        y="improvement_score",
        color="baseline_band",
        size="endline_learners",
        facet_col="Population",
        hover_data=["Program Name", "Grade", "baseline_score", "endline_score", "endline_learners"],
        title="Improvement vs Dosage by Baseline Band (School-Grade Units)",
        labels={
            "dosage_score": f"{stat_label} Dosage (Sessions)",
            "improvement_score": f"{stat_label} Improvement (Letters)",
            "baseline_band": "Baseline Band",
        },
    )

    population_names = sorted(school_grade_df["Population"].dropna().unique())
    for population_name in population_names:
        population_scatter_df = school_grade_df[school_grade_df["Population"] == population_name]
        population_trend = build_safe_linear_trend(
            population_scatter_df["dosage_score"],
            population_scatter_df["improvement_score"],
        )
        if population_trend is not None:
            x_line_values, y_line_values = population_trend
            facet_col_position = (
                1
                if population_name == population_names[0]
                else 2
            )
            scatter_chart.add_trace(
                go.Scatter(
                    x=x_line_values,
                    y=y_line_values,
                    mode="lines",
                    name=f"{population_name} Trend",
                    line={"color": "#111827", "width": 2, "dash": "dash"},
                    showlegend=False,
                    hovertemplate="Dosage: %{x:.2f}<br>Trend Improvement: %{y:.2f}<extra></extra>",
                ),
                row=1,
                col=facet_col_position,
            )
    scatter_chart.add_hline(y=0, line_dash="dash", line_color="#475569")
    st.plotly_chart(
        scatter_chart,
        use_container_width=True,
        key="starting_level_scatter_chart",
    )

    # 4) Summary table with sparse-cell warning
    st.info(
        "Table - Baseline x Dosage Summary: Use this as the source-of-truth for cell values and sample sizes. "
        "Prioritize patterns with larger unit counts and treat sparse cells as directional."
    )
    summary_df = interaction_df.rename(
        columns={
            "Population": "Population",
            "baseline_band": "Baseline Band",
            "dosage_band": "Dosage Band",
            "units": "School-Grade Units",
            "baseline_score": f"Baseline ({stat_label})",
            "dosage_score": f"Dosage ({stat_label})",
            "improvement_score": f"Improvement ({stat_label})",
        }
    )
    summary_df["Sparse Cell"] = summary_df["School-Grade Units"] < 8
    st.dataframe(summary_df, hide_index=True, use_container_width=True, height=430)
    sparse_cell_count = int(summary_df["Sparse Cell"].sum())
    if sparse_cell_count > 0:
        st.warning(
            f"{sparse_cell_count} baseline x dosage cells have fewer than 8 school-grade units. "
            "Treat those patterns as directional only."
        )
    st.info(
        "Interpretation guide: if lower baseline bands consistently sit in higher dosage bands "
        "and also show larger improvement medians, that supports the hypothesis that lower-starting "
        "units received more dosage and improved more."
    )


def render_group_dosage_tab(
    group_dosage_dataframe: pd.DataFrame,
    endline_dataframe: pd.DataFrame,
    baseline_dataframe: pd.DataFrame,
    comparator_mode: str,
) -> None:
    st.subheader("Group Dosage (Class Level)")
    compare_df, _ = build_population_comparison(
        group_dosage_dataframe,
        "program_name",
        comparator_mode,
    )
    compare_df = compare_df[
        compare_df["class_name"].notna()
        & (compare_df["class_name"].astype(str).str.strip() != "")
    ].copy()
    if compare_df.empty:
        st.warning("No group dosage records match the selected filters.")
        return

    summary_df = (
        compare_df.groupby("Population", as_index=False)
        .agg(
            groups=("group_key", "nunique"),
            schools=("program_name", "nunique"),
            total_sessions=("total_sessions", "sum"),
            avg_sessions_per_group=("total_sessions", "mean"),
            median_sessions_per_group=("total_sessions", "median"),
            median_sessions_per_active_day=("sessions_per_active_day", "median"),
            median_sessions_per_active_week=("sessions_per_active_week", "median"),
        )
        .round(2)
    )
    st.dataframe(summary_df, hide_index=True, use_container_width=True)

    compare_df["Session Band"] = compare_df["total_sessions"].apply(classify_group_session_band)
    band_summary = (
        compare_df.groupby(["Population", "Session Band"], as_index=False)
        .agg(groups=("group_key", "nunique"))
    )
    band_summary["Session Band"] = pd.Categorical(
        band_summary["Session Band"],
        categories=COHORT_ORDER,
        ordered=True,
    )
    band_summary = band_summary.sort_values(["Session Band", "Population"])

    band_chart = px.bar(
        band_summary,
        x="Session Band",
        y="groups",
        color="Population",
        barmode="group",
        title="Groups by Total Session Band",
        labels={"groups": "Number of Groups"},
    )
    st.plotly_chart(band_chart, use_container_width=True)

    day_week_chart = px.box(
        compare_df,
        x="Population",
        y="sessions_per_active_week",
        color="Population",
        title="Sessions per Active Week by Group",
        labels={"sessions_per_active_week": "Sessions per Active Week"},
    )
    st.plotly_chart(day_week_chart, use_container_width=True)

    school_table = (
        compare_df.groupby(["Population", "program_name"], as_index=False)
        .agg(
            groups=("group_key", "nunique"),
            total_sessions=("total_sessions", "sum"),
            median_sessions_per_group=("total_sessions", "median"),
            median_sessions_per_day=("sessions_per_active_day", "median"),
            median_sessions_per_week=("sessions_per_active_week", "median"),
            unique_eas=("unique_eas", "sum"),
        )
        .rename(columns={"program_name": "School"})
        .sort_values(["Population", "median_sessions_per_week"], ascending=[True, False])
    )
    st.dataframe(school_table, hide_index=True, use_container_width=True, height=420)

    render_school_grade_improvement_dosage_analysis(
        endline_dataframe=endline_dataframe,
        baseline_dataframe=baseline_dataframe,
        comparator_mode=comparator_mode,
        key_prefix="group_dosage_school_grade",
    )

    render_cohort_performance_reference_chart(
        endline_dataframe=endline_dataframe,
        baseline_dataframe=baseline_dataframe,
        comparator_mode=comparator_mode,
        key_prefix="group_dosage",
    )


def render_learning_content_tab(
    content_dataframe: pd.DataFrame,
    comparator_mode: str,
) -> None:
    st.subheader("What Learners Were Taught")
    compare_df, _ = build_population_comparison(
        content_dataframe,
        "program_name",
        comparator_mode,
    )
    if compare_df.empty:
        st.warning("No session content records match the selected filters.")
        return

    summary_df = (
        compare_df.groupby("Population", as_index=False)
        .agg(
            sessions=("session_id", "nunique"),
            sessions_with_letters=("has_letters_taught", "sum"),
            avg_num_letters=("num_letters_taught", "mean"),
            median_num_letters=("num_letters_taught", "median"),
        )
        .round(2)
    )
    summary_df["pct_sessions_with_letters"] = (
        summary_df["sessions_with_letters"] / summary_df["sessions"] * 100
    ).round(1)
    st.dataframe(summary_df, hide_index=True, use_container_width=True)

    letters_coverage_chart = px.bar(
        summary_df,
        x="Population",
        y="pct_sessions_with_letters",
        color="Population",
        title="Sessions with Recorded Letters Taught",
        labels={"pct_sessions_with_letters": "Percent of Sessions"},
    )
    letters_coverage_chart.update_traces(
        text=[f"{value:.1f}%" for value in summary_df["pct_sessions_with_letters"]],
        textposition="outside",
    )
    st.plotly_chart(letters_coverage_chart, use_container_width=True)

    avg_letters_chart = px.bar(
        summary_df,
        x="Population",
        y="avg_num_letters",
        color="Population",
        title="Average Number of Letters Taught per Session",
        labels={"avg_num_letters": "Average Letters per Session"},
    )
    st.plotly_chart(avg_letters_chart, use_container_width=True)

    token_df = explode_letters(compare_df[compare_df["has_letters_taught"]].copy())
    if token_df.empty:
        st.info("No `letters_taught` values are available after applying the current filters.")
        return

    top_letters = (
        token_df.groupby(["Population", "Letter"], as_index=False)
        .size()
        .rename(columns={"size": "mentions"})
        .sort_values("mentions", ascending=False)
    )
    top_letters = (
        top_letters.groupby("Population", group_keys=False)
        .head(12)
        .sort_values(["Population", "mentions"], ascending=[True, False])
    )
    letters_chart = px.bar(
        top_letters,
        x="Letter",
        y="mentions",
        color="Population",
        barmode="group",
        title="Most Frequently Taught Letters (Top 12 per Population)",
        labels={"mentions": "Session Mentions"},
    )
    st.plotly_chart(letters_chart, use_container_width=True)
    st.dataframe(top_letters, hide_index=True, use_container_width=True)


@st.cache_data(ttl=3600)
def _analyse_quality_flags(dq_sessions: pd.DataFrame) -> pd.DataFrame:
    """Analyse DataQuest sessions for Moving-Too-Fast and Same-Letter-Groups flags.

    Moving Too Fast: an EA+school+group is flagged when >70% of consecutive session
    transitions introduce only new letters with no overlap (no review).

    Same Letter Groups: an EA+school is flagged when 3+ groups share the same
    highest-letter progress index in their most recent session.
    """
    df = dq_sessions.copy()

    # Deduplicate to one row per session
    df_unique = df.sort_values("session_started_at").drop_duplicates(
        subset=["session_id"], keep="last"
    )
    df_unique = df_unique[
        df_unique["letters_taught"].notna()
        & (df_unique["letters_taught"].astype(str).str.strip() != "")
    ].copy()
    if df_unique.empty:
        return pd.DataFrame()

    # --- Moving Too Fast (per EA + school + group) ---
    mtf_flagged_rows: list[dict] = []
    min_sessions = 3

    for (school, ea, group), grp in df_unique.groupby(
        ["program_name", "user_name", "class_name"]
    ):
        grp = grp.sort_values("session_started_at")
        if len(grp) < min_sessions:
            continue

        letters_per_session: list[set[str]] = []
        for letters_str in grp["letters_taught"]:
            tokens = {t.strip().lower() for t in str(letters_str).split(",") if t.strip()}
            letters_per_session.append(tokens)

        no_review = sum(
            1
            for i in range(1, len(letters_per_session))
            if not (letters_per_session[i] & letters_per_session[i - 1])
        )
        total_transitions = len(letters_per_session) - 1
        if total_transitions >= (min_sessions - 1) and no_review / total_transitions > 0.7:
            mtf_flagged_rows.append({"school": school, "ea": ea, "group": group})

    mtf_by_school = (
        pd.DataFrame(mtf_flagged_rows)
        .groupby("school", as_index=False)
        .agg(moving_too_fast_groups=("group", "count"))
        if mtf_flagged_rows
        else pd.DataFrame(columns=["school", "moving_too_fast_groups"])
    )

    # --- Same Letter Groups (per EA + school) ---
    # Find highest letter index per group's most recent session
    latest_idx = df_unique.groupby(
        ["program_name", "user_name", "class_name"]
    )["session_started_at"].idxmax()
    latest_sessions = df_unique.loc[latest_idx].copy()

    def _highest_letter_index(letters_str: str) -> int:
        tokens = [t.strip().lower() for t in str(letters_str).split(",") if t.strip()]
        max_idx = -1
        for token in tokens:
            if token in LETTER_SEQUENCE:
                max_idx = max(max_idx, LETTER_SEQUENCE.index(token))
        return max_idx

    latest_sessions["progress_index"] = latest_sessions["letters_taught"].apply(
        _highest_letter_index
    )

    slg_flagged_rows: list[dict] = []
    for (school, ea), ea_grp in latest_sessions.groupby(["program_name", "user_name"]):
        counts = Counter(ea_grp["progress_index"])
        if any(c >= 3 for c in counts.values()):
            slg_flagged_rows.append({"school": school, "ea": ea})

    slg_by_school = (
        pd.DataFrame(slg_flagged_rows)
        .groupby("school", as_index=False)
        .agg(same_letter_groups_eas=("ea", "count"))
        if slg_flagged_rows
        else pd.DataFrame(columns=["school", "same_letter_groups_eas"])
    )

    # --- Combine per school ---
    all_schools = pd.DataFrame(
        {"school": sorted(df_unique["program_name"].unique())}
    )
    result = all_schools.merge(mtf_by_school, on="school", how="left").merge(
        slg_by_school, on="school", how="left"
    )
    result["moving_too_fast_groups"] = result["moving_too_fast_groups"].fillna(0).astype(int)
    result["same_letter_groups_eas"] = result["same_letter_groups_eas"].fillna(0).astype(int)

    # Count total groups and EAs per school for context
    total_groups = (
        df_unique.groupby("program_name", as_index=False)
        .agg(total_groups=("class_name", "nunique"), total_eas=("user_name", "nunique"))
        .rename(columns={"program_name": "school"})
    )
    result = result.merge(total_groups, on="school", how="left")
    result = result.rename(columns={"school": "School", "total_groups": "Total Groups", "total_eas": "Total EAs"})
    return result


def render_school_dosage_tab(
    sessions_dataframe: pd.DataFrame,
    endline_dataframe: pd.DataFrame,
    comparator_mode: str,
) -> None:
    st.subheader("School Dosage")
    st.info("Charts on this tab are **not affected** by the Grade or 11+ session filters above. They show all sessions across all grades.")

    if sessions_dataframe.empty:
        st.warning("No session data available.")
        return

    compare_df, comparator_label = build_population_comparison(
        sessions_dataframe,
        "program_name",
        comparator_mode,
    )

    school_summary = compare_df.groupby(
        ["program_name", "Population"], as_index=False
    ).agg(
        Total_Sessions=("session_id", "nunique"),
        first_session=("session_started_at", "min"),
        last_session=("session_started_at", "max"),
    )
    date_range_days = (
        (school_summary["last_session"] - school_summary["first_session"]).dt.days + 1
    ).clip(lower=1)
    school_summary["Avg_Sessions_Per_Day"] = (
        school_summary["Total_Sessions"] / date_range_days
    ).round(2)

    # --- DataQuest Only: Total Sessions by School ---
    dq_only = school_summary[is_dataquest_school(school_summary["program_name"])].copy()

    dq_sorted_total = dq_only.sort_values("Total_Sessions", ascending=True)
    fig_dq_total = px.bar(
        dq_sorted_total,
        x="program_name",
        y="Total_Sessions",
        title="Total Sessions by School (DataQuest Only)",
        labels={"program_name": "School", "Total_Sessions": "Total Sessions"},
        category_orders={
            "program_name": dq_sorted_total["program_name"].tolist(),
        },
    )
    fig_dq_total.update_layout(
        xaxis_tickangle=-45,
        showlegend=False,
    )
    st.plotly_chart(fig_dq_total, use_container_width=True)

    # --- DataQuest Only: Average Sessions per Day by School ---
    dq_sorted_avg = dq_only.sort_values("Avg_Sessions_Per_Day", ascending=True)
    fig_dq_avg = px.bar(
        dq_sorted_avg,
        x="program_name",
        y="Avg_Sessions_Per_Day",
        title="Average Sessions per Day by School (DataQuest Only)",
        labels={"program_name": "School", "Avg_Sessions_Per_Day": "Avg Sessions Per Day"},
        category_orders={
            "program_name": dq_sorted_avg["program_name"].tolist(),
        },
    )
    fig_dq_avg.update_layout(
        xaxis_tickangle=-45,
        showlegend=False,
    )
    st.plotly_chart(fig_dq_avg, use_container_width=True)

    st.divider()

    # --- Total Sessions by School ---
    sorted_total = school_summary.sort_values("Total_Sessions", ascending=True)
    fig_total = px.bar(
        sorted_total,
        x="program_name",
        y="Total_Sessions",
        color="Population",
        title="Total Sessions by School",
        labels={"program_name": "School", "Total_Sessions": "Total Sessions"},
        category_orders={
            "program_name": sorted_total["program_name"].tolist(),
        },
    )
    fig_total.update_layout(
        xaxis_tickangle=-45,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_total, use_container_width=True)

    # --- Average Sessions per Day by School ---
    sorted_avg = school_summary.sort_values("Avg_Sessions_Per_Day", ascending=True)
    fig_avg = px.bar(
        sorted_avg,
        x="program_name",
        y="Avg_Sessions_Per_Day",
        color="Population",
        title="Average Sessions per Day by School",
        labels={"program_name": "School", "Avg_Sessions_Per_Day": "Avg Sessions Per Day"},
        category_orders={
            "program_name": sorted_avg["program_name"].tolist(),
        },
    )
    fig_avg.update_layout(
        xaxis_tickangle=-45,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_avg, use_container_width=True)

    # --- Quality Flags Summary (DataQuest Only) ---
    st.divider()
    st.markdown("### Quality Flag Summary (DataQuest Only)")
    st.caption(
        "Analyses session data for DataQuest schools to flag EA groups that may be running "
        "the programme incorrectly. "
        "**Moving Too Fast:** >70% of session transitions introduce only new letters with no review. "
        "**Same Letter Groups:** An EA has 3+ groups at the same letter progress level."
    )

    dq_sessions = sessions_dataframe[
        is_dataquest_school(sessions_dataframe["program_name"])
    ].copy()
    if dq_sessions.empty:
        st.info("No DataQuest session data available for quality flag analysis.")
    else:
        flag_results = _analyse_quality_flags(dq_sessions)
        if flag_results.empty:
            st.success("No flagged groups found across DataQuest schools.")
        else:
            # --- Metrics ---
            schools_with_mtf = int(flag_results.loc[flag_results["moving_too_fast_groups"] > 0, "School"].nunique())
            schools_with_slg = int(flag_results.loc[flag_results["same_letter_groups_eas"] > 0, "School"].nunique())
            total_schools = int(flag_results["School"].nunique())
            total_mtf_groups = int(flag_results["moving_too_fast_groups"].sum())
            total_slg_eas = int(flag_results["same_letter_groups_eas"].sum())

            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric(
                    "Schools with Moving Too Fast",
                    f"{schools_with_mtf} / {total_schools}",
                )
            with m2:
                st.metric("Flagged Groups (Moving Too Fast)", f"{total_mtf_groups}")
            with m3:
                st.metric("EAs with Same Letter Groups", f"{total_slg_eas}")

            st.dataframe(
                flag_results.sort_values("moving_too_fast_groups", ascending=False),
                hide_index=True,
                use_container_width=True,
            )

            # --- Bar chart ---
            chart_df = flag_results.sort_values("moving_too_fast_groups", ascending=True)
            fig_flags = px.bar(
                chart_df,
                x="School",
                y=["moving_too_fast_groups", "same_letter_groups_eas"],
                title="Quality Flags by School (DataQuest Only)",
                labels={"value": "Count", "variable": "Flag Type"},
                barmode="group",
                category_orders={"School": chart_df["School"].tolist()},
            )
            fig_flags.for_each_trace(
                lambda t: t.update(
                    name="Moving Too Fast (groups)"
                    if "moving" in t.name
                    else "Same Letter Groups (EAs)"
                )
            )
            fig_flags.update_layout(
                xaxis_tickangle=-45,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig_flags, use_container_width=True)


def render_reference_letters_per_month_chart() -> None:
    st.divider()
    st.subheader("Letters per Month (Reference Snapshot)")
    st.info("This chart uses DataQuest data to show letters learned per month by dividing the baseline results by 6 months (Jan - Jul, we subtract a month for holidays) and then comparing that to the number of letters learned over the two months of the intervention (so improvement in letters / 2)")
    reference_df = pd.DataFrame(
        [
            {
                "Group": "NMB DataQuest",
                "Jan - Jul": 3.5,
                "Sept-Oct": 4.0,
                "Percent Difference": 14.0,
            },
            {
                "Group": "BCM Control",
                "Jan - Jul": 4.3,
                "Sept-Oct": 3.5,
                "Percent Difference": -19.0,
            },
        ]
    )

    monthly_levels_df = reference_df.melt(
        id_vars=["Group", "Percent Difference"],
        value_vars=["Jan - Jul", "Sept-Oct"],
        var_name="Period",
        value_name="Letters per Month",
    )
    monthly_levels_chart = px.bar(
        monthly_levels_df,
        x="Group",
        y="Letters per Month",
        color="Period",
        barmode="group",
        title="Grade 1: Letters Learned per Month",
        color_discrete_map={"Jan - Jul": "#94a3b8", "Sept-Oct": "#2563eb"},
    )
    st.plotly_chart(monthly_levels_chart, use_container_width=True)

    percent_diff_df = reference_df[["Group", "Percent Difference"]].copy()
    percent_diff_df["Direction"] = percent_diff_df["Percent Difference"].apply(
        lambda value: "Up" if value >= 0 else "Down"
    )
    percent_diff_chart = px.bar(
        percent_diff_df,
        x="Group",
        y="Percent Difference",
        color="Direction",
        title="Percent Difference (Up vs Down)",
        labels={"Percent Difference": "Percent Difference (%)"},
        color_discrete_map={"Up": "#16a34a", "Down": "#dc2626"},
    )
    percent_diff_chart.add_hline(y=0, line_dash="dash", line_color="#475569")
    st.plotly_chart(percent_diff_chart, use_container_width=True)
    st.dataframe(reference_df, hide_index=True, use_container_width=True)


def display_dataquest_schools_2025() -> None:
    st.title("2025 DataQuest Schools")
    st.caption(
        "Combined view of endline performance and session dosage for DataQuest schools "
        "compared with a configurable benchmark group."
    )

    with st.spinner("Loading 2025 endline and sessions data..."):
        endline_df = load_endline_data_2025()
        baseline_df = load_baseline_data_2025()
        sessions_df = load_sessions_data_2025()
        endline_lookup_df = build_endline_child_lookup(endline_df)
        child_dosage_df = build_child_dosage_data(sessions_df, endline_lookup_df)
        group_dosage_df = build_group_dosage_data(sessions_df, child_dosage_df)
        session_content_df = build_session_content_data(sessions_df, endline_lookup_df)

    if endline_df.empty:
        st.error("No 2025 endline data found.")
        return
    if sessions_df.empty:
        st.error("No 2025 sessions data found.")
        return

    refresh_times: list[pd.Timestamp] = []
    if "data_refresh_timestamp" in endline_df.columns and endline_df["data_refresh_timestamp"].notna().any():
        refresh_times.append(endline_df["data_refresh_timestamp"].max())
    if "data_refresh_timestamp" in sessions_df.columns and sessions_df["data_refresh_timestamp"].notna().any():
        refresh_times.append(pd.to_datetime(sessions_df["data_refresh_timestamp"], errors="coerce").max())
    refresh_times = [timestamp for timestamp in refresh_times if pd.notna(timestamp)]
    if refresh_times:
        st.info(f"Data last refreshed: {max(refresh_times).strftime('%Y-%m-%d %H:%M:%S')}")

    st.divider()
    control_col1, control_col2, control_col3 = st.columns([1.5, 1, 1])
    with control_col1:
        comparator_mode = st.radio(
            "Comparator group",
            options=[COMPARATOR_NON_DQ, COMPARATOR_OVERALL],
            index=0,
            horizontal=False,
        )
    with control_col2:
        selected_grade = st.selectbox("Grade filter", options=GRADE_OPTIONS, index=0)
    with control_col3:
        only_11_plus = st.toggle("Show only 11+ sessions", value=False)

    endline_filtered_df = apply_endline_filters(endline_df, selected_grade, only_11_plus)
    baseline_filtered_df = baseline_df.copy()
    if selected_grade != "All Grades" and not baseline_filtered_df.empty:
        baseline_filtered_df = baseline_filtered_df[baseline_filtered_df["Grade"] == selected_grade].copy()
    child_filtered_df = apply_matched_filters(
        child_dosage_df,
        selected_grade,
        only_11_plus,
        grade_column_name="Grade",
        endline_session_column_name="session_count_total",
    )
    group_filtered_df = apply_matched_filters(
        group_dosage_df,
        selected_grade,
        only_11_plus,
        grade_column_name="Grade",
        endline_session_column_name="median_endline_sessions",
    )
    content_filtered_df = apply_matched_filters(
        session_content_df,
        selected_grade,
        only_11_plus,
        grade_column_name="Grade",
        endline_session_column_name="median_endline_sessions",
    )

    st.caption(
        "For dosage and letters-taught tabs, grade and 11+ filters are applied to records "
        "that match endline children by name + school + class."
    )

    tabs = st.tabs(
        [
            "Learning Outcomes",
            "Population Checks",
            "Learner Dosage",
            "Group Dosage",
            "School Dosage",
            "Starting Level vs Dosage",
            "What Was Taught",
        ]
    )
    with tabs[0]:
        render_learning_outcomes_tab(
            endline_filtered_df,
            baseline_filtered_df,
            comparator_mode,
        )
    with tabs[1]:
        render_population_tab(
            endline_filtered_df,
            child_filtered_df,
            group_filtered_df,
            comparator_mode,
        )
    with tabs[2]:
        render_child_dosage_tab(
            child_filtered_df,
            endline_filtered_df,
            baseline_filtered_df,
            comparator_mode,
        )
    with tabs[3]:
        render_group_dosage_tab(
            group_filtered_df,
            endline_filtered_df,
            baseline_filtered_df,
            comparator_mode,
        )
    with tabs[4]:
        render_school_dosage_tab(sessions_df, endline_filtered_df, comparator_mode)
    with tabs[5]:
        render_starting_level_vs_dosage_tab(
            endline_filtered_df,
            baseline_filtered_df,
            comparator_mode,
        )
    with tabs[6]:
        render_learning_content_tab(content_filtered_df, comparator_mode)

    render_reference_letters_per_month_chart()


if __name__ == "__main__":
    display_dataquest_schools_2025()
else:
    display_dataquest_schools_2025()
