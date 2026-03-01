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


@st.cache_data(ttl=3600)
def load_letter_cells():
    """Load all letter cell results joined with assessment grade/language."""
    try:
        engine = get_database_engine()
        query = """
            SELECT c.response_id, c.cell_id, c.cell_index, c.status,
                   a.grade, a.language
            FROM assessment_cells_2026 c
            JOIN assessments_2026 a ON a.response_id = c.response_id
            WHERE c.question_type = 'letters'
              AND a.language IN ('isiXhosa', 'English', 'Afrikaans')
            ORDER BY c.cell_index
        """
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Error loading cell data: {str(e)}")
        return pd.DataFrame()


# ── Helpers ───────────────────────────────────────────────────────────────────

GRADE_ORDER  = ['PreR', 'Grade R', 'Grade 1', 'Grade 2']
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


# ── Letter-Level Analysis ─────────────────────────────────────────────────────

def render_letter_analysis(df_nmb):
    """Show % correct for each letter position in the EGRA grid, by grade."""
    if df_nmb.empty:
        return

    st.divider()
    st.header("Letter-Level Analysis")
    st.caption(
        "Percentage of learners who answered each letter correctly, shown in the "
        "order they appear on the EGRA assessment grid (60 letters). "
        "'Incomplete' attempts (stop rule) are excluded from the denominator."
    )

    all_cells = load_letter_cells()

    if all_cells.empty:
        st.info("No letter cell data available.")
        return

    # Filter cells to match current df_nmb selection (language, grade filters)
    filtered_ids = set(df_nmb['response_id'].tolist())
    cells = all_cells[all_cells['response_id'].isin(filtered_ids)].copy()

    if cells.empty:
        st.info("No letter cell data available.")
        return

    # Only count correct vs incorrect (exclude 'incomplete' — not attempted)
    cells_attempted = cells[cells['status'].isin(['correct', 'incorrect'])].copy()

    if cells_attempted.empty:
        st.info("No attempted letter data found.")
        return

    # Build letter labels from the most common cell_id at each position
    letter_labels = (
        cells.groupby('cell_index')['cell_id']
        .agg(lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else '?')
        .sort_index()
    )

    # Overall % correct by position
    overall = (
        cells_attempted.groupby('cell_index')
        .agg(correct=('status', lambda s: (s == 'correct').sum()), total=('status', 'count'))
        .reset_index()
    )
    overall['pct_correct'] = (overall['correct'] / overall['total'] * 100).round(1)
    overall['letter'] = overall['cell_index'].map(letter_labels)

    # By grade
    by_grade = (
        cells_attempted.groupby(['grade', 'cell_index'])
        .agg(correct=('status', lambda s: (s == 'correct').sum()), total=('status', 'count'))
        .reset_index()
    )
    by_grade['pct_correct'] = (by_grade['correct'] / by_grade['total'] * 100).round(1)
    by_grade['letter'] = by_grade['cell_index'].map(letter_labels)

    # ── Heatmap: grades as rows, letter positions as columns ──────────────
    grades_present = [g for g in GRADE_ORDER if g in by_grade['grade'].values]

    if grades_present:
        # Build a matrix: rows = grades, columns = letter positions
        pivot = by_grade.pivot_table(
            index='grade', columns='cell_index', values='pct_correct'
        ).reindex(grades_present)

        col_labels = [letter_labels.get(i, '?') for i in pivot.columns]

        fig_heat = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=col_labels,
            y=pivot.index.tolist(),
            colorscale='RdYlGn',
            zmin=0, zmax=100,
            text=pivot.values.round(0).astype(int),
            texttemplate='%{text}%',
            textfont={'size': 9},
            colorbar=dict(title='% Correct'),
        ))
        fig_heat.update_layout(
            title="% Correct per Letter Position by Grade",
            xaxis_title="Letter (assessment order)",
            yaxis_title="Grade",
            height=300,
            xaxis=dict(dtick=1),
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    # ── Bar chart: overall % correct per position ─────────────────────────
    fig_bar = px.bar(
        overall, x='letter', y='pct_correct',
        title="Overall % Correct per Letter Position (all grades)",
        labels={'pct_correct': '% Correct', 'letter': 'Letter'},
        text='pct_correct',
        color='pct_correct',
        color_continuous_scale='RdYlGn',
        range_color=[0, 100],
    )
    fig_bar.update_layout(
        xaxis=dict(dtick=1),
        showlegend=False,
        coloraxis_showscale=False,
    )
    fig_bar.update_traces(texttemplate='%{text:.0f}%', textposition='outside', textfont_size=9)
    st.plotly_chart(fig_bar, use_container_width=True)

    # ── Per-grade line chart ──────────────────────────────────────────────
    if len(grades_present) > 1:
        fig_line = px.line(
            by_grade[by_grade['grade'].isin(grades_present)],
            x='cell_index', y='pct_correct', color='grade',
            title="% Correct by Letter Position — Grade Comparison",
            labels={'pct_correct': '% Correct', 'cell_index': 'Letter Position', 'grade': 'Grade'},
            category_orders={'grade': GRADE_ORDER},
        )
        # Add letter labels on x-axis
        fig_line.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=list(letter_labels.index),
                ticktext=[letter_labels.get(i, '') for i in letter_labels.index],
                dtick=1,
            )
        )
        st.plotly_chart(fig_line, use_container_width=True)


