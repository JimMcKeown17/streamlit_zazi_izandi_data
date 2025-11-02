import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Database connection function
@st.cache_resource
def init_connection():
    return psycopg2.connect(
        host=st.secrets["postgres"]["host"],
        database=st.secrets["postgres"]["database"],
        user=st.secrets["postgres"]["user"],
        password=st.secrets["postgres"]["password"],
        port=st.secrets["postgres"]["port"],
        sslmode='require'
    )

# Function to run queries
@st.cache_data(ttl=600)  # Cache for 10 minutes
def run_query(query):
    conn = init_connection()
    df = pd.read_sql_query(query, conn)
    return df

# Get TA session data with optional filters
@st.cache_data(ttl=300)
def get_ta_sessions(date_filter=None, ta_filter=None, limit=5000):
    base_query = """
    SELECT 
        id, key, completion_date, submission_date, start_time, end_time,
        duration, username, device_id, device_info, ta_name, ta_name_name, 
        ta_name_id, group_number, letters_worked_on, flash_cards, board_game,
        comments, review_quality, review_status, ta_profile_id
    FROM api_tasession
    """
    
    conditions = []
    if date_filter:
        conditions.append(f"start_time >= '{date_filter}'")
    if ta_filter:
        conditions.append(f"ta_name ILIKE '%{ta_filter}%'")
    
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    
    base_query += f" ORDER BY start_time DESC LIMIT {limit}"
    
    return run_query(base_query)

# Get summary statistics
@st.cache_data(ttl=600)
def get_summary_stats():
    query = """
    SELECT 
        COUNT(*) as total_sessions,
        COUNT(DISTINCT username) as unique_students,
        COUNT(DISTINCT ta_name) as unique_tas,
        AVG(duration) as avg_duration_minutes,
        SUM(CASE WHEN flash_cards THEN 1 ELSE 0 END) as flash_card_sessions,
        SUM(CASE WHEN board_game THEN 1 ELSE 0 END) as board_game_sessions,
        COUNT(CASE WHEN review_quality IS NOT NULL THEN 1 END) as reviewed_sessions
    FROM api_tasession
    """
    return run_query(query)

# Get TA performance data
@st.cache_data(ttl=600)
def get_ta_performance():
    query = """
    SELECT 
        ta_name,
        COUNT(*) as session_count,
        AVG(duration) as avg_duration,
        SUM(CASE WHEN flash_cards THEN 1 ELSE 0 END) as flash_card_sessions,
        SUM(CASE WHEN board_game THEN 1 ELSE 0 END) as board_game_sessions,
        COUNT(CASE WHEN review_quality = 'excellent' THEN 1 END) as excellent_reviews,
        COUNT(CASE WHEN review_quality = 'good' THEN 1 END) as good_reviews,
        COUNT(CASE WHEN review_quality = 'poor' THEN 1 END) as poor_reviews
    FROM api_tasession
    GROUP BY ta_name
    ORDER BY session_count DESC
    """
    return run_query(query)

# Get daily activity
@st.cache_data(ttl=600)
def get_daily_activity():
    query = """
    SELECT 
        DATE(start_time) as session_date,
        COUNT(*) as daily_sessions,
        AVG(duration) as avg_daily_duration,
        COUNT(DISTINCT username) as unique_students_daily
    FROM api_tasession
    WHERE start_time IS NOT NULL
    GROUP BY DATE(start_time)
    ORDER BY session_date DESC
    LIMIT 30
    """
    return run_query(query)

