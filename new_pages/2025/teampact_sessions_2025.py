import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timedelta    
import plotly.express as px
import plotly.graph_objects as go

print(f"DEBUG: Token check at startup: {bool(os.getenv('TEAMPACT_API_TOKEN'))}")
print(f"DEBUG: Token length: {len(os.getenv('TEAMPACT_API_TOKEN', ''))}")

# Add the project root to the path so we can import the API module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from api.teampact_session_api import fetch_and_save_data
from data.mentor_schools import mentors_to_schools

# ECD Classification
ecd_list = [
    "Bavumeleni ECD",
    "Emmanuel Day Care",
    "Green Apple ECD",
    "Ilitha Lethu Day Care",
    "Kids College ECD",
    "Libhongolwethu ECD",
    "Livuse ECD",
    "Lukhanyo ECD",
    "Njongozabantu Day Care",
    "Sakha Bantwana ECD",
    "Siyabulela Pre-School",
    "St Mary Magdelene ECD",
    "Thembalethu Day Care",
    "Msobomvu ECD",
    "Mzamomhle Edu-care",
    "Nceduluntu Edu-care",
    "Ekhaya Pre-School",
    "Future Angels ECD",
    "Koester Day Care",
    "Khusta ECD",
    "Rise and Shine ECD",
    "Arise and Shine ECD"
]

def get_school_type(program_name):
    """Classify programs as ECD or Primary School"""
    if program_name in ecd_list:
        return 'ECD'
    else:
        return 'Primary School'

def get_mentor(program_name):
    """Assign mentor based on school name"""
    for mentor, schools in mentors_to_schools.items():
        if program_name in schools:
            return mentor
    return 'Unknown'

def create_session_views(df):
    """Transform participant-level data into session-level views focusing on education assistant activity"""
    
    # Ensure we have datetime columns
    df['session_started_at'] = pd.to_datetime(df['session_started_at'])
    df['session_date'] = df['session_started_at'].dt.date
    df['session_hour'] = df['session_started_at'].dt.hour
    df['session_weekday'] = df['session_started_at'].dt.day_name()
    
    # 1. SESSIONS PER ASSISTANT PER DAY
    daily_sessions = df.groupby(['user_name', 'session_date', 'session_id']).first().reset_index()
    daily_summary = daily_sessions.groupby(['user_name', 'session_date']).agg({
        'session_id': 'count',
        'total_duration_minutes': 'sum',
        'attended_percentage': 'mean'
    }).round(1)
    daily_summary.columns = ['Sessions_Count', 'Total_Minutes', 'Avg_Attendance_Pct']
    daily_summary = daily_summary.reset_index()
    
    # 2. WEEKLY PATTERNS
    weekly_sessions = df.groupby(['user_name', 'session_weekday', 'session_id']).first().reset_index()
    weekly_summary = weekly_sessions.groupby(['user_name', 'session_weekday']).size().reset_index()
    weekly_summary.columns = ['user_name', 'session_weekday', 'session_count']
    
    # 3. ASSISTANT WORKLOAD SUMMARY
    assistant_summary = daily_summary.groupby('user_name').agg({
        'Sessions_Count': ['sum', 'mean', 'max'],
        'Total_Minutes': ['sum', 'mean'],
        'Avg_Attendance_Pct': 'mean'
    }).round(1)
    
    # Flatten column names
    assistant_summary.columns = [
        'Total_Sessions', 'Avg_Sessions_Per_Day', 'Max_Sessions_Per_Day',
        'Total_Minutes_Taught', 'Avg_Minutes_Per_Day', 'Overall_Avg_Attendance'
    ]
    assistant_summary = assistant_summary.reset_index()
    
    return daily_summary, weekly_summary, assistant_summary

