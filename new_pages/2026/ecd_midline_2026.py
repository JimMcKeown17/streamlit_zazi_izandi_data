"""
2026 Midline - ECD
Compares ECD baseline (survey 805) and midline (survey 891) EGRA letters results.

All comparisons are CROSS-SECTIONAL: the baseline survey has no participant IDs, so
learners cannot be matched across phases (unlike the primary midline page). Analytics
count raw response rows for both phases; unique-learner counts are midline-only.
"""

import importlib

import pandas as pd
import plotly.express as px
import streamlit as st

from data_privacy import mask_dataframe
from database_utils import get_database_engine


helpers = importlib.import_module("new_pages.2026.ecd_midline_helpers_2026")


st.set_page_config(page_title="2026 Midline - ECD", layout="wide")


PHASE_COLORS = {"Baseline": "#9aa4b2", "Midline": "#1f5cc4"}
ECD_ACCENT = "#9467bd"


@st.cache_data(ttl=3600)
def _load_ecd_midline_raw():
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
                assessment_complete, assessment_type, data_refresh_timestamp
            FROM assessments_2026
            WHERE survey_id IN (805, 891)
              AND assessment_type IN ('baseline', 'midline')
            ORDER BY response_date DESC
        """
        df = pd.read_sql(query, engine)
        return helpers.normalize_ecd_assessments(df)
    except Exception as error:
        st.error(f"Error loading 2026 ECD assessment data: {error}")
        return pd.DataFrame()


def load_ecd_midline_data():
    return mask_dataframe(_load_ecd_midline_raw(), dataset_key="assessments_2026_ecd")


def fmt_int(value):
    if pd.isna(value):
        return "-"
    return f"{int(value):,}"


def fmt_float(value, suffix=""):
    if pd.isna(value):
        return "-"
    return f"{float(value):.1f}{suffix}"


def render_data_freshness(df):
    bits = []
    if "data_refresh_timestamp" in df.columns and df["data_refresh_timestamp"].notna().any():
        bits.append(f"Last database sync: {df['data_refresh_timestamp'].max().strftime('%Y-%m-%d %H:%M')}")
    if "response_date" in df.columns and df["response_date"].notna().any():
        bits.append(f"Latest assessment response: {df['response_date'].max().strftime('%Y-%m-%d %H:%M')}")
    if bits:
        st.caption(" | ".join(bits))


# ── Sections ─────────────────────────────────────────────────────────────────

def render_summary_metrics(df):
    summary = helpers.build_phase_letter_summary(df)
    if summary.empty:
        st.info("No ECD assessment data for either phase yet.")
        return

    by_phase = summary.set_index("Phase")
    midline = df[df["assessment_type"] == "midline"]
    unique_midline_learners = (
        midline["participant_id"].fillna("").astype(str).str.strip().replace("", pd.NA).nunique()
        if "participant_id" in midline.columns
        else 0
    )

    cols = st.columns(6)
    cols[0].metric("Baseline Assessments", fmt_int(by_phase["Assessments"].get("Baseline", 0)))
    cols[1].metric("Midline Assessments", fmt_int(by_phase["Assessments"].get("Midline", 0)))
    cols[2].metric("Midline Unique Learners", fmt_int(unique_midline_learners))
    cols[3].metric("Centers Assessed (Midline)", fmt_int(by_phase["Centers"].get("Midline", 0)))
    cols[4].metric("Baseline Avg Letters", fmt_float(by_phase["Mean Letters"].get("Baseline", pd.NA)))
    cols[5].metric("Midline Avg Letters", fmt_float(by_phase["Mean Letters"].get("Midline", pd.NA)))


def render_letters_section(df, key_prefix="ecd_letters"):
    st.header("Letters Learned: Baseline vs Midline")
    st.caption(
        "Cross-sectional comparison of all assessments in each phase — learners are NOT matched "
        "(the baseline survey had no participant IDs). Midline collection is still in progress and "
        "moves center by center; baseline rows carry no center identifiers, so the baseline cannot "
        "be re-weighted to the centers assessed so far. Read the midline-vs-baseline difference as "
        "provisional until collection completes."
    )

    summary = helpers.build_phase_letter_summary(df)
    if summary.empty or "Midline" not in set(summary["Phase"]):
        st.info("No midline assessments yet — the comparison will appear once survey 891 data is synced.")
        if not summary.empty:
            st.dataframe(summary, use_container_width=True, key=f"{key_prefix}_phase_table_baseline_only")
        return

    by_phase = summary.set_index("Phase")
    delta = by_phase["Mean Letters"].get("Midline", pd.NA) - by_phase["Mean Letters"].get("Baseline", pd.NA)
    st.markdown(f"**Provisional average letter gain (cross-sectional): {fmt_float(delta)} letters**")

    dist_col, bar_col = st.columns(2)
    with dist_col:
        frame = df.dropna(subset=["letters_total_correct"]).copy()
        frame["Phase"] = frame["assessment_type"].map(helpers.PHASE_LABELS)
        fig_dist = px.histogram(
            frame,
            x="letters_total_correct",
            color="Phase",
            barmode="overlay",
            histnorm="percent",
            nbins=30,
            opacity=0.65,
            category_orders={"Phase": ["Baseline", "Midline"]},
            color_discrete_map=PHASE_COLORS,
            title="Distribution of Letters Correct by Phase (% of phase)",
            labels={"letters_total_correct": "Letters correct"},
        )
        st.plotly_chart(fig_dist, use_container_width=True, key=f"{key_prefix}_dist")

    with bar_col:
        stat_label = st.radio("Statistic", ["Mean", "Median"], horizontal=True, key=f"{key_prefix}_stat")
        value_col = "Mean Letters" if stat_label == "Mean" else "Median Letters"
        fig_bar = px.bar(
            summary,
            x="Phase",
            y=value_col,
            text=value_col,
            color="Phase",
            category_orders={"Phase": ["Baseline", "Midline"]},
            color_discrete_map=PHASE_COLORS,
            title=f"{stat_label} Letters Correct by Phase",
            labels={value_col: f"{stat_label} letters correct"},
        )
        fig_bar.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True, key=f"{key_prefix}_bar")

    st.dataframe(summary, use_container_width=True, key=f"{key_prefix}_phase_table")


def render_benchmark_section(df, key_prefix="ecd_benchmark"):
    st.header("Benchmark Movement")
    st.caption("Share of assessments at or above a letters-correct threshold, per phase (cross-sectional).")
    threshold = st.slider("Letters correct threshold", 0, 60, 10, step=5, key=f"{key_prefix}_threshold")

    summary = helpers.benchmark_summary(df, threshold)
    if summary.empty:
        st.info("No benchmark data available.")
        return threshold

    fig = px.bar(
        summary,
        x="Phase",
        y="Percent",
        text="Percent",
        color="Phase",
        category_orders={"Phase": ["Baseline", "Midline"]},
        color_discrete_map=PHASE_COLORS,
        title=f"Percent at or above {threshold} letters",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(yaxis_range=[0, max(100, summary["Percent"].max() + 10)], showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_chart")
    st.dataframe(summary, use_container_width=True, key=f"{key_prefix}_table")
    return threshold


def render_zero_letter_section(df, key_prefix="ecd_zero"):
    st.header("Zero-Letter Learners")
    st.caption("Share of assessments scoring 0 letters correct — a vulnerability indicator.")
    summary = helpers.zero_letter_summary(df)
    if summary.empty:
        st.info("No data available.")
        return

    fig = px.bar(
        summary,
        x="Phase",
        y="Percent",
        text="Percent",
        color="Phase",
        category_orders={"Phase": ["Baseline", "Midline"]},
        color_discrete_map={"Baseline": "#d62728", "Midline": "#2ca02c"},
        title="Percent with 0 letters correct",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(yaxis_range=[0, max(10, summary["Percent"].max() + 10)], showlegend=False)
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_chart")
    st.dataframe(summary, use_container_width=True, key=f"{key_prefix}_table")


def render_center_section(df, threshold, key_prefix="ecd_center"):
    st.header("Centers (Midline)")
    st.caption(
        "Midline only — baseline rows carry no center identifiers, so per-center "
        f"baseline comparison is not possible. Benchmark column uses the {threshold}-letter "
        "threshold selected above."
    )
    summary = helpers.build_midline_dimension_summary(df, "program_name", threshold=threshold)
    if summary.empty:
        st.info("No midline center data yet.")
        return

    fig = px.bar(
        summary,
        x="mean_letters",
        y="program_name",
        orientation="h",
        color="percent",
        color_continuous_scale="RdYlGn",
        range_color=[0, 100],
        hover_data=["assessments", "unique_learners", "at_or_above"],
        title="Mean Letters Correct by Center (color = % at/above benchmark)",
        labels={"mean_letters": "Mean letters correct", "program_name": "Center", "percent": "% at/above"},
    )
    fig.update_layout(
        height=max(360, min(1100, 26 * len(summary) + 160)),
        yaxis={"categoryorder": "total ascending"},
    )
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_chart")
    st.dataframe(
        summary.rename(
            columns={
                "program_name": "Center",
                "assessments": "Assessments",
                "unique_learners": "Unique Learners",
                "mean_letters": "Mean Letters",
                "at_or_above": "At/Above Benchmark",
                "percent": "% At/Above",
            }
        ),
        use_container_width=True,
        key=f"{key_prefix}_table",
    )


def render_ea_section(df, key_prefix="ecd_ea"):
    st.header("Assessors (Midline)")
    st.caption(
        "Assessments captured and mean letters per assessor — an outlier-flagging view, "
        "not a performance ranking (no matched gains are possible for ECD)."
    )
    summary = helpers.build_midline_dimension_summary(df, "collected_by")
    if summary.empty:
        st.info("No midline assessor data yet.")
        return

    min_assessments = st.slider("Minimum assessments per assessor", 1, 30, 5, key=f"{key_prefix}_min")
    display = summary[summary["assessments"] >= min_assessments]
    if display.empty:
        st.info("No assessors meet the selected minimum.")
        return

    fig = px.bar(
        display,
        x="assessments",
        y="collected_by",
        orientation="h",
        color="mean_letters",
        color_continuous_scale="RdYlGn",
        text="assessments",
        hover_data=["unique_learners", "mean_letters"],
        title="Midline Assessments per Assessor (color = mean letters)",
        labels={"assessments": "Assessments", "collected_by": "Assessor", "mean_letters": "Mean letters"},
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig.update_layout(
        height=max(360, min(1000, 26 * len(display) + 160)),
        yaxis={"categoryorder": "total ascending"},
    )
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_chart")
    st.dataframe(
        display.rename(
            columns={
                "collected_by": "Assessor",
                "assessments": "Assessments",
                "unique_learners": "Unique Learners",
                "mean_letters": "Mean Letters",
            }
        ),
        use_container_width=True,
        key=f"{key_prefix}_table",
    )


def render_daily_capture_section(df, key_prefix="ecd_daily"):
    st.header("Assessments Captured per Day")
    st.caption("Every collected baseline and midline response row — repeat assessments included.")
    daily = helpers.build_daily_assessment_counts(df)
    if daily.empty:
        st.info("No dated assessment responses available.")
        return

    fig = px.bar(
        daily,
        x="date",
        y="assessments",
        color="Phase",
        category_orders={"Phase": ["Baseline", "Midline"]},
        color_discrete_map=PHASE_COLORS,
        title="Assessments Captured per Day",
        labels={"date": "Date", "assessments": "Assessments captured"},
    )
    fig.update_layout(legend_title_text="", bargap=0.1)
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_chart")

    with st.expander("View daily capture table"):
        table = daily.copy()
        table["date"] = table["date"].dt.strftime("%Y-%m-%d")
        st.dataframe(
            table.rename(columns={"date": "Date", "assessments": "Assessments"}),
            use_container_width=True,
            key=f"{key_prefix}_table",
        )


def render_export_section(df, key_prefix="ecd_export"):
    st.header("Data Export")
    display_cols = [
        "response_date",
        "assessment_type",
        "grade",
        "program_name",
        "class_name",
        "collected_by",
        "participant_id",
        "first_name",
        "last_name",
        "letters_total_correct",
    ]
    cols = [col for col in display_cols if col in df.columns]
    with st.expander("Raw ECD baseline + midline data"):
        st.dataframe(df[cols], use_container_width=True, key=f"{key_prefix}_table")
        st.download_button(
            "Download ECD midline/baseline CSV",
            data=df[cols].to_csv(index=False),
            file_name="2026_ecd_midline_baseline.csv",
            mime="text/csv",
            key=f"{key_prefix}_download",
        )


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    st.title("2026 Midline - ECD")
    st.caption(
        "ECD baseline (survey 805) vs midline (survey 891), letters only. Learners are not "
        "matched across phases — the baseline survey had no participant IDs — so all "
        "comparisons are cross-sectional. Gender is only available at baseline (the midline "
        "survey structure does not capture it)."
    )

    df = load_ecd_midline_data()
    if df.empty:
        st.warning("No 2026 ECD assessment data found.")
        st.stop()

    render_data_freshness(df)
    st.divider()
    render_summary_metrics(df)
    st.divider()
    render_letters_section(df)
    st.divider()
    threshold = render_benchmark_section(df)
    st.divider()
    render_zero_letter_section(df)
    st.divider()
    render_center_section(df, threshold)
    st.divider()
    render_ea_section(df)
    st.divider()
    render_daily_capture_section(df)
    st.divider()
    render_export_section(df)


main()