# ── Collector Outlier Analysis ────────────────────────────────────────────────

def render_collector_outliers(df):
    if df.empty or 'letters_total_correct' not in df.columns:
        return

    grades_present = [g for g in GRADE_ORDER if g in df['grade'].values]
    if not grades_present:
        return

    st.divider()
    st.header("Potential Outlier Assessors")
    st.caption(
        "Top 10 and bottom 10 collectors by mean letters correct, per grade. "
        "Collectors with fewer than 5 assessments are excluded. "
        "Outliers may indicate data quality issues worth investigating."
    )

    MIN_ASSESSMENTS = 5

    for grade in grades_present:
        gdf = df[df['grade'] == grade].dropna(subset=['letters_total_correct', 'collected_by'])
        if gdf.empty:
            continue

        collector_stats = (
            gdf.groupby('collected_by')['letters_total_correct']
            .agg(mean='mean', count='count')
            .reset_index()
        )
        collector_stats = collector_stats[collector_stats['count'] >= MIN_ASSESSMENTS].copy()
        collector_stats['mean'] = collector_stats['mean'].round(1)
        collector_stats = collector_stats.sort_values('mean', ascending=False)

        if collector_stats.empty:
            continue

        st.subheader(f"{grade}")
        col_top, col_bot = st.columns(2)

        top10 = collector_stats.head(10)
        bot10 = collector_stats.tail(10).sort_values('mean', ascending=True)

        with col_top:
            fig_top = px.bar(
                top10, x='mean', y='collected_by', orientation='h',
                title=f"Top 10 — {grade}",
                labels={'mean': 'Avg Letters Correct', 'collected_by': 'Collector'},
                text='mean',
                color_discrete_sequence=['#2ca02c'],
            )
            fig_top.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            st.plotly_chart(fig_top, use_container_width=True)

        with col_bot:
            fig_bot = px.bar(
                bot10, x='mean', y='collected_by', orientation='h',
                title=f"Bottom 10 — {grade}",
                labels={'mean': 'Avg Letters Correct', 'collected_by': 'Collector'},
                text='mean',
                color_discrete_sequence=['#d62728'],
            )
            fig_bot.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            st.plotly_chart(fig_bot, use_container_width=True)


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
    df_ecd = df[(df['language'] == 'ECD') & (df['grade'] != 'null')].copy()

    # Sidebar filters
    with st.sidebar:
        st.header("Filters")

        # Language filter (NMB tab)
        lang_options = ['All'] + sorted(df_nmb['language'].dropna().unique().tolist())
        selected_lang = st.selectbox("Language (NMB)", lang_options)

        # Grade filter — include all grades present in the data
        grade_options = ['All'] + [g for g in GRADE_ORDER if g in df['grade'].values]
        # Also include any grades not in GRADE_ORDER (e.g. 'null')
        extra = sorted(set(df['grade'].dropna().unique()) - set(GRADE_ORDER))
        grade_options += extra
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
    tab_nmb, tab_ecd = st.tabs(["Primary Schools", "ECDCs"])

    with tab_nmb:
        render_nmb_charts(df_nmb)

    with tab_ecd:
        render_ecd_charts(df_ecd)

    # Letter-level analysis (respects current filters)
    render_letter_analysis(df_nmb)

    # Outlier collector analysis (uses unfiltered df_nmb so all grades visible)
    df_nmb_all = df[df['language'].isin(['isiXhosa', 'English', 'Afrikaans'])].copy()
    render_collector_outliers(df_nmb_all)


main()