def main():
    st.set_page_config(page_title="TA Session Analytics", layout="wide")
    st.title("📚 TA Session Analytics Dashboard")
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Date filter
    date_filter = st.sidebar.date_input(
        "Sessions from date:",
        value=datetime.now() - timedelta(days=30),
        max_value=datetime.now()
    )
    
    # TA filter
    ta_filter = st.sidebar.text_input("Filter by TA name (partial match):")
    
    # Load data
    with st.spinner("Loading data..."):
        sessions_df = get_ta_sessions(date_filter, ta_filter)
        summary_stats = get_summary_stats()
        ta_performance = get_ta_performance()
        daily_activity = get_daily_activity()
    
    if sessions_df.empty:
        st.warning("No sessions found with current filters.")
        return
    
    # Convert timestamps
    for col in ['completion_date', 'submission_date', 'start_time', 'end_time']:
        if col in sessions_df.columns:
            sessions_df[col] = pd.to_datetime(sessions_df[col])
    
    # Summary metrics
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
    
    # Activity metrics
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
    
    # Charts
    st.header("📈 Analytics")
    
    # Daily activity chart
    if not daily_activity.empty:
        daily_activity['session_date'] = pd.to_datetime(daily_activity['session_date'])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Daily Session Volume")
            fig = px.line(daily_activity, x='session_date', y='daily_sessions', 
                         title="Sessions per Day")
            fig.update_layout(xaxis_title="Date", yaxis_title="Number of Sessions")
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            st.subheader("Daily Average Duration")
            fig = px.line(daily_activity, x='session_date', y='avg_daily_duration',
                         title="Average Session Duration per Day")
            fig.update_layout(xaxis_title="Date", yaxis_title="Duration (minutes)")
            st.plotly_chart(fig, width='stretch')
    
    # TA Performance
    st.subheader("🎯 TA Performance")
    if not ta_performance.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Top TAs by session count
            top_tas = ta_performance.head(10)
            fig = px.bar(top_tas, x='session_count', y='ta_name', 
                        orientation='h', title="Sessions by TA")
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, width='stretch')
        
        with col2:
            # Average duration by TA
            fig = px.scatter(ta_performance, x='session_count', y='avg_duration',
                           hover_data=['ta_name'], title="Duration vs Volume by TA")
            fig.update_layout(xaxis_title="Session Count", yaxis_title="Avg Duration (min)")
            st.plotly_chart(fig, width='stretch')
    
    # Activity analysis
    if not sessions_df.empty:
        st.subheader("🎲 Activity Analysis")
        
        # Create activity summary
        activity_summary = sessions_df.groupby(['flash_cards', 'board_game']).size().reset_index(name='count')
        activity_summary['activity_type'] = activity_summary.apply(
            lambda x: 'Flash Cards Only' if x['flash_cards'] and not x['board_game']
            else 'Board Game Only' if not x['flash_cards'] and x['board_game']
            else 'Both Activities' if x['flash_cards'] and x['board_game']
            else 'Neither Activity', axis=1
        )
        
        fig = px.pie(activity_summary, values='count', names='activity_type',
                    title="Distribution of Session Activities")
        st.plotly_chart(fig, width='stretch')
    
    # Recent sessions table
    st.header("📋 Recent Sessions")
    
    # Display options
    col1, col2 = st.columns(2)
    with col1:
        show_rows = st.selectbox("Rows to display:", [10, 25, 50, 100], index=1)
    with col2:
        show_columns = st.multiselect(
            "Select columns to display:",
            options=sessions_df.columns.tolist(),
            default=['start_time', 'ta_name', 'username', 'duration', 'letters_worked_on', 'flash_cards', 'board_game']
        )
    
    if show_columns:
        display_df = sessions_df[show_columns].head(show_rows)
        st.dataframe(display_df, width='stretch')
    
    # Export data
    st.header("📥 Export Data")
    col1, col2 = st.columns(2)
    
    with col1:
        # Export filtered sessions
        csv_sessions = sessions_df.to_csv(index=False)
        st.download_button(
            label="Download Session Data (CSV)",
            data=csv_sessions,
            file_name=f"ta_sessions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Export TA performance
        csv_performance = ta_performance.to_csv(index=False)
        st.download_button(
            label="Download TA Performance (CSV)",
            data=csv_performance,
            file_name=f"ta_performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    # Raw data explorer
    with st.expander("🔍 Advanced Data Explorer"):
        st.subheader("Custom Query Builder")
        
        # Simple query builder
        col1, col2, col3 = st.columns(3)
        with col1:
            query_ta = st.selectbox("Filter by TA:", ['All'] + sorted(sessions_df['ta_name'].unique().tolist()))
        with col2:
            query_activity = st.selectbox("Activity type:", ['All', 'Flash Cards', 'Board Game', 'Both', 'Neither'])
        with col3:
            query_duration = st.slider("Min duration (minutes):", 0, 180, 0)
        
        # Apply filters
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

if __name__ == "__main__":
    main()