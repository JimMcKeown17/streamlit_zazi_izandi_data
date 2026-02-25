"""
2026 Baseline Assessments — NMB and ECD
Reads live data from the DB during the baseline collection period.
Covers surveys 815 (isiXhosa), 816 (Afrikaans), 817 (English), 805 (ECD).
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database_utils import get_database_engine

st.set_page_config(page_title="2026 Baseline Assessments", layout="wide")

# ── Data Loading ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_assessments_2026():
    """Load 2026 assessment data from database."""
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
            ORDER BY response_date DESC
        """
        df = pd.read_sql(query, engine)
        df['response_date'] = pd.to_datetime(df['response_date'], errors='coerce')
        df['data_refresh_timestamp'] = pd.to_datetime(df['data_refresh_timestamp'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error loading 2026 assessment data: {str(e)}")
        return pd.DataFrame()


# ── Helpers ───────────────────────────────────────────────────────────────────

GRADE_ORDER  = ['Grade R', 'Grade 1', 'Grade 2']
LANG_COLORS  = {
    'isiXhosa':  '#1f77b4',
    'English':   '#ff7f0e',
    'Afrikaans': '#2ca02c',
    'ECD':       '#9467bd',
}


def fmt_int(n):
    return f"{int(n):,}" if pd.notna(n) else "—"


def render_summary_metrics(df):
    total   = len(df)
    xhosa   = len(df[df['language'] == 'isiXhosa'])
    english = len(df[df['language'] == 'English'])
    afrikaans = len(df[df['language'] == 'Afrikaans'])
    ecd     = len(df[df['language'] == 'ECD'])
    schools = df['program_name'].nunique()
    collectors = df['collected_by'].nunique()

    cols = st.columns(7)
    cols[0].metric("Total Assessments", fmt_int(total))
    cols[1].metric("isiXhosa", fmt_int(xhosa))
    cols[2].metric("English", fmt_int(english))
    cols[3].metric("Afrikaans", fmt_int(afrikaans))
    cols[4].metric("ECD", fmt_int(ecd))
    cols[5].metric("Schools", fmt_int(schools))
    cols[6].metric("Assessors", fmt_int(collectors))


# ── NMB Charts ────────────────────────────────────────────────────────────────

def render_nmb_charts(df_nmb):
    if df_nmb.empty:
        st.info("No NMB assessment data available yet.")
        return

    st.subheader("NMB Baseline — Letters, Non-words, Words")

    # ── 1. EGRA scores by grade ───────────────────────────────────────────────
    st.markdown("#### Average EGRA Scores by Grade")
    score_cols = {
        'Letters': 'letters_total_correct',
        'Non-words': 'nonwords_total_correct',
        'Words': 'words_total_correct',
    }
    mean_toggle = st.radio("Metric", ["Mean", "Median"], horizontal=True, key="nmb_metric")
    agg = 'mean' if mean_toggle == "Mean" else 'median'

    grade_data = []
    for grade in GRADE_ORDER:
        gdf = df_nmb[df_nmb['grade'] == grade]
        if gdf.empty:
            continue
        for label, col in score_cols.items():
            if col in gdf.columns:
                val = gdf[col].agg(agg)
                if pd.notna(val):
                    grade_data.append({'Grade': grade, 'Sub-test': label, 'Score': round(val, 1)})

    if grade_data:
        gdf_plot = pd.DataFrame(grade_data)
        fig = px.bar(
            gdf_plot, x='Grade', y='Score', color='Sub-test', barmode='group',
            title=f"{mean_toggle} EGRA Scores by Grade",
            category_orders={'Grade': GRADE_ORDER},
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── 2. Scores by language and grade ──────────────────────────────────────
    st.markdown("#### Letters Correct by Language & Grade")
    if 'letters_total_correct' in df_nmb.columns:
        lang_grade = (
            df_nmb.groupby(['language', 'grade'])['letters_total_correct']
            .agg(agg)
            .reset_index()
        )
        lang_grade.columns = ['Language', 'Grade', 'Letters Correct']
        fig2 = px.bar(
            lang_grade, x='Grade', y='Letters Correct', color='Language',
            barmode='group',
            title=f"{mean_toggle} Letters Correct by Language & Grade",
            category_orders={'Grade': GRADE_ORDER},
            color_discrete_map=LANG_COLORS,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── 3. Assessments per collector ─────────────────────────────────────────
    st.markdown("#### Assessments per Data Collector")
    collector_counts = df_nmb['collected_by'].value_counts().reset_index()
    collector_counts.columns = ['Collector', 'Assessments']
    fig3 = px.bar(
        collector_counts.head(30), x='Assessments', y='Collector',
        orientation='h', title="Assessments per Data Collector (top 30)",
        text='Assessments',
    )
    fig3.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig3, use_container_width=True)

    # ── 4. Distribution histogram ─────────────────────────────────────────────
    st.markdown("#### Distribution of Letters Correct")
    if 'letters_total_correct' in df_nmb.columns:
        fig4 = px.histogram(
            df_nmb.dropna(subset=['letters_total_correct']),
            x='letters_total_correct', color='grade', nbins=30,
            title="Distribution of Letters Correct by Grade",
            labels={'letters_total_correct': 'Letters Correct'},
            category_orders={'grade': GRADE_ORDER},
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ── 5. School breakdown ───────────────────────────────────────────────────
    with st.expander("School-Level Breakdown"):
        school_summary = (
            df_nmb.groupby('program_name')
            .agg(
                Count=('response_id', 'count'),
                Letters_Mean=('letters_total_correct', 'mean'),
                Letters_Median=('letters_total_correct', 'median'),
            )
            .reset_index()
            .sort_values('Count', ascending=False)
        )
        school_summary['Letters_Mean'] = school_summary['Letters_Mean'].round(1)
        school_summary['Letters_Median'] = school_summary['Letters_Median'].round(1)
        school_summary.columns = ['School', 'Count', 'Avg Letters', 'Median Letters']
        st.dataframe(school_summary, use_container_width=True)

    # ── 6. Raw data ───────────────────────────────────────────────────────────
    with st.expander("Raw Data"):
        display_cols = [
            'response_date', 'language', 'grade', 'program_name', 'class_name',
            'collected_by', 'first_name', 'last_name',
            'letters_total_correct', 'nonwords_total_correct', 'words_total_correct',
        ]
        cols_present = [c for c in display_cols if c in df_nmb.columns]
        st.dataframe(df_nmb[cols_present], use_container_width=True)
        csv = df_nmb.to_csv(index=False)
        st.download_button(
            "Download NMB Data CSV",
            data=csv,
            file_name="2026_nmb_baseline.csv",
            mime="text/csv",
        )


# ── ECD Charts ────────────────────────────────────────────────────────────────

def render_ecd_charts(df_ecd):
    if df_ecd.empty:
        st.info("No ECD baseline data available yet.")
        return

    st.subheader("ECD Baseline — Letters")

    # Summary metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total ECD Assessments", fmt_int(len(df_ecd)))
    c2.metric("Schools / Centers", fmt_int(df_ecd['program_name'].nunique()))
    c3.metric("Avg Letters Correct",
              round(df_ecd['letters_total_correct'].mean(), 1)
              if 'letters_total_correct' in df_ecd.columns else "—")
    c4.metric("Assessors", fmt_int(df_ecd['collected_by'].nunique()))

    # ── Letters by grade ──────────────────────────────────────────────────────
    st.markdown("#### Letters Correct by Grade")
    if 'letters_total_correct' in df_ecd.columns:
        grade_agg = (
            df_ecd.groupby('grade')['letters_total_correct']
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
    st.markdown("#### Distribution of Letters Correct (ECD)")
    if 'letters_total_correct' in df_ecd.columns:
        fig2 = px.histogram(
            df_ecd.dropna(subset=['letters_total_correct']),
            x='letters_total_correct', nbins=30,
            title="Distribution of ECD Letters Correct",
            labels={'letters_total_correct': 'Letters Correct'},
            color_discrete_sequence=[LANG_COLORS['ECD']],
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Center breakdown ──────────────────────────────────────────────────────
    with st.expander("ECD Center Breakdown"):
        center_summary = (
            df_ecd.groupby('program_name')
            .agg(
                Count=('response_id', 'count'),
                Letters_Mean=('letters_total_correct', 'mean'),
            )
            .reset_index()
            .sort_values('Count', ascending=False)
        )
        center_summary['Letters_Mean'] = center_summary['Letters_Mean'].round(1)
        center_summary.columns = ['Center / School', 'Count', 'Avg Letters']
        st.dataframe(center_summary, use_container_width=True)

    with st.expander("Raw ECD Data"):
        display_cols = [
            'response_date', 'grade', 'gender', 'program_name', 'class_name',
            'collected_by', 'first_name', 'last_name', 'letters_total_correct',
        ]
        cols_present = [c for c in display_cols if c in df_ecd.columns]
        st.dataframe(df_ecd[cols_present], use_container_width=True)
        csv = df_ecd.to_csv(index=False)
        st.download_button(
            "Download ECD Data CSV",
            data=csv,
            file_name="2026_ecd_baseline.csv",
            mime="text/csv",
        )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.title("2026 Baseline Assessments")
    st.caption("Live data — synced nightly from TeamPact. Surveys 815, 816, 817 (NMB) and 805 (ECD).")

    df = load_assessments_2026()

    if df.empty:
        st.warning("No assessment data found. Run `sync_assessments_2026` to populate the database.")
        st.stop()

    # Last refresh info
    if 'data_refresh_timestamp' in df.columns and df['data_refresh_timestamp'].notna().any():
        last_refresh = df['data_refresh_timestamp'].max()
        st.caption(f"Last synced: {last_refresh.strftime('%Y-%m-%d %H:%M UTC')}")

    # Overall summary
    render_summary_metrics(df)
    st.divider()

    # Split NMB vs ECD
    df_nmb = df[df['language'].isin(['isiXhosa', 'English', 'Afrikaans'])].copy()
    df_ecd = df[df['language'] == 'ECD'].copy()

    # Sidebar filters
    with st.sidebar:
        st.header("Filters")

        # Language filter (NMB tab)
        lang_options = ['All'] + sorted(df_nmb['language'].dropna().unique().tolist())
        selected_lang = st.selectbox("Language (NMB)", lang_options)

        # Grade filter
        grade_options = ['All'] + [g for g in GRADE_ORDER if g in df['grade'].values]
        selected_grade = st.selectbox("Grade", grade_options)

        # Assessment type filter
        types = df['assessment_type'].dropna().unique().tolist()
        if len(types) > 1:
            selected_type = st.selectbox("Assessment Type", ['All'] + sorted(types))
        else:
            selected_type = 'All'

    # Apply filters
    if selected_lang != 'All':
        df_nmb = df_nmb[df_nmb['language'] == selected_lang]
    if selected_grade != 'All':
        df_nmb = df_nmb[df_nmb['grade'] == selected_grade]
        df_ecd = df_ecd[df_ecd['grade'] == selected_grade]
    if selected_type != 'All':
        df_nmb = df_nmb[df_nmb['assessment_type'] == selected_type]
        df_ecd = df_ecd[df_ecd['assessment_type'] == selected_type]

    # Tabs
    tab_nmb, tab_ecd = st.tabs(["NMB Schools (815/816/817)", "ECD Centers (805)"])

    with tab_nmb:
        render_nmb_charts(df_nmb)

    with tab_ecd:
        render_ecd_charts(df_ecd)


main()
