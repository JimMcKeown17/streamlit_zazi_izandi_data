"""
2026 Midline - Primary Schools
Compares baseline and midline EGRA assessment results from assessments_2026,
split into Treatment / Control / SEF cohort tabs.
Baseline surveys: 815, 816, 817. Midline surveys: 880, 881, 882.

Cohort classification is derived from the raw (unmasked) program_name BEFORE masking
so that the public (unauthenticated) view, where program_name is aliased, still works.
"""

import importlib

import pandas as pd
import plotly.express as px
import streamlit as st

from data_privacy import mask_dataframe
from database_utils import get_database_engine


helpers = importlib.import_module("new_pages.2026.midline_primary_helpers_2026")


st.set_page_config(page_title="2026 Midline - Primary School", layout="wide")


GRADE_ORDER = ["Grade R", "Grade 1", "Grade 2"]
LANGUAGE_ORDER = ["isiXhosa", "English", "Afrikaans"]
LANGUAGE_COLORS = {
    "isiXhosa": "#1f77b4",
    "English": "#ff7f0e",
    "Afrikaans": "#2ca02c",
}
SCORE_OPTIONS = {
    "Letters": "letters_total_correct",
    "Non-words": "nonwords_total_correct",
    "Words": "words_total_correct",
}
COHORT_LABELS = {"treatment": "Treatment", "control": "Control", "sef": "SEF"}
COHORT_COLORS = {"treatment": "#1f5cc4", "control": "#9aa4b2", "sef": "#2ca02c"}


@st.cache_data(ttl=3600)
def _load_primary_midline_raw():
    try:
        engine = get_database_engine()
        query = """
            SELECT
                response_id, survey_id, survey_name,
                participant_id, first_name, last_name, gender, grade, language,
                program_name, class_name, collected_by,
                response_date,
                letters_total_correct, letters_total_incorrect,
                letters_total_attempted, letters_total_not_attempted, letters_time_taken,
                nonwords_total_correct, nonwords_total_incorrect,
                nonwords_total_attempted, nonwords_total_not_attempted, nonwords_time_taken,
                words_total_correct, words_total_incorrect,
                words_total_attempted, words_total_not_attempted, words_time_taken,
                assessment_complete, stop_rule_reached, timer_elapsed,
                assessment_type, data_refresh_timestamp
            FROM assessments_2026
            WHERE language IN ('isiXhosa', 'English', 'Afrikaans')
              AND assessment_type IN ('baseline', 'midline')
            ORDER BY response_date DESC
        """
        df = pd.read_sql(query, engine)
        normalized = helpers.normalize_primary_assessments(df)
        # Classify cohort on the raw program_name BEFORE masking (cohort is non-sensitive
        # and survives mask_dataframe, which would otherwise alias program_name).
        return helpers.add_cohort_column(normalized)
    except Exception as error:
        st.error(f"Error loading 2026 assessment data: {error}")
        return pd.DataFrame()


def load_primary_midline_data():
    return mask_dataframe(_load_primary_midline_raw(), dataset_key="assessments_2026")


def fmt_int(value):
    if pd.isna(value):
        return "-"
    return f"{int(value):,}"


def fmt_float(value, suffix=""):
    if pd.isna(value):
        return "-"
    return f"{float(value):.1f}{suffix}"


# ── Filters ─────────────────────────────────────────────────────────────────

def render_global_filters(df):
    st.subheader("Filters")
    col_language, col_grade = st.columns(2)

    with col_language:
        available_languages = set(df["language"].dropna().unique())
        language_options = ["All languages"]
        language_options.extend([language for language in LANGUAGE_ORDER if language in available_languages])
        language_options.extend(sorted(available_languages - set(LANGUAGE_ORDER)))
        selected_language = st.selectbox("Language", language_options, key="midline_primary_language_filter")

    with col_grade:
        available_grades = set(df["grade"].dropna().unique())
        grade_options = ["All grades"]
        grade_options.extend([grade for grade in GRADE_ORDER if grade in available_grades])
        grade_options.extend(sorted(available_grades - set(GRADE_ORDER)))
        default_grade_index = grade_options.index("Grade 1") if "Grade 1" in grade_options else 0
        selected_grade = st.selectbox("Grade", grade_options, index=default_grade_index, key="midline_primary_grade_filter")

    return selected_language, selected_grade


