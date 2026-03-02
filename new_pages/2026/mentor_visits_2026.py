"""
2026 Mentor Visits Dashboard
Reads from mentor_visits_2026 table (updated nightly).
Survey 824: Mentor Visit Tracker 2026 (ECD and Schools)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    if not v or v in ("", "n/a", "na"):
        return "Did not observe"
    if any(x in v for x in ["didn't observe", "did not observe", "could not observe",
                             "no sessions", "not observe", "i did not"]):
        return "Did not observe"
    if "excellent" in v:
        return "Excellent"
    if "very good" in v:
        return "Good"
    if "good" in v:
        return "Good"
    if "average" in v or "fair" in v or "moderate" in v:
        return "Average"
    if "poor" in v:
        return "Poor"
    # Free-text that doesn't match any category — treat as qualitative (skip for numeric)
    return None


def make_donut_chart(series, title):
    """Create a donut/pie chart showing % Yes vs No (handles compound values)."""
    # Normalize compound values like "Yes, Not Applicable" → "Yes"
    normalized = series.dropna().apply(extract_yes_no).dropna()
    normalized = normalized[normalized.isin(['Yes', 'No'])]
    counts = normalized.value_counts()
    if counts.empty:
        return None
    colors = yes_no_colors()
    fig = go.Figure(data=[go.Pie(
        labels=counts.index.tolist(),
        values=counts.values.tolist(),
        hole=0.45,
        marker_colors=[colors.get(label, '#999') for label in counts.index],
        textinfo='label+percent',
        textposition='outside',
    )])
    fig.update_layout(
        title=dict(text=title, x=0.5),
        showlegend=False,
        margin=dict(t=50, b=20, l=20, r=20),
        height=300,
    )
    return fig


def extract_yes_no(val):
    """Extract Yes/No from potentially compound values like 'No, Not Applicable'."""
    if pd.isna(val):
        return None
    v = str(val).strip()
    if not v:
        return None
    lower = v.lower()
    if lower.startswith("yes"):
        return "Yes"
    if lower.startswith("no"):
        return "No"
    return v


def get_flagged_eas(df, compliance_col, reason_col=None):
    """
    Find EAs whose most recent visit had a 'No' for the given compliance column.
    Returns a DataFrame with EA Name, School, Mentor, Visit Date, and optional reason.
    """
    if compliance_col not in df.columns:
        return pd.DataFrame()

    subset = df[df[compliance_col].str.strip() != ''].copy()
    if subset.empty:
        return pd.DataFrame()

    # Normalize compound values to Yes/No
    subset['_yn'] = subset[compliance_col].apply(extract_yes_no)

    # Sort by date descending, take the most recent per EA
    subset = subset.sort_values('Response Date', ascending=False)
    latest = subset.groupby('ea_name').first().reset_index()

    # Filter to those whose most recent answer was No
    flagged = latest[latest['_yn'] == 'No'].copy()

    if flagged.empty:
        return pd.DataFrame()

    cols = {
        'ea_name': 'EA Name',
        'school_name': 'School',
        'mentor_name': 'Mentor',
        'Response Date': 'Visit Date',
    }
    if reason_col and reason_col in flagged.columns:
        cols[reason_col] = 'Reason'

    result = flagged[[c for c in cols.keys() if c in flagged.columns]].rename(columns=cols)
    if 'Visit Date' in result.columns:
        result['Visit Date'] = pd.to_datetime(result['Visit Date'], errors='coerce').dt.strftime('%Y-%m-%d')
    return result.sort_values('EA Name')


# ── Compliance section builder ────────────────────────────────────────────────

def render_compliance_section(df, title, compliance_col, reason_col=None):
    """Render a donut chart + flagged EA table for a compliance question."""
    if compliance_col not in df.columns:
        return

    st.subheader(title)
    col_chart, col_table = st.columns([1, 2])

    with col_chart:
        fig = make_donut_chart(df[compliance_col], title)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available.")

    with col_table:
        flagged = get_flagged_eas(df, compliance_col, reason_col)
        if flagged.empty:
            st.success("All EAs are compliant (most recent visit = Yes).")
        else:
            st.warning(f"{len(flagged)} EA(s) flagged — most recent visit was **No**")
            st.dataframe(flagged, use_container_width=True, hide_index=True)


# ── Dashboard ─────────────────────────────────────────────────────────────────

def display_dashboard(df):
    # ── 1. Summary metrics ────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Visits", len(df))
    c2.metric("Mentors", df['mentor_name'].nunique())
    c3.metric("Schools", df['school_name'].nunique())
    c4.metric("EAs Observed", df['ea_name'].nunique())

    st.divider()

    # ── 2. Visits Over Time ───────────────────────────────────────────────────
    st.subheader("Visits Over Time")
    if 'Response Date' in df.columns and df['Response Date'].notna().any():
        time_df = df.copy()
        time_df['Week'] = time_df['Response Date'].dt.to_period('W').apply(lambda r: r.start_time)
        weekly = time_df.groupby('Week').size().reset_index(name='Visits')
        fig = px.bar(weekly, x='Week', y='Visits', text='Visits', title="Visits per Week")
        fig.update_traces(textposition='outside')
        fig.update_layout(xaxis_title="Week Starting", yaxis_title="Number of Visits")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No date information available for time chart.")

    st.divider()

    # ── 3. Visits per Mentor (stacked by school) ─────────────────────────────
    st.subheader("Visits per Mentor")
    mentor_school = df.groupby(['mentor_name', 'school_name']).size().reset_index(name='Visits')
    fig = px.bar(
        mentor_school,
        x='mentor_name', y='Visits', color='school_name',
        text='Visits', title="Visits per Mentor by School",
        labels={'mentor_name': 'Mentor', 'school_name': 'School'},
    )
    fig.update_traces(textposition='inside')
    fig.update_layout(
        xaxis_title="Mentor",
        yaxis_title="Visits",
        legend_title="School",
        barmode='stack',
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── 4. Compliance Checks ──────────────────────────────────────────────────
    st.header("Compliance Checks")

    # Map of (display title, column name, optional reason column)
    # Reason column names are guesses — guarded by `if col in df.columns`
    compliance_questions = [
        ("EA Grouping Correct", "grouping_correct", "grouping_incorrect_reason"),
        ("Letter Tracker Correct", "letter_tracker_correct", "letter_tracker_incorrect_reason"),
        ("Comment Section Usage", "comment_section_usage", None),
        ("Teaching Correct Letters", "teaching_correct_letters", "teaching_incorrect_reason"),
    ]

    # Check for mastery/blending column — try common names
    mastery_col = None
    for candidate in ['mastery_confirmed', 'mastery_before_blending', 'blending_mastery_confirmed']:
        if candidate in df.columns:
            mastery_col = candidate
            break

    if mastery_col:
        compliance_questions.append(("Mastery Confirmed Before Blending", mastery_col, None))

    for title, col, reason_col in compliance_questions:
        render_compliance_section(df, title, col, reason_col)

    st.divider()

    # ── 5. Session Quality & Engagement ───────────────────────────────────────
    st.header("Session Quality & Engagement")

    # Structured rating columns (single-select with Excellent/Good/Average/Poor)
    rating_cols = [
        ('session_quality', "Session Quality"),
        ('teacher_relationship', "EA-Teacher Relationship"),
    ]
    # Free-text qualitative columns — shown as summary tables instead of bar charts
    freetext_cols = [
        ('learner_engagement', "Learner Engagement"),
        ('ea_energy_preparation', "EA Energy & Preparation"),
    ]

    rating_order = ['Excellent', 'Good', 'Average', 'Poor', 'Did not observe']
    color_map = {
        'Excellent': '#2ca02c',
        'Good': '#1f77b4',
        'Average': '#ff7f0e',
        'Poor': '#d62728',
        'Did not observe': '#aec7e8',
    }

    # Rating bar charts
    q_row = st.columns(2)
    for i, (col, label) in enumerate(rating_cols):
        if col in df.columns:
            with q_row[i % 2]:
                norm_series = df[col].apply(normalize_rating).dropna()
                norm_counts = norm_series.value_counts().reindex(rating_order, fill_value=0).reset_index()
                norm_counts.columns = ['Response', 'Count']
                norm_counts = norm_counts[norm_counts['Count'] > 0]
                fig = px.bar(
                    norm_counts, x='Response', y='Count', text='Count',
                    title=label,
                    color='Response',
                    color_discrete_map=color_map,
                    category_orders={'Response': rating_order},
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

    # Per-mentor quality summary table
    rating_to_num = {'Excellent': 4, 'Good': 3, 'Average': 2, 'Poor': 1}
    present_rating_cols = [(col, label) for col, label in rating_cols if col in df.columns]
    if present_rating_cols:
        st.subheader("Quality Summary by Mentor")
        summary_rows = []
        for mentor, group in df.groupby('mentor_name'):
            row = {'Mentor': mentor, 'Visits': len(group)}
            for col, label in present_rating_cols:
                numeric = group[col].apply(normalize_rating).map(rating_to_num)
                mean_val = numeric.mean()
                row[label] = f"{mean_val:.1f}" if pd.notna(mean_val) else "—"
            summary_rows.append(row)
        summary_df = pd.DataFrame(summary_rows).sort_values('Visits', ascending=False)
        st.caption("Ratings: 4 = Excellent, 3 = Good, 2 = Average, 1 = Poor")
        st.dataframe(summary_df, use_container_width=True, hide_index=True)

    # Free-text qualitative fields — show as raw comment tables
    for col, label in freetext_cols:
        if col in df.columns:
            comments = df[df[col].str.strip().isin(['', 'N/A', 'n/a', 'Not Applicable']) == False][[
                'mentor_name', 'school_name', 'ea_name', col
            ]].copy()
            comments = comments[comments[col].str.strip() != '']
            if not comments.empty:
                with st.expander(f"{label} — Mentor Notes ({len(comments)} comments)"):
                    comments.columns = ['Mentor', 'School', 'EA', label]
                    st.dataframe(comments, use_container_width=True, hide_index=True)

    st.divider()

    # ── 6. Sessions per day & Trouble Getting Children ────────────────────────
    col_e, col_f = st.columns(2)
    with col_e:
        if 'sessions_per_day' in df.columns:
            st.subheader("Sessions Per Day (reported by EA)")
            counts = df['sessions_per_day'].dropna().value_counts().reset_index()
            counts.columns = ['Response', 'Count']
            fig = px.bar(counts, x='Response', y='Count', text='Count', title="Sessions Per Day Reported")
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

    with col_f:
        if 'trouble_getting_children' in df.columns:
            st.subheader("Trouble Getting Children")
            counts = df['trouble_getting_children'].dropna().value_counts().reset_index()
            counts.columns = ['Response', 'Count']
            fig = px.bar(counts, x='Response', y='Count', text='Count',
                         title="Trouble Getting Children", color='Response',
                         color_discrete_map=yes_no_colors())
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # ── 7. School Summary ─────────────────────────────────────────────────────
    st.subheader("School Summary")
    school_summary = df.groupby('school_name').agg(
        Visits=('response_id', 'count'),
        EAs=('ea_name', 'nunique'),
    ).reset_index().sort_values('Visits', ascending=False)
    school_summary.columns = ['School', 'Visits', 'EAs Observed']
    st.dataframe(school_summary, use_container_width=True, hide_index=True)

    # ── 8. Raw data ───────────────────────────────────────────────────────────
    with st.expander("All Visits Data"):
        show_cols = [
            'Response Date', 'mentor_name', 'school_name', 'ea_name', 'grade', 'class_name',
            'grouping_correct', 'letter_tracker_correct', 'teaching_correct_letters',
            'comment_section_usage', 'session_quality', 'learner_engagement',
            'ea_energy_preparation', 'teacher_relationship',
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
