"""
2026 ECD Baseline Assessments
Reads live data from the DB. Survey 805 (ZZ ECD Baseline 2026).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from database_utils import get_database_engine

st.set_page_config(page_title="2026 ECD Baseline", layout="wide")

# ── Data Loading ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_ecd_assessments():
    """Load ECD assessment data from database, excluding null grades."""
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
                assessment_complete, stop_rule_reached, timer_elapsed,
                assessment_type, data_refresh_timestamp
            FROM assessments_2026
            WHERE language = 'ECD' AND grade != 'null'
            ORDER BY response_date DESC
        """
        df = pd.read_sql(query, engine)
        df['response_date'] = pd.to_datetime(df['response_date'], errors='coerce')
        df['data_refresh_timestamp'] = pd.to_datetime(df['data_refresh_timestamp'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error loading ECD assessment data: {str(e)}")
        return pd.DataFrame()


# ── Helpers ───────────────────────────────────────────────────────────────────

LANG_COLORS = {'ECD': '#9467bd'}


def fmt_int(n):
    return f"{int(n):,}" if pd.notna(n) else "—"


# ── Charts ───────────────────────────────────────────────────────────────────

def render_ecd_charts(df):
    if df.empty:
        st.info("No ECD baseline data available yet.")
        return

    # Summary metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Assessments", fmt_int(len(df)))
    c2.metric("Centers / Schools", fmt_int(df['program_name'].nunique()))
    c3.metric("Avg Letters Correct",
              round(df['letters_total_correct'].mean(), 1)
              if 'letters_total_correct' in df.columns else "—")
    c4.metric("Assessors", fmt_int(df['collected_by'].nunique()))

    st.divider()

    # ── Letters by grade ──────────────────────────────────────────────────────
    st.markdown("#### Letters Correct by Grade")
    if 'letters_total_correct' in df.columns:
        grade_agg = (
            df.groupby('grade')['letters_total_correct']
            .agg(['mean', 'median', 'count'])
            .reset_index()
        )
        grade_agg.columns = ['Grade', 'Mean', 'Median', 'Count']
        grade_agg[['Mean', 'Median']] = grade_agg[['Mean', 'Median']].round(1)
        fig = px.bar(
            grade_agg, x='Grade', y='Mean', text='Mean',
            title="Mean Letters Correct by Grade (ECD)",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Distribution ──────────────────────────────────────────────────────────
    st.markdown("#### Distribution of Letters Correct")
    if 'letters_total_correct' in df.columns:
        fig2 = px.histogram(
            df.dropna(subset=['letters_total_correct']),
            x='letters_total_correct', nbins=30,
            title="Distribution of ECD Letters Correct",
            labels={'letters_total_correct': 'Letters Correct'},
            color_discrete_sequence=[LANG_COLORS['ECD']],
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Assessments per collector ─────────────────────────────────────────────
    st.markdown("#### Assessments per Data Collector")
    collector_counts = df['collected_by'].value_counts().reset_index()
    collector_counts.columns = ['Collector', 'Assessments']
    fig3 = px.bar(
        collector_counts.head(30), x='Assessments', y='Collector',
        orientation='h', title="Assessments per Data Collector (top 30)",
        text='Assessments',
    )
    fig3.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig3, use_container_width=True)

    # ── Center breakdown ──────────────────────────────────────────────────────
    with st.expander("ECD Center Breakdown"):
        center_summary = (
            df.groupby('program_name')
            .agg(
                Count=('response_id', 'count'),
                Letters_Mean=('letters_total_correct', 'mean'),
                Letters_Median=('letters_total_correct', 'median'),
            )
            .reset_index()
            .sort_values('Count', ascending=False)
        )
        center_summary['Letters_Mean'] = center_summary['Letters_Mean'].round(1)
        center_summary['Letters_Median'] = center_summary['Letters_Median'].round(1)
        center_summary.columns = ['Center / School', 'Count', 'Avg Letters', 'Median Letters']
        st.dataframe(center_summary, use_container_width=True)

    with st.expander("Raw ECD Data"):
        display_cols = [
            'response_date', 'grade', 'gender', 'program_name', 'class_name',
            'collected_by', 'first_name', 'last_name', 'letters_total_correct',
        ]
        cols_present = [c for c in display_cols if c in df.columns]
        st.dataframe(df[cols_present], use_container_width=True)
        csv = df.to_csv(index=False)
        st.download_button(
            "Download ECD Data CSV",
            data=csv,
            file_name="2026_ecd_baseline.csv",
            mime="text/csv",
        )


# ── Collector Outlier Analysis ────────────────────────────────────────────────

def render_collector_outliers(df):
    if df.empty or 'letters_total_correct' not in df.columns:
        return

    st.divider()
    st.header("Potential Outlier Assessors")
    st.caption(
        "Top 10 and bottom 10 collectors by mean letters correct. "
        "Collectors with fewer than 5 assessments are excluded."
    )

    MIN_ASSESSMENTS = 5

    collector_stats = (
        df.dropna(subset=['letters_total_correct', 'collected_by'])
        .groupby('collected_by')['letters_total_correct']
        .agg(mean='mean', count='count')
        .reset_index()
    )
    collector_stats = collector_stats[collector_stats['count'] >= MIN_ASSESSMENTS].copy()
    collector_stats['mean'] = collector_stats['mean'].round(1)
    collector_stats = collector_stats.sort_values('mean', ascending=False)

    if collector_stats.empty:
        return

    col_top, col_bot = st.columns(2)
    top10 = collector_stats.head(10)
    bot10 = collector_stats.tail(10).sort_values('mean', ascending=True)

    with col_top:
        fig_top = px.bar(
            top10, x='mean', y='collected_by', orientation='h',
            title="Top 10 Collectors",
            labels={'mean': 'Avg Letters Correct', 'collected_by': 'Collector'},
            text='mean',
            color_discrete_sequence=['#2ca02c'],
        )
        fig_top.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
        st.plotly_chart(fig_top, use_container_width=True)

    with col_bot:
        fig_bot = px.bar(
            bot10, x='mean', y='collected_by', orientation='h',
            title="Bottom 10 Collectors",
            labels={'mean': 'Avg Letters Correct', 'collected_by': 'Collector'},
            text='mean',
            color_discrete_sequence=['#d62728'],
        )
        fig_bot.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
        st.plotly_chart(fig_bot, use_container_width=True)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.title("2026 ECD Baseline Assessments")
    st.caption("Live data — synced nightly from TeamPact. Survey 805 (ZZ ECD Baseline 2026).")

    df = load_ecd_assessments()

    if df.empty:
        st.warning("No ECD assessment data found.")
        st.stop()

    if 'data_refresh_timestamp' in df.columns and df['data_refresh_timestamp'].notna().any():
        last_refresh = df['data_refresh_timestamp'].max()
        st.caption(f"Last synced: {last_refresh.strftime('%Y-%m-%d %H:%M UTC')}")

    render_ecd_charts(df)
    render_collector_outliers(df)


main()
