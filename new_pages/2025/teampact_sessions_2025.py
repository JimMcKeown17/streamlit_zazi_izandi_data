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

# DataQuest Schools Filter List
selected_schools_list = [
    "Aaron Gqadu Primary School",
    "Ben Sinuka Primary School",
    "Coega Primary School",
    "Dumani Primary School",
    "Ebongweni Public Primary School",
    "Elufefeni Primary School",
    "Empumalanga Primary School",
    "Enkululekweni Primary School",
    "Esitiyeni Public Primary School",
    "Fumisukoma Primary School",
    "Ilinge Primary School",
    "Isaac Booi Senior Primary School",
    "James Ntungwana Primary School",
    "Jarvis Gqamlana Public Primary School",
    "Joe Slovo Primary School",
    "Little Flower Primary School",
    "Magqabi Primary School",
    "Mjuleni Junior Primary School",
    "Mngcunube Primary School",
    "Molefe Senior Primary School",
    "Noninzi Luzipho Primary School",
    "Ntlemeza Primary School",
    "Phindubuye Primary School",
    "Seyisi Primary School",
    "Sikhothina Primary School",
    "Soweto-On-Sea Primary School",
    "Stephen Nkomo Senior Primary School",
    "W B Tshume Primary School"
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
    col1, col2, col3, col4, col5 = st.columns(5)
    
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
        # Count schools where EAs have been active 3+ days
        primary_ea_activity = df_primary_7days.groupby('user_name')['session_date'].nunique()
        primary_eas_3plus_users = primary_ea_activity[primary_ea_activity >= 3].index
        primary_schools_3plus = df_primary_7days[df_primary_7days['user_name'].isin(primary_eas_3plus_users)]['program_name'].nunique()
        st.metric("Schools Running 3+ Days", primary_schools_3plus)
    
    with col5:
        # Count schools where any EA has been active 1+ days
        primary_schools_1plus = df_primary_7days['program_name'].nunique()
        st.metric("Schools Running 1+ Days", primary_schools_1plus)
    
    # ECD metrics
    st.markdown("**Early Childhood Development Centers**")
    df_ecd_7days = df_7days[df_7days['school_type'] == 'ECD']
    col1, col2, col3, col4, col5 = st.columns(5)
    
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
        # Count ECDs where EAs have been active 3+ days
        ecd_ea_activity = df_ecd_7days.groupby('user_name')['session_date'].nunique()
        ecd_eas_3plus_users = ecd_ea_activity[ecd_ea_activity >= 3].index
        ecd_schools_3plus = df_ecd_7days[df_ecd_7days['user_name'].isin(ecd_eas_3plus_users)]['program_name'].nunique()
        st.metric("ECDs Running 3+ Days", ecd_schools_3plus)
    
    with col5:
        # Count ECDs where any EA has been active 1+ days
        ecd_schools_1plus = df_ecd_7days['program_name'].nunique()
        st.metric("ECDs Running 1+ Days", ecd_schools_1plus)
    
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
    
    # SESSIONS BY SCHOOLS & ECDs - PAST 30 DAYS (Moved below)
    st.subheader("Total Sessions by Schools & ECDs - Past 30 Days")
    
    # Calculate 30-day cutoff
    thirty_days_ago = max_date - timedelta(days=30)
    df_30days = df[pd.to_datetime(df['session_started_at']) >= thirty_days_ago]
    df_30days['session_date'] = pd.to_datetime(df_30days['session_started_at']).dt.date
    
    # Group by date and school type for sessions count
    daily_school_type_sessions = df_30days.groupby(['session_date', 'school_type'])['session_id'].nunique().reset_index()
    daily_school_type_sessions.columns = ['Date', 'School_Type', 'Sessions']
    
    if not daily_school_type_sessions.empty:
        fig_school_type_sessions = px.line(
            daily_school_type_sessions,
            x='Date',
            y='Sessions',
            color='School_Type',
            title="Daily Sessions by Schools & ECDs (Past 30 Days)",
            labels={'Sessions': 'Number of Sessions', 'Date': 'Date'},
            markers=True
        )
        st.plotly_chart(fig_school_type_sessions, use_container_width=True)
    
    # ACTIVE EAs (3+ DAYS) TREND - PAST 30 DAYS
    st.subheader("Active EAs (3+ Days) Trend - Past 30 Days")
    
    # Calculate active EAs (3+ days) for each day over past 30 days
    df_with_date = df.copy()
    df_with_date['session_date'] = pd.to_datetime(df_with_date['session_started_at']).dt.date
    
    # Get all unique dates in the past 30 days
    all_dates = pd.date_range(start=thirty_days_ago.date(), end=max_date.date(), freq='D').date
    
    active_ea_trend_data = []
    
    for current_date in all_dates:
        # Calculate 7-day window ending on current_date
        seven_days_before = current_date - timedelta(days=6)  # 6 days before + current day = 7 days
        
        # Filter data to this 7-day window
        window_data = df_with_date[
            (df_with_date['session_date'] >= seven_days_before) & 
            (df_with_date['session_date'] <= current_date)
        ]
        
        if not window_data.empty:
            # Count EAs active 3+ days in this window, by school type
            for school_type in ['Primary School', 'ECD']:
                school_data = window_data[window_data['school_type'] == school_type]
                if not school_data.empty:
                    ea_activity = school_data.groupby('user_name')['session_date'].nunique()
                    active_eas_count = (ea_activity >= 3).sum()
                else:
                    active_eas_count = 0
                
                active_ea_trend_data.append({
                    'Date': current_date,
                    'School_Type': school_type,
                    'Active_EAs_3Plus': active_eas_count
                })
    
    if active_ea_trend_data:
        active_ea_trend_df = pd.DataFrame(active_ea_trend_data)
        
        fig_active_ea_trend = px.line(
            active_ea_trend_df,
            x='Date',
            y='Active_EAs_3Plus',
            color='School_Type',
            title="Daily Count of Active EAs (3+ Days) - Past 30 Days",
            labels={'Active_EAs_3Plus': 'Number of Active EAs (3+ Days)', 'Date': 'Date'},
            markers=True
        )
        st.plotly_chart(fig_active_ea_trend, use_container_width=True)
        
        st.info("📊 **Note**: For each day, we count EAs who were active 3+ days within the 7-day period ending on that day.")
    
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
    
    # Create two columns for the filters
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        # School type filter for this section
        ea_school_type_filter = st.selectbox(
            "Filter by School Type:",
            options=["Primary School", "ECD", "All"],
            index=0,  # Default to Primary School
            key="ea_activity_filter"
        )
    
    with filter_col2:
        # Mentor filter for this section
        mentor_options = ["All mentors"] + list(mentors_to_schools.keys())
        ea_mentor_filter = st.selectbox(
            "Filter by Mentor:",
            options=mentor_options,
            index=0,  # Default to All mentors
            key="ea_mentor_filter"
        )
    
    # Apply filters for EA activity section
    ea_filtered_df = df.copy()
    
    if ea_school_type_filter != "All":
        ea_filtered_df = ea_filtered_df[ea_filtered_df['school_type'] == ea_school_type_filter]
    
    if ea_mentor_filter != "All mentors":
        ea_filtered_df = ea_filtered_df[ea_filtered_df['mentor'] == ea_mentor_filter]
    
    # Create the activity table
    activity_table = create_ea_activity_table(ea_filtered_df)
    
    if not activity_table.empty:
        # ACTIVE DAYS BREAKDOWN AND PIE CHART
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Create filter text for display
            filter_parts = []
            if ea_school_type_filter != "All":
                filter_parts.append(ea_school_type_filter)
            if ea_mentor_filter != "All mentors":
                filter_parts.append(f"Mentor: {ea_mentor_filter}")
            
            filter_text = f" ({', '.join(filter_parts)})" if filter_parts else ""
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
        if filter_parts:
            summary_text += f" ({', '.join(filter_parts)} only)"
        st.info(summary_text)
    else:
        st.warning("No session data available for the activity table.")
    

def load_ea_implementation_data():
    """Load EA implementation data from Excel file"""
    try:
        excel_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                 'data', 'EAs Implemeting (2).xlsx')
        
        # Load the Excel file
        df_excel = pd.read_excel(excel_path)
        
        # Standardize column names to handle any variations
        df_excel.columns = df_excel.columns.str.strip()
        
        # Convert all columns to string to avoid Arrow serialization issues
        for col in df_excel.columns:
            df_excel[col] = df_excel[col].astype(str)
        
        # Clean up 'nan' values that result from astype(str) conversion
        df_excel = df_excel.replace('nan', '')
        
        return df_excel
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return pd.DataFrame()