def create_ea_activity_table(df):
    """Create EA activity table for past 10 weekdays"""
    
    # Get unique session dates and sort them
    df['session_date'] = pd.to_datetime(df['session_started_at']).dt.date
    df['session_datetime'] = pd.to_datetime(df['session_started_at'])
    
    # Filter to weekdays only (Monday=0, Sunday=6, so weekdays are 0-4)
    weekday_df = df[df['session_datetime'].dt.weekday < 5]
    unique_weekdays = sorted(weekday_df['session_date'].unique(), reverse=True)
    
    # Get the past 10 weekdays
    past_10_dates = unique_weekdays[:10]
    
    if len(past_10_dates) == 0:
        return pd.DataFrame()
    
    # Use the same logic as elsewhere in the code, but with weekday-filtered data
    daily_sessions = weekday_df.groupby(['user_name', 'session_date', 'session_id']).first().reset_index()
    
    # Count sessions per EA per day
    ea_daily_counts = daily_sessions.groupby(['user_name', 'session_date']).size().reset_index()
    ea_daily_counts.columns = ['user_name', 'session_date', 'session_count']
    
    # Create pivot table with past 10 dates as columns
    pivot_table = ea_daily_counts.pivot(index='user_name', columns='session_date', values='session_count')
    
    # Filter to only past 10 dates and reorder columns chronologically (most recent first)
    pivot_table = pivot_table.reindex(columns=past_10_dates, fill_value=0)
    
    # Add total column showing number of active days
    pivot_table['Total Active Days'] = (pivot_table > 0).sum(axis=1)
    
    # Sort by total active days descending
    pivot_table = pivot_table.sort_values('Total Active Days', ascending=False)
    
    return pivot_table