def apply_language_filter(df, language):
    if language != "All languages":
        return df[df["language"] == language]
    return df


def apply_grade_filter(df, grade):
    if grade != "All grades":
        return df[df["grade"] == grade]
    return df


def render_school_filter(df_cohort, key_prefix):
    school_values = df_cohort["program_name"].dropna().astype(str).str.strip()
    school_options = ["All schools"] + sorted([school for school in school_values.unique().tolist() if school])
    return st.selectbox("School", school_options, key=f"{key_prefix}_school_filter")


def render_unmapped_caption(df):
    if "cohort" not in df.columns:
        return
    other = df[df["cohort"] == "other"]
    if other.empty:
        return
    schools = sorted({school for school in other["program_name"].dropna().astype(str).str.strip() if school})
    learners = other["participant_id"].nunique() if "participant_id" in other.columns else len(other)
    listed = ", ".join(schools[:8]) + ("…" if len(schools) > 8 else "")
    st.caption(
        f"⚠️ {len(schools)} school(s) in the data are not in any cohort list "
        f"({fmt_int(learners)} learners) and are excluded from the tabs: {listed}. "
        "Add them to data/2026_cohorts.py to include them."
    )


def render_data_freshness(df):
    timestamps = []
    for column in ("data_refresh_timestamp", "response_date"):
        if column in df.columns and df[column].notna().any():
            timestamps.append((column, df[column].max()))

    if timestamps:
        refresh = dict(timestamps).get("data_refresh_timestamp")
        latest_response = dict(timestamps).get("response_date")
        bits = []
        if pd.notna(refresh):
            bits.append(f"Last database sync: {refresh.strftime('%Y-%m-%d %H:%M')}")
        if pd.notna(latest_response):
            bits.append(f"Latest assessment response: {latest_response.strftime('%Y-%m-%d %H:%M')}")
        st.caption(" | ".join(bits))


# ── Shared analysis sections (one cohort at a time) ─────────────────────────

def render_summary_metrics(df, matched):
    latest = helpers.latest_assessment_per_phase(df)
    baseline_count = len(latest[latest["assessment_type"] == "baseline"]) if not latest.empty else 0
    midline_count = len(latest[latest["assessment_type"] == "midline"]) if not latest.empty else 0
    matched_count = len(matched)
    match_rate = (matched_count / midline_count * 100) if midline_count else 0
    schools = df["program_name"].nunique() if "program_name" in df.columns else 0
    avg_letters_gain = matched["letters_change"].mean() if not matched.empty else pd.NA

    cols = st.columns(6)
    cols[0].metric("Baseline Learners", fmt_int(baseline_count))
    cols[1].metric("Midline Learners", fmt_int(midline_count))
    cols[2].metric("Matched Learners", fmt_int(matched_count))
    cols[3].metric("Match Rate", fmt_float(match_rate, "%"))
    cols[4].metric("Schools", fmt_int(schools))
    cols[5].metric("Avg Letter Gain", fmt_float(avg_letters_gain))


def render_phase_score_chart(df, key_prefix):
    st.header("Baseline vs Midline Scores")
    controls_left, controls_right = st.columns([1, 1])
    with controls_left:
        score_label = st.radio("Sub-test", list(SCORE_OPTIONS.keys()), horizontal=True, key=f"{key_prefix}_phase_subtest")
    with controls_right:
        agg_label = st.radio("Statistic", ["Mean", "Median"], horizontal=True, key=f"{key_prefix}_phase_stat")

    score_col = SCORE_OPTIONS[score_label]
    agg = "mean" if agg_label == "Mean" else "median"
    summary = helpers.build_phase_score_summary(df, ["grade", "language"], score_col, agg=agg)
    if summary.empty:
        st.info("No score data available for the selected filters.")
        return

    chart_data = summary.melt(
        id_vars=["grade", "language"],
        value_vars=["Baseline", "Midline"],
        var_name="Phase",
        value_name="Score",
    ).dropna(subset=["Score"])

    fig = px.bar(
        chart_data,
        x="grade",
        y="Score",
        color="Phase",
        facet_col="language",
        barmode="group",
        category_orders={"grade": GRADE_ORDER, "language": LANGUAGE_ORDER},
        title=f"{agg_label} {score_label} Correct by Grade and Language",
        color_discrete_map={"Baseline": "#9aa4b2", "Midline": "#1f5cc4"},
    )
    fig.update_layout(legend_title_text="")
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_phase_chart")

    with st.expander("View score summary table"):
        st.dataframe(summary.sort_values(["language", "grade"]), use_container_width=True, key=f"{key_prefix}_phase_table")