def calculate_teampact_sessions(df, user_name):
    """Calculate session metrics for a specific user"""
    user_data = df[df['user_name'] == user_name]
    
    if user_data.empty:
        return {'sessions_last_10_days': 0, 'sessions_total': 0}
    
    # Calculate sessions in last 10 weekdays
    user_data['session_date'] = pd.to_datetime(user_data['session_started_at']).dt.date
    weekday_data = user_data[pd.to_datetime(user_data['session_started_at']).dt.weekday < 5]
    unique_weekdays = sorted(weekday_data['session_date'].unique(), reverse=True)
    past_10_dates = unique_weekdays[:10]
    
    if past_10_dates:
        last_10_days_data = weekday_data[weekday_data['session_date'].isin(past_10_dates)]
        sessions_last_10_days = last_10_days_data['session_id'].nunique()
    else:
        sessions_last_10_days = 0
    
    # Total sessions ever
    sessions_total = user_data['session_id'].nunique()
    
    return {
        'sessions_last_10_days': sessions_last_10_days,
        'sessions_total': sessions_total
    }

def create_ea_implementation_table(df_sessions, df_excel):
    """Create merged table of EA implementation data with TeamPact sessions"""
    
    if df_excel.empty:
        return pd.DataFrame()
    
    # Create the merged table
    merged_data = []
    
    for _, excel_row in df_excel.iterrows():
        name = excel_row.get('Name and Surname', '')
        
        # Calculate TeamPact session metrics for this user
        session_metrics = calculate_teampact_sessions(df_sessions, name)
        
        # Get mentor for this user - first try from sessions data, then from Excel mentor column
        user_sessions = df_sessions[df_sessions['user_name'] == name]
        mentor_from_sessions = user_sessions['mentor'].iloc[0] if not user_sessions.empty else ''
        
        # Try to get mentor from Excel 'Mentor' column, fallback to school-based mentor assignment
        excel_mentor = str(excel_row.get('Mentor', '')) if pd.notna(excel_row.get('Mentor', '')) else ''
        if not excel_mentor:
            # Use school-based mentor assignment as fallback
            school_name = excel_row.get('School', '')
            excel_mentor = get_mentor(school_name)
        
        # Use TeamPact mentor if available, otherwise use Excel mentor
        final_mentor = mentor_from_sessions if mentor_from_sessions else excel_mentor
        
        merged_row = {
            'Name and Surname': str(name) if pd.notna(name) else '',
            'School': str(excel_row.get('School', '')) if pd.notna(excel_row.get('School', '')) else '',
            'Training Status': str(excel_row.get('Training Status Flag', '')) if pd.notna(excel_row.get('Training Status Flag', '')) else '',
            'Grade R': str(excel_row.get('Grade R', '')) if pd.notna(excel_row.get('Grade R', '')) else '',
            'Grade 1': str(excel_row.get('Grade 1', '')) if pd.notna(excel_row.get('Grade 1', '')) else '',
            'Grade 2': str(excel_row.get('Grade 2', '')) if pd.notna(excel_row.get('Grade 2', '')) else '',
            'Reason For Not Having Sessions': str(excel_row.get('Reasons For Not Having Sessions On Teampact', '')) if pd.notna(excel_row.get('Reasons For Not Having Sessions On Teampact', '')) else '',
            'Reason if NOT Implementation': str(excel_row.get('Reason if NOT Implmementation', '')) if pd.notna(excel_row.get('Reason if NOT Implmementation', '')) else '',
            'Mentor Confirmed Implementation': str(excel_row.get('Mentor Confirmed Implimentation', '')) if pd.notna(excel_row.get('Mentor Confirmed Implimentation', '')) else '',
            'Sessions Last 10 Days': int(session_metrics['sessions_last_10_days']),
            'Total Sessions Ever': int(session_metrics['sessions_total']),
            'Mentor': str(final_mentor) if pd.notna(final_mentor) else 'Unknown'
        }
        
        merged_data.append(merged_row)
    
    return pd.DataFrame(merged_data)

