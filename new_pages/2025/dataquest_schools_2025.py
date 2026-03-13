import streamlit as st
import pandas as pd
import plotly.express as px

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


def render_cohort_performance_reference_chart(
    endline_dataframe: pd.DataFrame,
    key_prefix: str,
) -> None:
    st.divider()
    st.markdown("### Cohort Performance Analysis")
    st.markdown("**Key Question:** Do more sessions lead to better EGRA performance?")

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
        key_prefix="learner_dosage",
    )


def render_group_dosage_tab(
    group_dosage_dataframe: pd.DataFrame,
    endline_dataframe: pd.DataFrame,
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

    render_cohort_performance_reference_chart(
        endline_dataframe=endline_dataframe,
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
        render_child_dosage_tab(child_filtered_df, endline_filtered_df, comparator_mode)
    with tabs[3]:
        render_group_dosage_tab(group_filtered_df, endline_filtered_df, comparator_mode)
    with tabs[4]:
        render_learning_content_tab(content_filtered_df, comparator_mode)

    render_reference_letters_per_month_chart()


if __name__ == "__main__":
    display_dataquest_schools_2025()
else:
    display_dataquest_schools_2025()