def render_matched_gain_section(matched, key_prefix):
    st.header("Matched Learner Gains")
    if matched.empty:
        st.info("No matched baseline/midline learners for the selected filters.")
        return

    improved = (matched["letters_change"] > 0).sum()
    flat_or_down = len(matched) - improved
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Avg Letters Gained", fmt_float(matched["letters_change"].mean()))
    col_b.metric("Median Letters Gained", fmt_float(matched["letters_change"].median()))
    col_c.metric("Improved Learners", fmt_int(improved))
    col_d.metric("Flat or Declined", fmt_int(flat_or_down))

    chart_col, scatter_col = st.columns(2)
    with chart_col:
        fig_hist = px.histogram(
            matched,
            x="letters_change",
            nbins=30,
            title="Distribution of Letter Gains",
            labels={"letters_change": "Midline - Baseline letters correct"},
            color_discrete_sequence=["#1f5cc4"],
        )
        fig_hist.add_vline(x=0, line_dash="dash", line_color="#d62728")
        st.plotly_chart(fig_hist, use_container_width=True, key=f"{key_prefix}_gain_hist")

    with scatter_col:
        fig_scatter = px.scatter(
            matched,
            x="baseline_letters_total_correct",
            y="midline_letters_total_correct",
            color="language",
            hover_data=["grade", "program_name", "letters_change"],
            title="Matched Learners: Baseline vs Midline",
            labels={
                "baseline_letters_total_correct": "Baseline letters",
                "midline_letters_total_correct": "Midline letters",
            },
            color_discrete_map=LANGUAGE_COLORS,
        )
        fig_scatter.add_shape(type="line", x0=0, y0=0, x1=60, y1=60, line={"dash": "dash", "color": "#6b7280"})
        st.plotly_chart(fig_scatter, use_container_width=True, key=f"{key_prefix}_gain_scatter")


