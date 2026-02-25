"""
2026 Mentor Visits Dashboard
Reads from 2026_mentor_visits.parquet (updated nightly).
Survey 824: Mentor Visit Tracker 2026 (ECD and Schools)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
from data_loader import load_mentor_visits_2026

# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def load_data():
    try:
        return load_mentor_visits_2026()
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading mentor visit data: {e}")
        return pd.DataFrame()


# ── Helpers ───────────────────────────────────────────────────────────────────

def yes_no_colors():
    return {'Yes': '#2E86AB', 'No': '#F24236'}


def normalize_rating(val):
    """Normalize Excellent/Good/Average/Poor and similar."""
    if pd.isna(val):
        return None
    v = str(val).lower().strip()
    if any(x in v for x in ["didn't observe", "did not observe", "could not observe", "n/a"]):
        return "Did not observe"
    if "excellent" in v:
        return "Excellent"
    if "good" in v:
        return "Good"
    if "average" in v or "fair" in v or "moderate" in v:
        return "Average"
    if "poor" in v:
        return "Poor"
    return str(val).strip()


def bar_chart(series, title, color_map=None):
    counts = series.dropna().value_counts().reset_index()
    counts.columns = ['Response', 'Count']
    kwargs = dict(x='Response', y='Count', text='Count', title=title)
    if color_map:
        kwargs['color'] = 'Response'
        kwargs['color_discrete_map'] = color_map
    fig = px.bar(counts, **kwargs)
    fig.update_traces(textposition='outside')
    return fig


# ── Dashboard ─────────────────────────────────────────────────────────────────

def display_dashboard(df):
    # ── Summary metrics ────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Visits", len(df))
    c2.metric("Mentors", df['mentor_name'].nunique())
    c3.metric("Schools", df['school_name'].nunique())
    c4.metric("EAs Observed", df['ea_name'].nunique())

    st.divider()

    # ── Visits per Mentor ──────────────────────────────────────────────────────
    st.subheader("Visits per Mentor")
    mentor_counts = df['mentor_name'].value_counts().reset_index()
    mentor_counts.columns = ['Mentor', 'Visits']
    fig = px.bar(mentor_counts, x='Mentor', y='Visits', text='Visits', title="Visits per Mentor")
    fig.update_traces(textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

    # ── Grouping ──────────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("EA Grouping Correct")
        if 'grouping_correct' in df.columns:
            st.plotly_chart(bar_chart(df['grouping_correct'], "EA Grouping Correct",
                                      yes_no_colors()), use_container_width=True)
    with col_b:
        st.subheader("Letter Tracker Correct")
        if 'letter_tracker_correct' in df.columns:
            st.plotly_chart(bar_chart(df['letter_tracker_correct'], "Letter Tracker Correct",
                                      yes_no_colors()), use_container_width=True)

    # ── Teaching at right level ────────────────────────────────────────────────
    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("Teaching Correct Letters")
        if 'teaching_correct_letters' in df.columns:
            st.plotly_chart(bar_chart(df['teaching_correct_letters'], "Teaching Correct Letters",
                                      yes_no_colors()), use_container_width=True)
    with col_d:
        st.subheader("Comment Section Usage")
        if 'comment_section_usage' in df.columns:
            st.plotly_chart(bar_chart(df['comment_section_usage'], "Comment Section Usage",
                                      yes_no_colors()), use_container_width=True)

    # ── Quality metrics ────────────────────────────────────────────────────────
    st.subheader("Session Quality & Engagement")
    q_cols = [
        ('learner_engagement', "Learner Engagement"),
        ('ea_energy_preparation', "EA Energy & Preparation"),
        ('session_quality', "Session Quality"),
        ('teacher_relationship', "EA-Teacher Relationship"),
    ]
    q_row = st.columns(2)
    for i, (col, label) in enumerate(q_cols):
        if col in df.columns:
            with q_row[i % 2]:
                norm_series = df[col].apply(normalize_rating)
                order = ['Excellent', 'Good', 'Average', 'Poor', 'Did not observe']
                norm_counts = norm_series.value_counts().reindex(order, fill_value=0).reset_index()
                norm_counts.columns = ['Response', 'Count']
                norm_counts = norm_counts[norm_counts['Count'] > 0]
                color_map = {
                    'Excellent': '#2ca02c',
                    'Good': '#1f77b4',
                    'Average': '#ff7f0e',
                    'Poor': '#d62728',
                    'Did not observe': '#aec7e8',
                }
                fig = px.bar(
                    norm_counts, x='Response', y='Count', text='Count',
                    title=label,
                    color='Response',
                    color_discrete_map=color_map,
                    category_orders={'Response': order},
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    # ── Sessions per day reported ──────────────────────────────────────────────
    if 'sessions_per_day' in df.columns:
        st.subheader("Sessions Per Day (as reported by EA)")
        st.plotly_chart(bar_chart(df['sessions_per_day'], "Sessions Per Day Reported"),
                        use_container_width=True)

    # ── Trouble getting children ───────────────────────────────────────────────
    if 'trouble_getting_children' in df.columns:
        st.subheader("Trouble Getting Children for Sessions")
        st.plotly_chart(bar_chart(df['trouble_getting_children'],
                                  "Trouble Getting Children", yes_no_colors()),
                        use_container_width=True)

    # ── School breakdown table ─────────────────────────────────────────────────
    st.subheader("School Summary")
    school_summary = df.groupby('school_name').agg(
        Visits=('response_id', 'count'),
        EAs=('ea_name', 'nunique'),
    ).reset_index().sort_values('Visits', ascending=False)
    school_summary.columns = ['School', 'Visits', 'EAs Observed']
    st.dataframe(school_summary, use_container_width=True, hide_index=True)

    # ── Raw data ───────────────────────────────────────────────────────────────
    with st.expander("All Visits Data"):
        show_cols = [
            'Response Date', 'mentor_name', 'school_name', 'ea_name', 'grade', 'class_name',
            'grouping_correct', 'letter_tracker_correct', 'teaching_correct_letters',
            'session_quality', 'learner_engagement', 'teacher_relationship',
            'additional_commentary',
        ]
        cols_present = [c for c in show_cols if c in df.columns]
        st.dataframe(df[cols_present], use_container_width=True)
        st.download_button(
            "Download CSV",
            data=df.to_csv(index=False),
            file_name="2026_mentor_visits.csv",
            mime="text/csv",
        )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    st.title("Mentor Visits — 2026")
    st.caption("Survey 824 — Mentor Visit Tracker 2026 (ECD and Schools). Updated nightly.")

    df = load_data()

    if df.empty:
        st.warning("No mentor visit data found. Data is updated nightly after `sync_mentor_visits_2026` runs.")
        st.stop()

    if 'response_start_at' in df.columns and df['response_start_at'].notna().any():
        last_refresh = df['response_start_at'].max()
        if pd.notna(last_refresh):
            st.caption(f"Most recent visit: {last_refresh.strftime('%Y-%m-%d')}")

    # ── Sidebar filters ────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Filters")
        mentor_opts = ['All'] + sorted(df['mentor_name'].dropna().unique().tolist())
        sel_mentor = st.selectbox("Mentor", mentor_opts)

        school_opts = ['All'] + sorted(df['school_name'].dropna().unique().tolist())
        sel_school = st.selectbox("School", school_opts)

    fdf = df.copy()
    if sel_mentor != 'All':
        fdf = fdf[fdf['mentor_name'] == sel_mentor]
    if sel_school != 'All':
        fdf = fdf[fdf['school_name'] == sel_school]

    if fdf.empty:
        st.info("No visits match the current filters.")
        return

    display_dashboard(fdf)


main()