def display_session_analysis(df):
    """Display comprehensive session analysis dashboard"""
    
    # Calculate 7-day cutoff
    max_date = pd.to_datetime(df['session_started_at']).max()
    seven_days_ago = max_date - timedelta(days=7)
    df_7days = df[pd.to_datetime(df['session_started_at']) >= seven_days_ago]
    df_7days['session_date'] = pd.to_datetime(df_7days['session_started_at']).dt.date
    
    # UPDATED METRICS - PAST 7 DAYS ONLY (Moved to top)
    st.subheader("Session Overview Metrics - Past 7 Days")
    
    # Primary School metrics
    st.markdown("**Primary Schools**")
    df_primary_7days = df_7days[df_7days['school_type'] == 'Primary School']
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        primary_eas_active = df_primary_7days['user_name'].nunique()
        st.metric("School EAs Active 1+ Days", primary_eas_active)
    
    with col2:
        primary_ea_activity = df_primary_7days.groupby('user_name')['session_date'].nunique()
        primary_eas_3plus = (primary_ea_activity >= 3).sum()
        st.metric("School EAs Active 3+ Days", primary_eas_3plus)
    
    with col3:
        primary_sessions = df_primary_7days['session_id'].nunique()
        primary_avg_sessions = primary_sessions / primary_eas_active if primary_eas_active > 0 else 0
        st.metric("Avg Sessions per School EA", f"{primary_avg_sessions:.1f}")
    
    with col4:
        primary_schools = df_primary_7days['program_name'].nunique()
        st.metric("Schools Running", primary_schools)
    
    # ECD metrics
    st.markdown("**Early Childhood Development Centers**")
    df_ecd_7days = df_7days[df_7days['school_type'] == 'ECD']
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ecd_eas_active = df_ecd_7days['user_name'].nunique()
        st.metric("ECD EAs Active 1+ Days", ecd_eas_active)
    
    with col2:
        ecd_ea_activity = df_ecd_7days.groupby('user_name')['session_date'].nunique()
        ecd_eas_3plus = (ecd_ea_activity >= 3).sum()
        st.metric("ECD EAs Active 3+ Days", ecd_eas_3plus)
    
    with col3:
        ecd_sessions = df_ecd_7days['session_id'].nunique()
        ecd_avg_sessions = ecd_sessions / ecd_eas_active if ecd_eas_active > 0 else 0
        st.metric("Avg Sessions per ECD EA", f"{ecd_avg_sessions:.1f}")
    
    with col4:
        ecd_schools = df_ecd_7days['program_name'].nunique()
        st.metric("ECDs Running", ecd_schools)
    
    st.divider()

    # UNIQUE EAs BY SCHOOLS & ECDs - PAST 7 DAYS (Moved to top)
    st.subheader("Active EAs by Schools & ECDs - Past 7 Days")
    
    # Group by date and school type for unique EAs count
    daily_school_type_eas = df_7days.groupby(['session_date', 'school_type'])['user_name'].nunique().reset_index()
    daily_school_type_eas.columns = ['Date', 'School_Type', 'Active_EAs']
    
    if not daily_school_type_eas.empty:
        fig_school_type_eas = px.bar(
            daily_school_type_eas,
            x='Date',
            y='Active_EAs',
            color='School_Type',
            title="Daily Active EAs by Schools & ECDs (Past 7 Days)",
            labels={'Active_EAs': 'Number of Active EAs', 'Date': 'Date'}
        )
        st.plotly_chart(fig_school_type_eas, use_container_width=True)
    
    # SESSIONS BY SCHOOLS & ECDs - PAST 7 DAYS (Moved below)
    st.subheader("Total Sessions by Schools & ECDs - Past 7 Days")
    
    # Group by date and school type for sessions count
    daily_school_type_sessions = df_7days.groupby(['session_date', 'school_type'])['session_id'].nunique().reset_index()
    daily_school_type_sessions.columns = ['Date', 'School_Type', 'Sessions']
    
    if not daily_school_type_sessions.empty:
        fig_school_type_sessions = px.bar(
            daily_school_type_sessions,
            x='Date',
            y='Sessions',
            color='School_Type',
            title="Daily Sessions by Schools & ECDs (Past 7 Days)",
            labels={'Sessions': 'Number of Sessions', 'Date': 'Date'}
        )
        st.plotly_chart(fig_school_type_sessions, use_container_width=True)
    
    # Create the views
    daily_summary, weekly_summary, assistant_summary = create_session_views(df)
    
    # SCHOOL TYPE FILTER
    st.subheader("Filter by School Type")
    school_type_filter = st.selectbox(
        "Select School Type:",
        options=["All", "ECD", "Primary School"],
        index=0
    )
    
    # Apply filter
    if school_type_filter != "All":
        filtered_df = df[df['school_type'] == school_type_filter]
        st.info(f"Showing data for {school_type_filter} only ({len(filtered_df):,} records)")
    else:
        filtered_df = df
        st.info(f"Showing all school types ({len(filtered_df):,} records)")
    
    # Recalculate views with filtered data
    daily_summary_filtered, weekly_summary_filtered, assistant_summary_filtered = create_session_views(filtered_df)
    
    # EA WORKLOAD COMPARISON
    st.subheader("EA Workload Comparison")
    
    # Total sessions bar chart
    fig_total = px.bar(
        assistant_summary_filtered.sort_values('Total_Sessions', ascending=True),
        x='user_name',
        y='Total_Sessions',
        title=f"Total Sessions by EA ({school_type_filter})"
    )
    st.plotly_chart(fig_total, use_container_width=True)
    
        # Average daily sessions
    fig_avg = px.bar(
        assistant_summary_filtered.sort_values('Avg_Sessions_Per_Day', ascending=True),
        x='user_name',
        y='Avg_Sessions_Per_Day',
        title=f"Average Sessions per Day ({school_type_filter})"
    )
    st.plotly_chart(fig_avg, use_container_width=True)
    
    # EA ACTIVITY TABLE - PAST 10 WEEKDAYS
    st.subheader("EA Session Activity - Past 10 Weekdays")
    
    # School type filter for this section
    ea_school_type_filter = st.selectbox(
        "Filter by School Type:",
        options=["Primary School", "ECD", "All"],
        index=0,  # Default to Primary School
        key="ea_activity_filter"
    )
    
    # Apply filter for EA activity section
    if ea_school_type_filter != "All":
        ea_filtered_df = df[df['school_type'] == ea_school_type_filter]
    else:
        ea_filtered_df = df
    
    # Create the activity table
    activity_table = create_ea_activity_table(ea_filtered_df)
    
    if not activity_table.empty:
        # ACTIVE DAYS BREAKDOWN AND PIE CHART
        col1, col2 = st.columns([1, 1])
        
        with col1:
            filter_text = f" ({ea_school_type_filter})" if ea_school_type_filter != "All" else ""
            st.info(f"**Here's a breakdown of how many days each EA has worked over the past 10 weekdays{filter_text}.**")
            
            # Create breakdown of Total Active Days
            active_days_counts = activity_table['Total Active Days'].value_counts().sort_index(ascending=False)
            total_eas = len(activity_table)
            
            # Create breakdown table
            breakdown_df = pd.DataFrame({
                'No. of Days Worked': active_days_counts.index,
                'Counto of EAs': active_days_counts.values,
                'Percentage of EAs': (active_days_counts.values / total_eas * 100).round(1)
            })
            
            st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
        
        with col2:   
            
            st.info(f"**Charting the distribution of days worked by EAs (over the past 10 weekdays{filter_text}).**")         
            # Create work frequency categories
            def categorize_work_frequency(days):
                if days == 0:
                    return "0 days"
                elif 1 <= days <= 3:
                    return "1-3 days"
                elif 4 <= days <= 6:
                    return "4-6 days"
                else:
                    return "7+ days"
            
            # Apply categorization
            activity_table['Work_Category'] = activity_table['Total Active Days'].apply(categorize_work_frequency)
            category_counts = activity_table['Work_Category'].value_counts()
            
            # Create pie chart with custom colors
            chart_title = f"Days Worked Distribution by EAs{filter_text}"
            
            # Define color mapping
            color_map = {
                "0 days": "#FF0000",      # RED
                "1-3 days": "#FFB3B3",   # Light red
                "4-6 days": "#6495ED",   # Streamlit info blue
                "7+ days": "#0000FF"     # Dark blue
            }
            
            # Create ordered colors list based on category_counts index
            colors = [color_map.get(category, "#CCCCCC") for category in category_counts.index]
            
            fig_pie = px.pie(
                values=category_counts.values,
                names=category_counts.index,
                title=chart_title,
                color_discrete_sequence=colors
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        st.divider()
        
        st.markdown("**Number of sessions run by each EA on each weekday (Monday-Friday)**")
        st.dataframe(activity_table.drop('Work_Category', axis=1), use_container_width=True)
        
        # Add summary info
        active_weekdays = len([col for col in activity_table.columns if col not in ['Total Active Days', 'Work_Category']])
        summary_text = f"Showing {total_eas} Education Assistants across {active_weekdays} most recent weekdays"
        if ea_school_type_filter != "All":
            summary_text += f" ({ea_school_type_filter} only)"
        st.info(summary_text)
    else:
        st.warning("No session data available for the activity table.")
    

def display_data_quality(df):
    """Data quality and export section"""
    
    st.header("Data Quality & Export")
    
    # School type breakdown
    st.subheader("School Type Distribution")
    school_type_counts = df['school_type'].value_counts()
    
    col1, col2 = st.columns(2)
    with col1:
        fig_school_pie = px.pie(
            values=school_type_counts.values,
            names=school_type_counts.index,
            title="Sessions by School Type"
        )
        st.plotly_chart(fig_school_pie, use_container_width=True)
    
    with col2:
        st.dataframe(school_type_counts.to_frame('Count'), use_container_width=True)
    
    # Data Quality Check
    st.markdown("### Data Quality")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("**Missing Data:**")
        missing_data = df.isnull().sum()
        missing_data = missing_data[missing_data > 0]
        if len(missing_data) > 0:
            st.dataframe(missing_data.to_frame('Missing Count'))
        else:
            st.success("No missing data!")
    
    with col2:
        st.markdown("**Data Info:**")
        st.text(f"Total columns: {len(df.columns)}")
        st.text(f"Total rows: {len(df):,}")
        st.text(f"Date range: {df['session_started_at'].min()} to {df['session_started_at'].max()}")
    
    # Raw Data Preview
    with st.expander("View Raw Data", expanded=False):
        st.markdown(f"**Showing first 100 records out of {len(df):,} total**")
        st.dataframe(df.head(100), use_container_width=True)
    
    # Data Export
    st.markdown("### Data Export")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Full CSV",
            data=csv,
            file_name=f"teampact_sessions_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    with col2:
        file_info = f"Data last updated: {datetime.fromtimestamp(os.path.getmtime('data/latest.csv')).strftime('%Y-%m-%d %H:%M:%S')}"
        st.info(file_info)

# MAIN APP STARTS HERE
st.title("TeamPact Education Assistant Analytics")
st.markdown("Session tracking and curriculum analysis")

# Create columns for title and refresh button
col1, col2 = st.columns([4, 1])

with col2:
    if st.button("Refresh Data", type="primary"):
        with st.spinner("Fetching data from TeamPact API..."):
            success = fetch_and_save_data()
            if success:
                st.success("Data refreshed successfully!")
                st.rerun()
            else:
                st.error("Failed to fetch data. Check your API credentials.")

# Check if data file exists
if not os.path.exists('data/latest.csv'):
    st.warning("No data file found. Click 'Refresh Data' to fetch from API.")
    st.stop()

# Load the data
try:
    df = pd.read_csv('data/latest.csv')
    
    if len(df) == 0:
        st.warning("Data file is empty.")
        st.stop()
    
    # Add school type classification
    df['school_type'] = df['program_name'].apply(get_school_type)
    
    # Add mentor assignment
    df['mentor'] = df['program_name'].apply(get_mentor)
    
    # CREATE TABS FOR DIFFERENT VIEWS
    tab1, tab2 = st.tabs(["EA Sessions Analysis", "Data Quality"])
    
    with tab1:
        display_session_analysis(df)
    
    with tab2:
        display_data_quality(df)

except Exception as e:
    st.error(f"Error loading data: {e}")
    with st.expander("Error Details"):
        import traceback
        st.code(traceback.format_exc())