def render_benchmark_section(df, key_prefix):
    st.header("Benchmark Movement")
    st.caption(
        "Cross-sectional: baseline and midline percentages use all assessed learners in each "
        "phase (not a matched cohort), so read movement with phase sample sizes in mind."
    )
    col_grade, col_threshold = st.columns([1, 1])
    with col_grade:
        grade_options = [grade for grade in GRADE_ORDER if grade in df["grade"].dropna().unique()]
        if not grade_options:
            st.info("No grade data available for benchmark analysis.")
            return
        selected_grade = st.selectbox("Benchmark grade", grade_options, index=0, key=f"{key_prefix}_benchmark_grade")
    with col_threshold:
        default_threshold = 40 if selected_grade == "Grade 1" else 20
        threshold = st.slider("Letters correct threshold", 0, 60, default_threshold, step=5, key=f"{key_prefix}_benchmark_threshold")

    summary = helpers.benchmark_summary(df, selected_grade, threshold)
    if summary.empty:
        st.info("No benchmark data for the selected grade.")
        return

    fig = px.bar(
        summary,
        x="Phase",
        y="Percent",
        text="Percent",
        title=f"{selected_grade}: Percent at or above {threshold} letters",
        color="Phase",
        color_discrete_map={"Baseline": "#9aa4b2", "Midline": "#1f5cc4"},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(yaxis_range=[0, max(100, summary["Percent"].max() + 10)], showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_benchmark_chart")
    st.dataframe(summary, use_container_width=True, key=f"{key_prefix}_benchmark_table")


def render_benchmark_by_school_section(df, key_prefix):
    st.header("Benchmark by School")
    grade_options = [grade for grade in GRADE_ORDER if grade in df["grade"].dropna().unique()]
    if not grade_options:
        st.info("No grade data available for the per-school benchmark.")
        return
    col_grade, col_threshold = st.columns([1, 1])
    with col_grade:
        selected_grade = st.selectbox("Grade", grade_options, index=0, key=f"{key_prefix}_benchschool_grade")
    with col_threshold:
        default_threshold = 40 if selected_grade == "Grade 1" else 20
        threshold = st.slider("Letters correct threshold", 0, 60, default_threshold, step=5, key=f"{key_prefix}_benchschool_threshold")

    summary = helpers.benchmark_by_school_summary(df, selected_grade, threshold, phase="midline")
    if summary.empty:
        st.info("No midline data for the selected grade.")
        return

    fig = px.bar(
        summary,
        x="percent",
        y="program_name",
        orientation="h",
        color="percent",
        color_continuous_scale="RdYlGn",
        range_color=[0, 100],
        hover_data=["learners", "at_or_above"],
        title=f"{selected_grade}: Midline % at or above {threshold} letters, by school",
        labels={"percent": "% at/above benchmark", "program_name": "School"},
    )
    fig.update_layout(
        height=max(360, min(1000, 26 * len(summary) + 160)),
        yaxis={"categoryorder": "total ascending"},
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_benchschool_chart")
    st.dataframe(
        summary.rename(columns={"program_name": "School", "learners": "Learners", "at_or_above": "At/Above", "percent": "Percent"}),
        use_container_width=True,
        key=f"{key_prefix}_benchschool_table",
    )


def render_zero_letter_section(df, key_prefix):
    st.header("Zero-Letter Learners")
    st.caption("Share of learners who scored 0 letters correct — a vulnerability indicator.")
    grade_options = [grade for grade in GRADE_ORDER if grade in df["grade"].dropna().unique()]
    if not grade_options:
        st.info("No grade data available.")
        return
    selected_grade = st.selectbox("Grade", grade_options, index=0, key=f"{key_prefix}_zero_grade")
    summary = helpers.zero_letter_summary(df, selected_grade)
    if summary.empty:
        st.info("No data for the selected grade.")
        return

    fig = px.bar(
        summary,
        x="Phase",
        y="Percent",
        text="Percent",
        title=f"{selected_grade}: Percent with 0 letters correct",
        color="Phase",
        color_discrete_map={"Baseline": "#d62728", "Midline": "#2ca02c"},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(yaxis_range=[0, max(10, summary["Percent"].max() + 10)], showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_zero_chart")
    st.dataframe(summary, use_container_width=True, key=f"{key_prefix}_zero_table")


def render_ea_performance_section(matched, key_prefix):
    st.header("EA Performance")
    st.caption("Average letter gain of matched learners, grouped by the EA who collected the midline assessment.")
    if matched.empty or "midline_collected_by" not in matched.columns:
        st.info("No matched learner data for EA analysis.")
        return
    min_learners = st.slider("Minimum matched learners per EA", 1, 30, 5, key=f"{key_prefix}_ea_min")
    summary = helpers.build_ea_gain_summary(matched, min_learners=min_learners)
    if summary.empty:
        st.info("No EAs meet the selected minimum.")
        return

    top = summary.head(25)
    fig = px.bar(
        top,
        x="letters_change",
        y="ea",
        orientation="h",
        color="letters_change",
        color_continuous_scale="RdYlGn",
        hover_data=["matched_learners"],
        title="Average Letter Gain by EA (top 25 by gain)",
        labels={"letters_change": "Avg letter gain", "ea": "EA"},
    )
    fig.update_layout(
        height=max(360, min(1000, 26 * len(top) + 160)),
        yaxis={"categoryorder": "total ascending"},
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_ea_chart")
    st.dataframe(
        summary.rename(columns={"ea": "EA", "matched_learners": "Matched Learners", "letters_change": "Avg Letter Gain"}),
        use_container_width=True,
        key=f"{key_prefix}_ea_table",
    )


def render_gender_section(matched, key_prefix):
    st.header("Gains by Gender")
    summary = helpers.build_gender_gain_summary(matched)
    if summary.empty:
        st.info("No gender data is available for the selected learners (2026 primary gender is often blank).")
        return

    fig = px.bar(
        summary,
        x="gender",
        y="letters_change",
        text="letters_change",
        color="gender",
        hover_data=["matched_learners"],
        title="Average Letter Gain by Gender",
        labels={"gender": "Gender", "letters_change": "Avg letter gain"},
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_gender_chart")
    st.dataframe(
        summary.rename(columns={"gender": "Gender", "matched_learners": "Matched Learners", "letters_change": "Avg Letter Gain"}),
        use_container_width=True,
        key=f"{key_prefix}_gender_table",
    )


def render_school_section(matched, key_prefix):
    st.header("School-Level Change")
    school_summary = helpers.build_school_gain_summary(matched)
    if school_summary.empty:
        st.info("No school-level matched learner data available.")
        return

    max_min = max(1, min(30, int(school_summary["matched_learners"].max())))
    min_learners = st.slider(
        "Minimum matched learners per school/grade/language",
        1,
        max_min,
        min(5, max_min),
        key=f"{key_prefix}_school_min",
    )
    display = school_summary[school_summary["matched_learners"] >= min_learners].copy()

    if display.empty:
        st.info("No school rows meet the selected minimum.")
        return

    top = display.sort_values("letters_change", ascending=False).head(20)
    fig = px.bar(
        top,
        x="letters_change",
        y="program_name",
        color="language",
        orientation="h",
        hover_data=["grade", "matched_learners", "baseline_letters", "midline_letters"],
        title="Top Letter Gains by School, Language, and Grade",
        labels={"letters_change": "Avg letter gain", "program_name": "School"},
        color_discrete_map=LANGUAGE_COLORS,
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_school_chart")

    st.dataframe(
        display.rename(
            columns={
                "program_name": "School",
                "language": "Language",
                "grade": "Grade",
                "matched_learners": "Matched Learners",
                "baseline_letters": "Baseline Letters",
                "midline_letters": "Midline Letters",
                "letters_change": "Letters Change",
                "nonwords_change": "Non-words Change",
                "words_change": "Words Change",
            }
        ),
        use_container_width=True,
        key=f"{key_prefix}_school_table",
    )


def render_data_quality(df, matched, key_prefix):
    st.header("Data Quality Checks")
    latest = helpers.latest_assessment_per_phase(df)
    unmatched = helpers.unmatched_midline_learners(df)
    midline_count = len(latest[latest["assessment_type"] == "midline"]) if not latest.empty else 0
    unmatched_rate = (len(unmatched) / midline_count * 100) if midline_count else 0

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Unmatched Midline Learners", fmt_int(len(unmatched)))
    col_b.metric("Unmatched Midline Rate", fmt_float(unmatched_rate, "%"))
    col_c.metric("Matched Rows in Analysis", fmt_int(len(matched)))

    with st.expander("Unmatched midline learners"):
        display_cols = [
            "response_date",
            "language",
            "grade",
            "program_name",
            "class_name",
            "collected_by",
            "participant_id",
            "letters_total_correct",
        ]
        cols = [col for col in display_cols if col in unmatched.columns]
        st.dataframe(unmatched[cols], use_container_width=True, key=f"{key_prefix}_dq_unmatched")

    with st.expander("Matched learner export"):
        st.dataframe(matched, use_container_width=True, key=f"{key_prefix}_dq_matched")
        st.download_button(
            "Download matched baseline-midline CSV",
            data=matched.to_csv(index=False),
            file_name=f"2026_primary_midline_matched_{key_prefix}.csv",
            mime="text/csv",
            key=f"{key_prefix}_dq_download",
        )


def render_completion_tab(summary, dimension, label, color, key_prefix):
    if summary.empty:
        st.info(f"No midline completion data available by {label.lower()}.")
        return

    top = summary.head(25).sort_values("assessments_completed", ascending=True)
    hover_columns = [column for column in ("unique_learners", "schools", "eas", "languages", "latest_response") if column in top.columns]
    fig = px.bar(
        top,
        x="assessments_completed",
        y=dimension,
        orientation="h",
        text="assessments_completed",
        hover_data=hover_columns,
        title=f"Top {len(top)} {label}s by Completed Midline Assessments",
        labels={
            dimension: label,
            "assessments_completed": "Assessments completed",
            "unique_learners": "Unique learners",
            "latest_response": "Latest response",
        },
        color_discrete_sequence=[color],
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(
        height=max(360, min(900, 28 * len(top) + 180)),
        showlegend=False,
        xaxis_title="Assessments completed",
        yaxis_title=label,
    )
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_completion_{dimension}_chart")

    display = summary.copy()
    if "latest_response" in display.columns:
        latest_response = pd.to_datetime(display["latest_response"], errors="coerce")
        display["latest_response"] = latest_response.dt.strftime("%Y-%m-%d %H:%M").fillna("")

    preferred_columns = [dimension, "assessments_completed", "unique_learners"]
    if dimension == "program_name":
        preferred_columns.extend(["eas", "languages", "latest_response"])
    else:
        preferred_columns.extend(["schools", "languages", "latest_response"])
    display = display[[column for column in preferred_columns if column in display.columns]]
    display = display.rename(
        columns={
            "program_name": "School",
            "collected_by": "EA",
            "assessments_completed": "Assessments Completed",
            "unique_learners": "Unique Learners",
            "schools": "Schools",
            "eas": "EAs",
            "languages": "Languages",
            "latest_response": "Latest Response",
        }
    )
    st.dataframe(display.reset_index(drop=True), use_container_width=True, key=f"{key_prefix}_completion_{dimension}_table")


def render_midline_completion_section(df, key_prefix):
    st.header("Midline Assessment Completion")
    st.caption("Counts use collected midline response rows for the selected filters; unique learners flags repeat assessments.")
    school_summary = helpers.build_midline_completion_summary(df, "program_name")
    ea_summary = helpers.build_midline_completion_summary(df, "collected_by")

    by_school, by_ea = st.tabs(["By school", "By EA"])
    with by_school:
        render_completion_tab(school_summary, "program_name", "School", "#1f5cc4", key_prefix)
    with by_ea:
        render_completion_tab(ea_summary, "collected_by", "EA", "#2ca02c", key_prefix)


# ── Treatment-tab extras: comparison + outstanding tracker ──────────────────

def render_treatment_vs_control_section(df_lang, matched_all, key_prefix="treatment_cmp"):
    st.header("Treatment vs Control")
    st.caption(
        "Matched baseline→midline learners, anchored on each learner's baseline school. "
        "Control midline is still in progress, so control samples are smaller — read the comparison with the n values in mind."
    )
    if matched_all.empty or "baseline_cohort" not in matched_all.columns:
        st.info("No matched learner data available for comparison.")
        return

    cmp = matched_all[matched_all["baseline_cohort"].isin(["treatment", "control"])].copy()
    if cmp.empty:
        st.info("No treatment or control matched learners yet.")
        return

    n_treat = int((cmp["baseline_cohort"] == "treatment").sum())
    n_ctrl = int((cmp["baseline_cohort"] == "control").sum())
    col_a, col_b = st.columns(2)
    col_a.metric("Treatment matched learners", fmt_int(n_treat))
    col_b.metric("Control matched learners", fmt_int(n_ctrl))

    gain = helpers.build_cohort_gain_summary(cmp)
    if not gain.empty:
        fig_gain = px.bar(
            gain,
            x="grade",
            y="letters_change",
            color="cohort",
            barmode="group",
            text="letters_change",
            category_orders={"grade": GRADE_ORDER, "cohort": ["treatment", "control"]},
            color_discrete_map=COHORT_COLORS,
            hover_data=["matched_learners", "baseline_letters", "midline_letters"],
            title="Average Letter Gain by Grade: Treatment vs Control",
            labels={"letters_change": "Avg letter gain", "grade": "Grade", "cohort": "Cohort"},
        )
        fig_gain.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        st.plotly_chart(fig_gain, use_container_width=True, key=f"{key_prefix}_gain_by_grade")

    grade_options = [grade for grade in GRADE_ORDER if grade in cmp["grade"].dropna().unique()]
    if grade_options:
        col_grade, col_threshold = st.columns([1, 1])
        with col_grade:
            default_index = grade_options.index("Grade 1") if "Grade 1" in grade_options else 0
            bench_grade = st.selectbox("Benchmark grade", grade_options, index=default_index, key=f"{key_prefix}_bench_grade")
        with col_threshold:
            default_threshold = 40 if bench_grade == "Grade 1" else 20
            bench_threshold = st.slider("Letters correct threshold", 0, 60, default_threshold, step=5, key=f"{key_prefix}_bench_threshold")
        bench = helpers.benchmark_by_cohort_matched(cmp, bench_grade, bench_threshold)
        if not bench.empty:
            fig_bench = px.bar(
                bench,
                x="Phase",
                y="Percent",
                color="cohort",
                barmode="group",
                text="Percent",
                category_orders={"Phase": ["Baseline", "Midline"], "cohort": ["treatment", "control"]},
                color_discrete_map=COHORT_COLORS,
                hover_data=["Learners", "At/Above Benchmark"],
                title=f"{bench_grade}: % at or above {bench_threshold} letters (matched learners, baseline→midline)",
                labels={"Percent": "% at/above benchmark"},
            )
            fig_bench.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig_bench.update_layout(yaxis_range=[0, max(100, bench["Percent"].max() + 10)])
            st.plotly_chart(fig_bench, use_container_width=True, key=f"{key_prefix}_bench_chart")

    if not gain.empty:
        with st.expander("Comparison summary table"):
            st.dataframe(
                gain.rename(
                    columns={
                        "cohort": "Cohort",
                        "grade": "Grade",
                        "matched_learners": "Matched Learners",
                        "baseline_letters": "Baseline Letters",
                        "midline_letters": "Midline Letters",
                        "letters_change": "Avg Letter Gain",
                    }
                ).sort_values(["Grade", "Cohort"]),
                use_container_width=True,
                key=f"{key_prefix}_table",
            )

    fig_dist = px.histogram(
        cmp,
        x="letters_change",
        color="baseline_cohort",
        barmode="overlay",
        nbins=30,
        opacity=0.6,
        color_discrete_map=COHORT_COLORS,
        title="Distribution of Letter Gains: Treatment vs Control",
        labels={"letters_change": "Midline - Baseline letters correct", "baseline_cohort": "Cohort"},
    )
    fig_dist.add_vline(x=0, line_dash="dash", line_color="#6b7280")
    st.plotly_chart(fig_dist, use_container_width=True, key=f"{key_prefix}_dist")


def render_outstanding_section(df_lang, key_prefix="treatment_out"):
    st.header("Outstanding Midline Assessments (Treatment)")
    st.caption(
        "Treatment learners assessed at baseline who still have no midline anywhere — the assessment work still outstanding. "
        "Defaults to all grades so nothing is hidden."
    )
    grade_values = [grade for grade in GRADE_ORDER if grade in df_lang["grade"].dropna().unique()]
    grade_choice = st.selectbox("Grade", ["All grades"] + grade_values, index=0, key=f"{key_prefix}_grade")
    frame = df_lang if grade_choice == "All grades" else df_lang[df_lang["grade"] == grade_choice]

    summary = helpers.outstanding_midline_by_school_grade(frame)
    if summary.empty:
        st.success("No outstanding midline assessments for treatment schools at the current filters. 🎉")
        return

    total_outstanding = int(summary["outstanding"].sum())
    total_baseline = int(summary["baseline_learners"].sum())
    pct_complete = round((total_baseline - total_outstanding) / total_baseline * 100, 1) if total_baseline else 0
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Baseline learners (treatment)", fmt_int(total_baseline))
    col_b.metric("Still outstanding", fmt_int(total_outstanding))
    col_c.metric("Midline complete", fmt_float(pct_complete, "%"))

    by_school = (
        summary.groupby("program_name", as_index=False)["outstanding"].sum().sort_values("outstanding", ascending=False)
    )
    by_school = by_school[by_school["outstanding"] > 0].head(30)
    if not by_school.empty:
        fig = px.bar(
            by_school,
            x="outstanding",
            y="program_name",
            orientation="h",
            title="Outstanding Midline Assessments by School (top 30)",
            labels={"outstanding": "Learners still to assess", "program_name": "School"},
            color_discrete_sequence=["#d62728"],
        )
        fig.update_layout(height=max(360, min(1100, 26 * len(by_school) + 160)), yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_chart")

    st.dataframe(
        summary.rename(
            columns={
                "program_name": "School",
                "grade": "Grade",
                "baseline_learners": "Baseline",
                "midline_learners": "Midline Done",
                "outstanding": "Outstanding",
                "percent_complete": "% Complete",
            }
        ),
        use_container_width=True,
        key=f"{key_prefix}_table",
    )

    learners = helpers.outstanding_baseline_learners(frame)
    if not learners.empty:
        display_cols = [
            "response_date",
            "language",
            "grade",
            "program_name",
            "class_name",
            "collected_by",
            "participant_id",
            "letters_total_correct",
        ]
        cols = [col for col in display_cols if col in learners.columns]
        with st.expander(f"List of {fmt_int(len(learners))} learners still needing a midline assessment"):
            st.dataframe(learners[cols].reset_index(drop=True), use_container_width=True, key=f"{key_prefix}_learners_table")
            st.download_button(
                "Download outstanding learners CSV",
                data=learners[cols].to_csv(index=False),
                file_name="2026_treatment_outstanding_midline_learners.csv",
                mime="text/csv",
                key=f"{key_prefix}_download",
            )


# ── Orchestration ───────────────────────────────────────────────────────────

def render_cohort_analysis(df_g, matched_all, cohort_key, grade):
    label = COHORT_LABELS[cohort_key]
    df_cohort = df_g[df_g["cohort"] == cohort_key].copy()
    if not matched_all.empty and "baseline_cohort" in matched_all.columns:
        matched = matched_all[matched_all["baseline_cohort"] == cohort_key].copy()
        if grade != "All grades":
            matched = matched[matched["grade"] == grade]
    else:
        matched = pd.DataFrame()

    if df_cohort.empty:
        st.info(f"No {label} assessment data for the current filters.")
        return

    selected_school = render_school_filter(df_cohort, key_prefix=cohort_key)
    if selected_school != "All schools":
        df_cohort = df_cohort[df_cohort["program_name"] == selected_school]
        if not matched.empty:
            matched = matched[matched["baseline_program_name"] == selected_school]

    render_summary_metrics(df_cohort, matched)
    st.divider()
    render_phase_score_chart(df_cohort, cohort_key)
    st.divider()
    render_matched_gain_section(matched, cohort_key)
    st.divider()
    render_benchmark_section(df_cohort, cohort_key)
    st.divider()
    render_benchmark_by_school_section(df_cohort, cohort_key)
    st.divider()
    render_zero_letter_section(df_cohort, cohort_key)
    st.divider()
    render_ea_performance_section(matched, cohort_key)
    st.divider()
    render_gender_section(matched, cohort_key)
    st.divider()
    render_school_section(matched, cohort_key)
    st.divider()
    render_data_quality(df_cohort, matched, cohort_key)
    st.divider()
    render_midline_completion_section(df_cohort, cohort_key)


def render_treatment_tab(df_lang, df_g, matched_all, grade):
    render_treatment_vs_control_section(df_lang, matched_all)
    st.divider()
    render_cohort_analysis(df_g, matched_all, "treatment", grade)
    st.divider()
    render_outstanding_section(df_lang)


def main():
    st.title("2026 Midline - Primary School")
    st.caption(
        "Baseline surveys 815/816/817 vs midline surveys 880/881/882, split into "
        "Treatment / Control / SEF cohorts. ECD is excluded from this page."
    )

    df = load_primary_midline_data()
    if df.empty:
        st.warning("No 2026 primary baseline or midline assessment data found.")
        st.stop()

    render_data_freshness(df)
    render_unmapped_caption(df)
    language, grade = render_global_filters(df)
    df_lang = apply_language_filter(df, language)
    df_g = apply_grade_filter(df_lang, grade)
    matched_all = helpers.build_matched_assessment_pairs(df_lang)
    counts = helpers.cohort_counts()

    st.divider()
    tab_treatment, tab_control, tab_sef = st.tabs(
        [
            f"Treatment ({counts['treatment']})",
            f"Control ({counts['control']})",
            f"SEF ({counts['sef']})",
        ]
    )
    with tab_treatment:
        render_treatment_tab(df_lang, df_g, matched_all, grade)
    with tab_control:
        render_cohort_analysis(df_g, matched_all, "control", grade)
    with tab_sef:
        render_cohort_analysis(df_g, matched_all, "sef", grade)


main()