def display_ea_implementation_analysis(df_sessions):
    """Display EA implementation analysis with Excel data merge"""
    
    st.subheader("EA Implementation Status & TeamPact Activity")
    
    # Load Excel data
    df_excel = load_ea_implementation_data()
    
    if df_excel.empty:
        st.error("Could not load EA implementation Excel file.")
        return
    
    # Show basic info about the Excel file
    st.info(f"Loaded {len(df_excel)} EAs from implementation tracking file.")
    
    # Create mentor filter
    mentor_options = ["All mentors"] + list(mentors_to_schools.keys())
    implementation_mentor_filter = st.selectbox(
        "Filter by Mentor:",
        options=mentor_options,
        index=0,
        key="implementation_mentor_filter"
    )
    
    # Create merged table
    merged_table = create_ea_implementation_table(df_sessions, df_excel)
    
    if merged_table.empty:
        st.warning("No data to display.")
        return
    
    # Apply mentor filter
    if implementation_mentor_filter != "All mentors":
        # Filter based on the mentor column (which combines TeamPact and Excel mentor data)
        filtered_table = merged_table[merged_table['Mentor'] == implementation_mentor_filter]
        st.info(f"Showing {len(filtered_table)} EAs for mentor: {implementation_mentor_filter}")
    else:
        filtered_table = merged_table
        st.info(f"Showing all {len(filtered_table)} EAs")
    
    # Display summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_eas = len(filtered_table)
        st.metric("Initial EAs", total_eas)
    
    with col2:
        active_last_10 = (filtered_table['Sessions Last 10 Days'] > 0).sum()
        st.metric("EAs Active Last 10 Days", active_last_10)
    
    with col3:
        # Calculate average sessions per day across all EAs (total sessions / (EAs * 10 days))
        total_sessions_last_10 = filtered_table['Sessions Last 10 Days'].sum()
        avg_sessions_per_day = total_sessions_last_10 / (total_eas * 10) if total_eas > 0 else 0
        st.metric("Avg Sessions Per Day", f"{avg_sessions_per_day:.2f}")
    
    with col4:
        no_sessions = (filtered_table['Total Sessions Ever'] == 0).sum()
        st.metric("EAs with No Sessions", no_sessions)
    
    # Display the table
    st.markdown("### EA Implementation Status Table")
    
    # Sort by Total Sessions Ever (descending) then by name
    display_table = filtered_table.sort_values(['Total Sessions Ever', 'Name and Surname'], 
                                             ascending=[False, True])
    
    # Color code based on session activity
    def highlight_activity(val):
        if pd.isna(val) or val == 0:
            return 'background-color: #ffcccc'  # Light red for no activity
        elif val <= 5:
            return 'background-color: #ffffcc'  # Light yellow for low activity
        else:
            return 'background-color: #ccffcc'  # Light green for good activity
    
    # Apply styling to session columns
    styled_table = display_table.style.applymap(
        highlight_activity, 
        subset=['Sessions Last 10 Days', 'Total Sessions Ever']
    )
    
    st.dataframe(styled_table, use_container_width=True, height=600)
    
    # Export option
    st.markdown("### Export Data")
    csv = display_table.to_csv(index=False)
    st.download_button(
        label="Download EA Implementation Report",
        data=csv,
        file_name=f"ea_implementation_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

def display_selected_schools_analysis(df):
    """Display session analysis for DataQuest schools subset"""
    
    # Filter data to only include selected schools using lowercase comparison
    # Convert both the database program names and our list to lowercase for matching
    selected_schools_lower = [school.lower() for school in selected_schools_list]
    filtered_df = df[df['program_name'].str.lower().isin(selected_schools_lower)]
    
    if filtered_df.empty:
        st.warning("No data found for the DataQuest schools.")
        st.info("The DataQuest schools list may not match the program names in the database exactly.")
        return
    
    st.info(f"Showing data for {len(selected_schools_list)} DataQuest schools ({len(filtered_df):,} records)")
    
    # Calculate 7-day cutoff
    max_date = pd.to_datetime(filtered_df['session_started_at']).max()
    seven_days_ago = max_date - timedelta(days=7)
    df_7days = filtered_df[pd.to_datetime(filtered_df['session_started_at']) >= seven_days_ago]
    df_7days['session_date'] = pd.to_datetime(df_7days['session_started_at']).dt.date
    
    # SESSION OVERVIEW METRICS - PAST 7 DAYS
    st.subheader("Session Overview Metrics - Past 7 Days (DataQuest Schools)")
    
    # Primary School metrics (filtered)
    st.markdown("**Primary Schools**")
    df_primary_7days = df_7days[df_7days['school_type'] == 'Primary School']
    col1, col2, col3, col4, col5 = st.columns(5)
    
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
        # Count schools where EAs have been active 3+ days
        primary_ea_activity = df_primary_7days.groupby('user_name')['session_date'].nunique()
        primary_eas_3plus_users = primary_ea_activity[primary_ea_activity >= 3].index
        primary_schools_3plus = df_primary_7days[df_primary_7days['user_name'].isin(primary_eas_3plus_users)]['program_name'].nunique()
        st.metric("Schools Running 3+ Days", primary_schools_3plus)
    
    with col5:
        # Count schools where any EA has been active 1+ days
        primary_schools_1plus = df_primary_7days['program_name'].nunique()
        st.metric("Schools Running 1+ Days", primary_schools_1plus)
    
    st.divider()
    
    # DATAQUEST SCHOOLS BREAKDOWN TABLE
    st.subheader("EA Activity by DataQuest School - Past 7 Days")
    
    # Create table showing each DataQuest school with EA activity metrics
    school_activity_data = []
    
    for school in selected_schools_list:
        # Find matching school in data (case-insensitive)
        school_data = df_7days[df_7days['program_name'].str.lower() == school.lower()]
        
        if not school_data.empty:
            # Calculate EAs active 1+ days for this school
            eas_1plus = school_data['user_name'].nunique()
            
            # Calculate EAs active 3+ days for this school
            ea_activity = school_data.groupby('user_name')['session_date'].nunique()
            eas_3plus = (ea_activity >= 3).sum()
            
            # Get the actual school name from the data (proper case)
            actual_school_name = school_data['program_name'].iloc[0]
        else:
            # No data for this school
            eas_1plus = 0
            eas_3plus = 0
            actual_school_name = school  # Use the name from our list
        
        school_activity_data.append({
            'School Name': actual_school_name,
            'EAs Active 1+ Days': eas_1plus,
            'EAs Active 3+ Days': eas_3plus
        })
    
    # Create DataFrame and display
    school_activity_df = pd.DataFrame(school_activity_data)
    
    # Sort by EAs Active 3+ Days (descending), then by EAs Active 1+ Days (descending)
    school_activity_df = school_activity_df.sort_values(['EAs Active 3+ Days', 'EAs Active 1+ Days'], ascending=[False, False])
    
    # Display the table
    st.dataframe(school_activity_df, use_container_width=True, hide_index=True)
    
    # Add summary info
    total_schools_with_data = (school_activity_df['EAs Active 1+ Days'] > 0).sum()
    schools_with_3plus = (school_activity_df['EAs Active 3+ Days'] > 0).sum()
    st.info(f"📊 **Summary**: {total_schools_with_data} of {len(selected_schools_list)} DataQuest schools have EA activity in the past 7 days. {schools_with_3plus} schools have EAs active 3+ days.")
    
    st.divider()

    # UNIQUE EAs BY SCHOOLS & ECDs - PAST 7 DAYS
    st.subheader("Active EAs by Schools & ECDs - Past 7 Days (DataQuest Schools)")
    
    # Group by date and school type for unique EAs count
    daily_school_type_eas = df_7days.groupby(['session_date', 'school_type'])['user_name'].nunique().reset_index()
    daily_school_type_eas.columns = ['Date', 'School_Type', 'Active_EAs']
    
    if not daily_school_type_eas.empty:
        fig_school_type_eas = px.bar(
            daily_school_type_eas,
            x='Date',
            y='Active_EAs',
            color='School_Type',
            title="Daily Active EAs by Schools & ECDs - DataQuest Schools (Past 7 Days)",
            labels={'Active_EAs': 'Number of Active EAs', 'Date': 'Date'}
        )
        st.plotly_chart(fig_school_type_eas, use_container_width=True)
    
    # SESSIONS BY SCHOOLS & ECDs - PAST 30 DAYS
    st.subheader("Total Sessions by Schools & ECDs - Past 30 Days (DataQuest Schools)")
    
    # Calculate 30-day cutoff
    thirty_days_ago = max_date - timedelta(days=30)
    df_30days = filtered_df[pd.to_datetime(filtered_df['session_started_at']) >= thirty_days_ago]
    df_30days['session_date'] = pd.to_datetime(df_30days['session_started_at']).dt.date
    
    # Group by date and school type for sessions count
    daily_school_type_sessions = df_30days.groupby(['session_date', 'school_type'])['session_id'].nunique().reset_index()
    daily_school_type_sessions.columns = ['Date', 'School_Type', 'Sessions']
    
    if not daily_school_type_sessions.empty:
        fig_school_type_sessions = px.line(
            daily_school_type_sessions,
            x='Date',
            y='Sessions',
            color='School_Type',
            title="Daily Sessions by Schools & ECDs - DataQuest Schools (Past 30 Days)",
            labels={'Sessions': 'Number of Sessions', 'Date': 'Date'},
            markers=True
        )
        st.plotly_chart(fig_school_type_sessions, use_container_width=True)
    
    # ACTIVE EAs (3+ DAYS) TREND - PAST 30 DAYS
    st.subheader("Active EAs (3+ Days) Trend - Past 30 Days (DataQuest Schools)")
    
    # Calculate active EAs (3+ days) for each day over past 30 days
    df_with_date = filtered_df.copy()
    df_with_date['session_date'] = pd.to_datetime(df_with_date['session_started_at']).dt.date
    
    # Get all unique dates in the past 30 days
    all_dates = pd.date_range(start=thirty_days_ago.date(), end=max_date.date(), freq='D').date
    
    active_ea_trend_data = []
    
    for current_date in all_dates:
        # Calculate 7-day window ending on current_date
        seven_days_before = current_date - timedelta(days=6)  # 6 days before + current day = 7 days
        
        # Filter data to this 7-day window
        window_data = df_with_date[
            (df_with_date['session_date'] >= seven_days_before) & 
            (df_with_date['session_date'] <= current_date)
        ]
        
        if not window_data.empty:
            # Count EAs active 3+ days in this window, by school type
            for school_type in ['Primary School', 'ECD']:
                school_data = window_data[window_data['school_type'] == school_type]
                if not school_data.empty:
                    ea_activity = school_data.groupby('user_name')['session_date'].nunique()
                    active_eas_count = (ea_activity >= 3).sum()
                else:
                    active_eas_count = 0
                
                active_ea_trend_data.append({
                    'Date': current_date,
                    'School_Type': school_type,
                    'Active_EAs_3Plus': active_eas_count
                })
    
    if active_ea_trend_data:
        active_ea_trend_df = pd.DataFrame(active_ea_trend_data)
        
        fig_active_ea_trend = px.line(
            active_ea_trend_df,
            x='Date',
            y='Active_EAs_3Plus',
            color='School_Type',
            title="Daily Count of Active EAs (3+ Days) - DataQuest Schools (Past 30 Days)",
            labels={'Active_EAs_3Plus': 'Number of Active EAs (3+ Days)', 'Date': 'Date'},
            markers=True
        )
        st.plotly_chart(fig_active_ea_trend, use_container_width=True)
        
        st.info("📊 **Note**: For each day, we count EAs who were active 3+ days within the 7-day period ending on that day.")
    
    # Create the views with filtered data
    daily_summary, weekly_summary, assistant_summary = create_session_views(filtered_df)
    
    # SCHOOL TYPE FILTER
    st.subheader("Filter by School Type (DataQuest Schools)")
    school_type_filter = st.selectbox(
        "Select School Type:",
        options=["All", "ECD", "Primary School"],
        index=0,
        key="dataquest_schools_type_filter"
    )
    
    # Apply filter
    if school_type_filter != "All":
        type_filtered_df = filtered_df[filtered_df['school_type'] == school_type_filter]
        st.info(f"Showing data for {school_type_filter} only ({len(type_filtered_df):,} records)")
    else:
        type_filtered_df = filtered_df
        st.info(f"Showing all school types ({len(type_filtered_df):,} records)")
    
    # Recalculate views with type-filtered data
    daily_summary_filtered, weekly_summary_filtered, assistant_summary_filtered = create_session_views(type_filtered_df)
    
    # EA WORKLOAD COMPARISON
    st.subheader("EA Workload Comparison (DataQuest Schools)")
    
    # Total sessions bar chart
    fig_total = px.bar(
        assistant_summary_filtered.sort_values('Total_Sessions', ascending=True),
        x='user_name',
        y='Total_Sessions',
        title=f"Total Sessions by EA - DataQuest Schools ({school_type_filter})"
    )
    st.plotly_chart(fig_total, use_container_width=True)
    
    # Average daily sessions
    fig_avg = px.bar(
        assistant_summary_filtered.sort_values('Avg_Sessions_Per_Day', ascending=True),
        x='user_name',
        y='Avg_Sessions_Per_Day',
        title=f"Average Sessions per Day - DataQuest Schools ({school_type_filter})"
    )
    st.plotly_chart(fig_avg, use_container_width=True)
    
    # EA ACTIVITY TABLE - PAST 10 WEEKDAYS
    st.subheader("EA Session Activity - Past 10 Weekdays (DataQuest Schools)")
    
    # Create two columns for the filters
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        # School type filter for this section
        ea_school_type_filter = st.selectbox(
            "Filter by School Type:",
            options=["Primary School", "ECD", "All"],
            index=0,  # Default to Primary School
            key="dataquest_ea_activity_filter"
        )
    
    with filter_col2:
        # Mentor filter for this section
        mentor_options = ["All mentors"] + list(mentors_to_schools.keys())
        ea_mentor_filter = st.selectbox(
            "Filter by Mentor:",
            options=mentor_options,
            index=0,  # Default to All mentors
            key="dataquest_ea_mentor_filter"
        )
    
    # Apply filters for EA activity section
    ea_filtered_df = filtered_df.copy()
    
    if ea_school_type_filter != "All":
        ea_filtered_df = ea_filtered_df[ea_filtered_df['school_type'] == ea_school_type_filter]
    
    if ea_mentor_filter != "All mentors":
        ea_filtered_df = ea_filtered_df[ea_filtered_df['mentor'] == ea_mentor_filter]
    
    # Create the activity table
    activity_table = create_ea_activity_table(ea_filtered_df)
    
    if not activity_table.empty:
        # ACTIVE DAYS BREAKDOWN AND PIE CHART
        col1, col2 = st.columns([1, 1])
        
        with col1:
            # Create filter text for display
            filter_parts = []
            if ea_school_type_filter != "All":
                filter_parts.append(ea_school_type_filter)
            if ea_mentor_filter != "All mentors":
                filter_parts.append(f"Mentor: {ea_mentor_filter}")
            
            filter_text = f" ({', '.join(filter_parts)})" if filter_parts else ""
            st.info(f"**Here's a breakdown of how many days each EA has worked over the past 10 weekdays{filter_text} - DataQuest Schools.**")
            
            # Create breakdown of Total Active Days
            active_days_counts = activity_table['Total Active Days'].value_counts().sort_index(ascending=False)
            total_eas = len(activity_table)
            
            # Create breakdown table
            breakdown_df = pd.DataFrame({
                'No. of Days Worked': active_days_counts.index,
                'Count of EAs': active_days_counts.values,
                'Percentage of EAs': (active_days_counts.values / total_eas * 100).round(1)
            })
            
            st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
        
        with col2:   
            
            st.info(f"**Charting the distribution of days worked by EAs (over the past 10 weekdays{filter_text}) - DataQuest Schools.**")         
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
            chart_title = f"Days Worked Distribution by EAs{filter_text} - DataQuest Schools"
            
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
        
        st.markdown("**Number of sessions run by each EA on each weekday (Monday-Friday) - DataQuest Schools**")
        st.dataframe(activity_table.drop('Work_Category', axis=1), use_container_width=True)
        
        # Add summary info
        active_weekdays = len([col for col in activity_table.columns if col not in ['Total Active Days', 'Work_Category']])
        summary_text = f"Showing {total_eas} Education Assistants across {active_weekdays} most recent weekdays (DataQuest Schools)"
        if filter_parts:
            summary_text += f" ({', '.join(filter_parts)} only)"
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
        try:
            last_refresh = get_last_refresh_timestamp()
            if last_refresh:
                refresh_info = f"Data last refreshed: {last_refresh.strftime('%Y-%m-%d %H:%M:%S')}"
                st.info(refresh_info)
                
                # Show database summary
                summary = get_data_summary()
                if summary:
                    st.caption(f"Database: {summary['total_records']:,} records, {summary['unique_sessions']:,} sessions")
            else:
                st.warning("No refresh timestamp available")
        except Exception as e:
            st.error(f"Could not get database info: {e}")

# MAIN APP STARTS HERE
st.title("TeamPact Education Assistant Analytics")
st.markdown("Session tracking and curriculum analysis")

# Create columns for title and refresh button
col1, col2 = st.columns([4, 1])

with col2:
    # Show last updated info
    try:
        from database_utils import get_last_refresh_timestamp, get_data_summary
        last_refresh = get_last_refresh_timestamp()
        if last_refresh:
            time_ago = datetime.now() - last_refresh.replace(tzinfo=None)
            hours_ago = time_ago.total_seconds() / 3600
            if hours_ago < 1:
                time_str = f"{int(time_ago.total_seconds() / 60)} min ago"
            else:
                time_str = f"{int(hours_ago)} hours ago"
            st.caption(f"Last updated: {time_str}")
        else:
            st.caption("No data found")
    except:
        st.caption("Database status unknown")
    
    # Check if refresh is in progress
    refresh_key = "data_refresh_in_progress"
    if refresh_key not in st.session_state:
        st.session_state[refresh_key] = False
    
    if st.session_state[refresh_key]:
        st.info("🔄 Data refresh in progress... Please wait.")
        if st.button("Cancel Refresh", type="secondary"):
            st.session_state[refresh_key] = False
            st.rerun()
    else:
        if st.button("Refresh Data", type="primary"):
            st.session_state[refresh_key] = True
            st.rerun()
            
    # Perform refresh if flagged
    if st.session_state[refresh_key]:
        with st.spinner("Fetching data from TeamPact API..."):
            success = fetch_and_save_data()
            st.session_state[refresh_key] = False
            if success:
                st.success("Data refreshed successfully!")
                # Clear the cache to force reload with new data
                from database_utils import load_session_data_from_db
                load_session_data_from_db.clear()
                st.rerun()
            else:
                st.error("Failed to fetch data. Check your API credentials.")
                st.rerun()

# Load the data from database
try:
    # Import database utilities
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from database_utils import load_session_data_from_db, get_last_refresh_timestamp, get_data_summary
    
    # Load data from database
    df = load_session_data_from_db()
    
    if df.empty:
        st.warning("No data found in database. Please refresh data from API.")
        st.info("Click the 'Refresh Data' button above to fetch the latest session data from TeamPact.")
        st.stop()

except Exception as e:
    st.error(f"Error loading data from database: {e}")
    
    # Show recovery options
    st.subheader("Database Connection Issues")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Try Fresh Data Fetch", type="primary"):
            with st.spinner("Fetching fresh data from TeamPact API..."):
                success = fetch_and_save_data()
                if success:
                    st.success("Fresh data fetched successfully!")
                    st.rerun()
                else:
                    st.error("Failed to fetch fresh data.")
    
    with col2:
        if st.button("🔍 Test Database Connection"):
            from database_utils import test_database_connection
            success, message = test_database_connection()
            if success:
                st.success(message)
            else:
                st.error(message)
    
    with st.expander("🔍 Error Details"):
        import traceback
        st.code(traceback.format_exc())
        
    with st.expander("💡 Troubleshooting"):
        st.markdown("""
        **Common Solutions:**
        1. **Database Migration**: Run `python database_migrations/run_migration.py` to create the database table
        2. **Environment Variables**: Check that `RENDER_DATABASE_URL` is set correctly  
        3. **Network**: Verify connection to your Render PostgreSQL database
        4. **Fresh Data**: Try refreshing data from the API using the button above
        """)
    
    st.stop()

# School type and mentor classification are now handled in the database loading function

# CREATE TABS FOR DIFFERENT VIEWS
tab1, tab2, tab3, tab4 = st.tabs(["EA Sessions Analysis", "EA Implementation Status", "Data Quality", "DataQuest Schools"])

with tab1:
    display_session_analysis(df)

with tab2:
    display_ea_implementation_analysis(df)

with tab3:
    display_data_quality(df)

with tab4:
    display_selected_schools_analysis(df)