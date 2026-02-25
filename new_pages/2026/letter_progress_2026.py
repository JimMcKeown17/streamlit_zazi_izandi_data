"""
2026 Letter Progress Dashboard
Reads from 2026 sessions parquet (updated nightly) and computes letter
progress per school, grade, TA, and group.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
from data_loader import load_sessions_2026

LETTER_SEQUENCE = [
    'a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p',
    's', 'h', 'z', 'n', 'd', 'y', 'f', 'w', 'v', 'x',
    'g', 't', 'q', 'r', 'c', 'j'
]


def detect_grade_from_class_name(class_name):
    if not class_name:
        return 'Unknown'
    g = str(class_name).strip()
    if (g.startswith('1 ') or g.startswith('1A') or g.startswith('1B') or
            g.startswith('1C') or g.startswith('1D') or g.startswith('1E') or
            g.startswith('1F') or 'Grade 1' in g):
        return 'Grade 1'
    if (g.startswith('2 ') or g.startswith('2A') or g.startswith('2B') or
            g.startswith('2C') or g.startswith('2D') or 'Grade 2' in g):
        return 'Grade 2'
    if (g.startswith('R ') or g.startswith('R A') or g.startswith('R B') or
            g.startswith('R C') or g.startswith('PreR') or 'Grade R' in g):
        return 'Grade R'
    return 'Unknown'


def letters_to_progress(letters_str):
    """Return (progress_index 0-25, progress_pct, rightmost_letter)."""
    if not letters_str or str(letters_str).strip() == '':
        return -1, 0.0, None
    parts = [l.strip().lower() for l in str(letters_str).split(',') if l.strip()]
    max_idx = -1
    rightmost = None
    for l in parts:
        if l in LETTER_SEQUENCE:
            idx = LETTER_SEQUENCE.index(l)
            if idx > max_idx:
                max_idx = idx
                rightmost = l
    pct = ((max_idx + 1) / len(LETTER_SEQUENCE)) * 100 if max_idx >= 0 else 0.0
    return max_idx, pct, rightmost


@st.cache_data(ttl=3600)
def build_progress_table():
    """
    Build a group-level progress table from 2026 sessions parquet.
    One row per (school, ta, group) with the most recent letter progress.
    """
    df = load_sessions_2026()
    df = df[df['letters_taught'].notna() & (df['letters_taught'] != '')]

    # Most recent session per (school, ta, group)
    df['session_started_at'] = pd.to_datetime(df['session_started_at'], errors='coerce')
    df = df.sort_values('session_started_at', ascending=False)
    latest = df.drop_duplicates(subset=['program_name', 'user_name', 'class_name'], keep='first').copy()

    # Compute progress
    latest[['progress_index', 'progress_pct', 'current_letter']] = latest['letters_taught'].apply(
        lambda s: pd.Series(letters_to_progress(s))
    )

    # Detect grade
    latest['grade'] = latest['class_name'].apply(detect_grade_from_class_name)

    latest['session_count'] = latest.groupby(['program_name', 'user_name', 'class_name'])['session_id'].transform('count')

    return latest[[
        'program_name', 'user_name', 'class_name', 'grade',
        'progress_index', 'progress_pct', 'current_letter', 'session_started_at',
        'school_type', 'mentor',
    ]].rename(columns={
        'program_name': 'School',
        'user_name': 'TA',
        'class_name': 'Group',
        'grade': 'Grade',
        'progress_index': 'Progress Index',
        'progress_pct': 'Progress %',
        'current_letter': 'Current Letter',
        'session_started_at': 'Last Session',
        'school_type': 'School Type',
        'mentor': 'Mentor',
    })


def main():
    st.title("📊 Letter Progress — 2026")
    st.caption("Most recent letter progress per group. Data updated nightly from 2026 sessions parquet.")

    try:
        df = build_progress_table()
    except FileNotFoundError:
        st.warning("2026 sessions parquet not found yet. It is created nightly after the first sync runs.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

    if df.empty:
        st.info("No session data with letter information found yet.")
        return

    # ── Sidebar filters ────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Filters")

        mentor_options = ['All'] + sorted(df['Mentor'].dropna().unique().tolist())
        selected_mentor = st.selectbox("Mentor", mentor_options)

        school_type_options = ['All'] + sorted(df['School Type'].dropna().unique().tolist())
        selected_type = st.selectbox("School Type", school_type_options)

        grade_options = ['All', 'Grade R', 'Grade 1', 'Grade 2', 'Unknown']
        selected_grade = st.selectbox("Grade", grade_options)

    fdf = df.copy()
    if selected_mentor != 'All':
        fdf = fdf[fdf['Mentor'] == selected_mentor]
    if selected_type != 'All':
        fdf = fdf[fdf['School Type'] == selected_type]
    if selected_grade != 'All':
        fdf = fdf[fdf['Grade'] == selected_grade]

    # ── Summary metrics ────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Schools", fdf['School'].nunique())
    c2.metric("TAs", fdf['TA'].nunique())
    c3.metric("Groups", len(fdf))
    avg_pct = fdf['Progress %'].mean()
    c4.metric("Avg Progress", f"{avg_pct:.1f}%")

    st.divider()

    # ── Progress by Grade ──────────────────────────────────────────────────────
    st.subheader("Average Progress by Grade")
    grade_summary = (
        fdf[fdf['Grade'] != 'Unknown']
        .groupby('Grade')['Progress %']
        .agg(['mean', 'median', 'count'])
        .reset_index()
    )
    grade_summary.columns = ['Grade', 'Mean %', 'Median %', 'Groups']
    grade_summary[['Mean %', 'Median %']] = grade_summary[['Mean %', 'Median %']].round(1)
    grade_order = ['Grade R', 'Grade 1', 'Grade 2']
    grade_summary['_order'] = grade_summary['Grade'].map({g: i for i, g in enumerate(grade_order)})
    grade_summary = grade_summary.sort_values('_order').drop(columns=['_order'])

    fig = px.bar(
        grade_summary, x='Grade', y='Mean %', text='Mean %',
        title="Mean Letter Progress % by Grade",
        color='Grade',
        category_orders={'Grade': grade_order},
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(yaxis_range=[0, 105], showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(grade_summary, use_container_width=True, hide_index=True)

    # ── Progress by School ─────────────────────────────────────────────────────
    st.subheader("Progress by School")
    school_summary = (
        fdf.groupby('School')
        .agg(
            Groups=('Group', 'count'),
            TAs=('TA', 'nunique'),
            Mean_Pct=('Progress %', 'mean'),
            Median_Pct=('Progress %', 'median'),
        )
        .reset_index()
        .sort_values('Mean_Pct', ascending=False)
    )
    school_summary[['Mean_Pct', 'Median_Pct']] = school_summary[['Mean_Pct', 'Median_Pct']].round(1)
    school_summary.columns = ['School', 'Groups', 'TAs', 'Mean Progress %', 'Median Progress %']

    fig2 = px.bar(
        school_summary.head(30), x='Mean Progress %', y='School',
        orientation='h',
        title="Mean Letter Progress % by School (top 30)",
        text='Mean Progress %',
    )
    fig2.update_traces(texttemplate='%{text:.1f}%')
    fig2.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
    st.plotly_chart(fig2, use_container_width=True)

    # ── Detailed group table ───────────────────────────────────────────────────
    st.subheader("Group-Level Detail")
    display_cols = ['School', 'TA', 'Group', 'Grade', 'Current Letter', 'Progress %', 'Last Session', 'Mentor']
    cols_present = [c for c in display_cols if c in fdf.columns]
    display_df = fdf[cols_present].sort_values(['School', 'TA', 'Group'])
    display_df['Progress %'] = display_df['Progress %'].round(1)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    csv = display_df.to_csv(index=False)
    st.download_button(
        "Download Group Progress CSV",
        data=csv,
        file_name="2026_letter_progress.csv",
        mime="text/csv",
    )


main()
