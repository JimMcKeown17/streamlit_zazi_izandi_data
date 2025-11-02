import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

# Ensure the project root is on the import path so we can import db_api_get_sessions
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import db_api_get_sessions as db  # Re-use existing data/DB logic


def show():
    # Authentication guard – consistent with other pages
    if 'user' not in st.session_state or st.session_state.user is None:
        st.error("Please log in to access this page")
        return

    st.title("📚 2025 Session Analysis")

    # Sidebar filters
    st.sidebar.header("Filters")
    date_filter = st.sidebar.date_input(
        "Sessions from date:",
        value=datetime.now() - timedelta(days=30),
        max_value=datetime.now(),
        key="session_date_filter_2025"
    )
    ta_filter = st.sidebar.text_input("Filter by TA name (partial match):", key="session_ta_filter_2025")

    # Load data
    with st.spinner("Loading data…"):
        sessions_df = db.get_ta_sessions(date_filter, ta_filter)
        summary_stats = db.get_summary_stats()
        ta_performance = db.get_ta_performance()
        daily_activity = db.get_daily_activity()

        # Fallback: if no rows returned and a date filter is applied, retry without the date filter
        if sessions_df.empty and date_filter:
            sessions_df = db.get_ta_sessions(None, ta_filter)

    if sessions_df.empty:
        st.warning("No sessions found with current filters.")
        return

    # Convert timestamps for convenience
    for col in ['completion_date', 'submission_date', 'start_time', 'end_time']:
        if col in sessions_df.columns:
            sessions_df[col] = pd.to_datetime(sessions_df[col])

    # ===== Overview Metrics =====
    st.header("📊 Overview")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sessions", f"{summary_stats['total_sessions'].iloc[0]:,}")
    with col2:
        st.metric("Unique Students", f"{summary_stats['unique_students'].iloc[0]:,}")
    with col3:
        st.metric("Unique TAs", f"{summary_stats['unique_tas'].iloc[0]:,}")
    with col4:
        avg_duration = summary_stats['avg_duration_minutes'].iloc[0]
        st.metric("Avg Duration", f"{avg_duration:.1f} min")

    col1, col2, col3 = st.columns(3)
    with col1:
        flash_card_pct = (summary_stats['flash_card_sessions'].iloc[0] / summary_stats['total_sessions'].iloc[0]) * 100
        st.metric("Flash Card Sessions", f"{flash_card_pct:.1f}%")
    with col2:
        board_game_pct = (summary_stats['board_game_sessions'].iloc[0] / summary_stats['total_sessions'].iloc[0]) * 100
        st.metric("Board Game Sessions", f"{board_game_pct:.1f}%")
    with col3:
        review_pct = (summary_stats['reviewed_sessions'].iloc[0] / summary_stats['total_sessions'].iloc[0]) * 100
        st.metric("Reviewed Sessions", f"{review_pct:.1f}%")

    # ===== Charts =====
    st.header("📈 Analytics")

    if not daily_activity.empty:
        daily_activity['session_date'] = pd.to_datetime(daily_activity['session_date'])
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Daily Session Volume")
            fig = px.line(daily_activity, x='session_date', y='daily_sessions', title="Sessions per Day")
            fig.update_layout(xaxis_title="Date", yaxis_title="Number of Sessions")
            st.plotly_chart(fig, width='stretch')
        with col2:
            st.subheader("Daily Average Duration")
            fig = px.line(daily_activity, x='session_date', y='avg_daily_duration', title="Average Session Duration per Day")
            fig.update_layout(xaxis_title="Date", yaxis_title="Duration (minutes)")
            st.plotly_chart(fig, width='stretch')

    # ===== TA Performance =====
    st.subheader("🎯 TA Performance")
    if not ta_performance.empty:
        col1, col2 = st.columns(2)
        with col1:
            top_tas = ta_performance.head(10)
            fig = px.bar(top_tas, x='session_count', y='ta_name', orientation='h', title="Sessions by TA")
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, width='stretch')
        with col2:
            fig = px.scatter(ta_performance, x='session_count', y='avg_duration', hover_data=['ta_name'], title="Duration vs Volume by TA")
            fig.update_layout(xaxis_title="Session Count", yaxis_title="Avg Duration (min)")
            st.plotly_chart(fig, width='stretch')

    # ===== Activity Analysis =====
    st.subheader("🎲 Activity Analysis")
    activity_summary = sessions_df.groupby(['flash_cards', 'board_game']).size().reset_index(name='count')
    activity_summary['activity_type'] = activity_summary.apply(
        lambda x: 'Flash Cards Only' if x['flash_cards'] and not x['board_game'] else (
            'Board Game Only' if not x['flash_cards'] and x['board_game'] else (
                'Both Activities' if x['flash_cards'] and x['board_game'] else 'Neither Activity'
            )
        ), axis=1
    )
    fig = px.pie(activity_summary, values='count', names='activity_type', title="Distribution of Session Activities")
    st.plotly_chart(fig, width='stretch')

    # ===== Recent Sessions Table =====
    st.header("📋 Recent Sessions")
    col1, col2 = st.columns(2)
    with col1:
        show_rows = st.selectbox("Rows to display:", [10, 25, 50, 100], index=1, key="session_rows")
    with col2:
        show_columns = st.multiselect(
            "Select columns to display:",
            options=sessions_df.columns.tolist(),
            default=['start_time', 'ta_name', 'username', 'duration', 'letters_worked_on', 'flash_cards', 'board_game'],
            key="session_columns"
        )
    if show_columns:
        display_df = sessions_df[show_columns].head(show_rows)
        st.dataframe(display_df, width='stretch')

    # ===== Export Buttons =====
    st.header("📥 Export Data")
    col1, col2 = st.columns(2)
    with col1:
        csv_sessions = sessions_df.to_csv(index=False)
        st.download_button(
            label="Download Session Data (CSV)",
            data=csv_sessions,
            file_name=f"ta_sessions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_sessions_csv"
        )
    with col2:
        csv_performance = ta_performance.to_csv(index=False)
        st.download_button(
            label="Download TA Performance (CSV)",
            data=csv_performance,
            file_name=f"ta_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            key="download_performance_csv"
        )

    # ===== Advanced Data Explorer =====
    with st.expander("🔍 Advanced Data Explorer"):
        st.subheader("Custom Query Builder")
        query_ta = st.selectbox("Filter by TA:", ['All'] + sorted(sessions_df['ta_name'].unique().tolist()), key="adv_query_ta")
        query_activity = st.selectbox("Activity type:", ['All', 'Flash Cards', 'Board Game', 'Both', 'Neither'], key="adv_query_activity")
        query_duration = st.slider("Min duration (minutes):", 0, 180, 0, key="adv_query_duration")

        filtered_df = sessions_df.copy()
        if query_ta != 'All':
            filtered_df = filtered_df[filtered_df['ta_name'] == query_ta]
        if query_activity != 'All':
            if query_activity == 'Flash Cards':
                filtered_df = filtered_df[filtered_df['flash_cards'] & ~filtered_df['board_game']]
            elif query_activity == 'Board Game':
                filtered_df = filtered_df[~filtered_df['flash_cards'] & filtered_df['board_game']]
            elif query_activity == 'Both':
                filtered_df = filtered_df[filtered_df['flash_cards'] & filtered_df['board_game']]
            elif query_activity == 'Neither':
                filtered_df = filtered_df[~filtered_df['flash_cards'] & ~filtered_df['board_game']]
        filtered_df = filtered_df[filtered_df['duration'] >= query_duration]
        st.write(f"Filtered results: {len(filtered_df)} sessions")
        if not filtered_df.empty:
            st.dataframe(filtered_df, width='stretch') 