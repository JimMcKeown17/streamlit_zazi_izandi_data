import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Add the project root to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from data.mentor_schools import mentors_to_schools
from data_loader import load_sessions_2026

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

el_schools = [
    "Brownlee Primary School",
    "Bumbanani Primary School",
    "Chuma Junior Primary School",
    "Duncan Village Public School",
    "Ebhotwe Junior Full Service School",
    "Emncotsho Primary School",
    "Encotsheni Senior Primary School",
    "Equleni Junior Primary School",
    "Fanti Gaqa Senior Primary School",
    "Inkqubela Junior Primary School",
    "Isibane Junior Primary School",
    "Isithsaba Junior Primary School",
    "Jityaza Combined Primary School",
    "Khanyisa Junior Primary School",
    "Lunga Junior Primary School",
    "Lwandisa Junior Primary School",
    "Manyano Junior Primary School",
    "Masakhe Primary School",
    "Mdantsane Junior Primary School",
    "Misukukhanya Senior Primary School",
    "Mzoxolo Senior Primary School",
    "Nkangeleko Intermediate School",
    "Nkosinathi Primary School",
    "Nobhotwe Junior Primary School",
    "Nontombi Matta Junior Primary School",
    "Nontsikelelo Junior Primary School",
    "Nontuthuzelo Primary School",
    "Nqonqweni Primary School",
    "Nzuzo Junior Primary School",
    "Qaqamba Junior Primary School",
    "R H Godlo Junior Primary School",
    "Sakhile Senior Primary School",
    "Shad Mashologu Junior Primary School",
    "St John'S Road Junior Secondary School",
    "Thembeka Junior Primary School",
    "Vuthondaba Full Service School",
    "W.N. Madikizela-Mandela Primary School",
    "Zamani Junior Primary School",
    "Zanempucuko Senior Secondary School",
    "Zanokukhanya Junior Primary School",
    "Zuzile Junior Primary School"
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

    # Convert session_duration from seconds to minutes if it exists
    if 'session_duration' in df.columns and 'total_duration_minutes' not in df.columns:
        df['total_duration_minutes'] = df['session_duration'] / 60.0

    # 1. SESSIONS PER ASSISTANT PER DAY
    daily_sessions = df.groupby(['user_name', 'session_date', 'session_id']).first().reset_index()

    # Handle both old and new column names
    agg_dict = {'session_id': 'count'}
    if 'total_duration_minutes' in daily_sessions.columns:
        agg_dict['total_duration_minutes'] = 'sum'
    if 'attended_percentage' in daily_sessions.columns:
        agg_dict['attended_percentage'] = 'mean'

    daily_summary = daily_sessions.groupby(['user_name', 'session_date']).agg(agg_dict).round(1)

    # Rename columns based on what we have
    col_names = ['Sessions_Count']
    if 'total_duration_minutes' in agg_dict:
        col_names.append('Total_Minutes')
    if 'attended_percentage' in agg_dict:
        col_names.append('Avg_Attendance_Pct')

    daily_summary.columns = col_names
    daily_summary = daily_summary.reset_index()

    # 2. WEEKLY PATTERNS
    weekly_sessions = df.groupby(['user_name', 'session_weekday', 'session_id']).first().reset_index()
    weekly_summary = weekly_sessions.groupby(['user_name', 'session_weekday']).size().reset_index()
    weekly_summary.columns = ['user_name', 'session_weekday', 'session_count']

    # 3. ASSISTANT WORKLOAD SUMMARY
    # Build aggregation dynamically based on available columns
    agg_dict_assistant = {'Sessions_Count': ['sum', 'mean', 'max']}
    if 'Total_Minutes' in daily_summary.columns:
        agg_dict_assistant['Total_Minutes'] = ['sum', 'mean']
    if 'Avg_Attendance_Pct' in daily_summary.columns:
        agg_dict_assistant['Avg_Attendance_Pct'] = 'mean'

    assistant_summary = daily_summary.groupby('user_name').agg(agg_dict_assistant).round(1)

    # Flatten column names based on what we have
    col_names_assistant = ['Total_Sessions', 'Avg_Sessions_Per_Day', 'Max_Sessions_Per_Day']
    if 'Total_Minutes' in agg_dict_assistant:
        col_names_assistant.extend(['Total_Minutes_Taught', 'Avg_Minutes_Per_Day'])
    if 'Avg_Attendance_Pct' in agg_dict_assistant:
        col_names_assistant.append('Overall_Avg_Attendance')

    assistant_summary.columns = col_names_assistant
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

def create_school_workload_summary(df):
    """Create school-level workload summary with school categorization"""

    if df.empty:
        return pd.DataFrame()

    # Convert school names to lowercase for comparison
    el_schools_lower = [school.lower() for school in el_schools]

    # Create school categorization function
    def categorize_school(program_name):
        if program_name.lower() in el_schools_lower:
            return 'East London Schools'
        else:
            return 'NMB Schools'

    # Add school category to dataframe
    df_with_category = df.copy()
    df_with_category['school_category'] = df_with_category['program_name'].apply(categorize_school)

    # Group by school and calculate metrics
    school_summary = df_with_category.groupby(['program_name', 'school_category']).agg({
        'session_id': 'nunique',  # Total unique sessions
        'user_name': 'nunique',  # Number of EAs
        'session_started_at': ['min', 'max']  # Date range
    }).round(1)

    # Flatten column names
    school_summary.columns = ['Total_Sessions', 'Num_EAs', 'First_Session', 'Last_Session']
    school_summary = school_summary.reset_index()

    # Calculate average sessions per day
    school_summary['Date_Range_Days'] = (pd.to_datetime(school_summary['Last_Session']) - pd.to_datetime(school_summary['First_Session'])).dt.days + 1
    school_summary['Avg_Sessions_Per_Day'] = (school_summary['Total_Sessions'] / school_summary['Date_Range_Days']).round(2)

    # Sort by total sessions descending
    school_summary = school_summary.sort_values('Total_Sessions', ascending=False)

    return school_summary

def display_session_analysis(df):
    """Display comprehensive session analysis dashboard"""

    # Prepare date columns for all data
    df_all = df.copy()
    df_all['session_date'] = pd.to_datetime(df_all['session_started_at']).dt.date

    # UPDATED METRICS - ALL DATA
    st.subheader("Session Overview Metrics - All Data")

    # Primary School metrics
    st.markdown("**Primary Schools**")
    df_primary_all = df_all[df_all['school_type'] == 'Primary School']
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        primary_ea_activity = df_primary_all.groupby('user_name')['session_date'].nunique()
        primary_eas_3plus = (primary_ea_activity >= 3).sum()
        st.metric("School EAs Active 3+ Days", primary_eas_3plus)

    with col2:
        primary_ea_activity = df_primary_all.groupby('user_name')['session_date'].nunique()
        primary_eas_15plus = (primary_ea_activity >= 15).sum()
        st.metric("School EAs Active 15+ Days", primary_eas_15plus)

    with col3:
        primary_sessions = df_primary_all['session_id'].nunique()
        primary_eas_active = df_primary_all['user_name'].nunique()
        primary_avg_sessions = primary_sessions / primary_eas_active if primary_eas_active > 0 else 0
        st.metric("Avg Sessions per School EA", f"{primary_avg_sessions:.1f}")

    with col4:
        # Count schools where EAs have been active 3+ days
        primary_ea_activity = df_primary_all.groupby('user_name')['session_date'].nunique()
        primary_eas_3plus_users = primary_ea_activity[primary_ea_activity >= 3].index
        primary_schools_3plus = df_primary_all[df_primary_all['user_name'].isin(primary_eas_3plus_users)]['program_name'].nunique()
        st.metric("Schools Running 3+ Days", primary_schools_3plus)

    with col5:
        # Count schools where EAs have been active 15+ days
        primary_ea_activity = df_primary_all.groupby('user_name')['session_date'].nunique()
        primary_eas_15plus_users = primary_ea_activity[primary_ea_activity >= 15].index
        primary_schools_15plus = df_primary_all[df_primary_all['user_name'].isin(primary_eas_15plus_users)]['program_name'].nunique()
        st.metric("Schools Running 15+ Days", primary_schools_15plus)

    # ECD metrics
    st.markdown("**Early Childhood Development Centers**")
    df_ecd_all = df_all[df_all['school_type'] == 'ECD']
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        ecd_ea_activity = df_ecd_all.groupby('user_name')['session_date'].nunique()
        ecd_eas_3plus = (ecd_ea_activity >= 3).sum()
        st.metric("ECD EAs Active 3+ Days", ecd_eas_3plus)

    with col2:
        ecd_ea_activity = df_ecd_all.groupby('user_name')['session_date'].nunique()
        ecd_eas_15plus = (ecd_ea_activity >= 15).sum()
        st.metric("ECD EAs Active 15+ Days", ecd_eas_15plus)

    with col3:
        ecd_sessions = df_ecd_all['session_id'].nunique()
        ecd_eas_active = df_ecd_all['user_name'].nunique()
        ecd_avg_sessions = ecd_sessions / ecd_eas_active if ecd_eas_active > 0 else 0
        st.metric("Avg Sessions per ECD EA", f"{ecd_avg_sessions:.1f}")

    with col4:
        # Count ECDs where EAs have been active 3+ days
        ecd_ea_activity = df_ecd_all.groupby('user_name')['session_date'].nunique()
        ecd_eas_3plus_users = ecd_ea_activity[ecd_ea_activity >= 3].index
        ecd_schools_3plus = df_ecd_all[df_ecd_all['user_name'].isin(ecd_eas_3plus_users)]['program_name'].nunique()
        st.metric("ECDs Running 3+ Days", ecd_schools_3plus)

    with col5:
        # Count ECDs where EAs have been active 15+ days
        ecd_ea_activity = df_ecd_all.groupby('user_name')['session_date'].nunique()
        ecd_eas_15plus_users = ecd_ea_activity[ecd_ea_activity >= 15].index
        ecd_schools_15plus = df_ecd_all[df_ecd_all['user_name'].isin(ecd_eas_15plus_users)]['program_name'].nunique()
        st.metric("ECDs Running 15+ Days", ecd_schools_15plus)

    st.divider()

    # HISTOGRAM: DAYS WORKED DISTRIBUTION
    st.subheader("Distribution of Days Worked by EAs")

    # Calculate days worked for each EA
    ea_days_worked = df_all.groupby('user_name')['session_date'].nunique().reset_index()
    ea_days_worked.columns = ['EA_Name', 'Days_Worked']

    # Create histogram with bucket size of 1
    fig_histogram = px.histogram(
        ea_days_worked,
        x='Days_Worked',
        nbins=int(ea_days_worked['Days_Worked'].max()) if not ea_days_worked.empty else 50,
        title="Number of EAs by Days Worked",
        labels={'Days_Worked': 'Days Worked', 'count': 'Number of EAs'},
        color_discrete_sequence=['#1f77b4']
    )

    # Update layout for better readability
    fig_histogram.update_layout(
        xaxis_title="Days Worked",
        yaxis_title="Number of EAs",
        bargap=0.1,
        showlegend=False
    )

    st.plotly_chart(fig_histogram, width='stretch')

    # Show summary statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total EAs", len(ea_days_worked))
    with col2:
        st.metric("Avg Days per EA", f"{ea_days_worked['Days_Worked'].mean():.1f}")
    with col3:
        st.metric("Median Days per EA", f"{ea_days_worked['Days_Worked'].median():.0f}")
    with col4:
        st.metric("Max Days Worked", f"{ea_days_worked['Days_Worked'].max():.0f}")

    st.divider()

    # UNIQUE EAs BY SCHOOLS & ECDs - ALL DATA
    st.subheader("Active EAs by Schools & ECDs")

    # Group by date and school type for unique EAs count
    daily_school_type_eas = df_all.groupby(['session_date', 'school_type'])['user_name'].nunique().reset_index()
    daily_school_type_eas.columns = ['Date', 'School_Type', 'Active_EAs']

    if not daily_school_type_eas.empty:
        fig_school_type_eas = px.bar(
            daily_school_type_eas,
            x='Date',
            y='Active_EAs',
            color='School_Type',
            title="Daily Active EAs by Schools & ECDs",
            labels={'Active_EAs': 'Number of Active EAs', 'Date': 'Date'}
        )
        st.plotly_chart(fig_school_type_eas, width='stretch')

    # SESSIONS BY SCHOOLS & ECDs - ALL DATA
    st.subheader("Total Sessions by Schools & ECDs")

    # Group by date and school type for sessions count
    daily_school_type_sessions = df_all.groupby(['session_date', 'school_type'])['session_id'].nunique().reset_index()
    daily_school_type_sessions.columns = ['Date', 'School_Type', 'Sessions']

    if not daily_school_type_sessions.empty:
        fig_school_type_sessions = px.line(
            daily_school_type_sessions,
            x='Date',
            y='Sessions',
            color='School_Type',
            title="Daily Sessions by Schools & ECDs",
            labels={'Sessions': 'Number of Sessions', 'Date': 'Date'},
            markers=True
        )
        st.plotly_chart(fig_school_type_sessions, width='stretch')

    # ACTIVE EAs (3+ DAYS) TREND - ALL DATA
    st.subheader("Active EAs (3+ Days) Trend")

    # Calculate active EAs (3+ days) for each day over all available data
    df_with_date = df.copy()
    df_with_date['session_date'] = pd.to_datetime(df_with_date['session_started_at']).dt.date

    # Get all unique dates in the data
    max_date = pd.to_datetime(df['session_started_at']).max()
    min_date = pd.to_datetime(df['session_started_at']).min()
    all_dates = pd.date_range(start=min_date.date(), end=max_date.date(), freq='D').date

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
            title="Daily Count of Active EAs (3+ Days)",
            labels={'Active_EAs_3Plus': 'Number of Active EAs (3+ Days)', 'Date': 'Date'},
            markers=True
        )
        st.plotly_chart(fig_active_ea_trend, width='stretch')

        st.info("**Note**: For each day, we count EAs who were active 3+ days within the 7-day period ending on that day.")

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
    st.plotly_chart(fig_total, width='stretch')

        # Average daily sessions
    fig_avg = px.bar(
        assistant_summary_filtered.sort_values('Avg_Sessions_Per_Day', ascending=True),
        x='user_name',
        y='Avg_Sessions_Per_Day',
        title=f"Average Sessions per Day ({school_type_filter})"
    )
    st.plotly_chart(fig_avg, width='stretch')

    # SCHOOL WORKLOAD COMPARISON
    st.subheader("School Workload Comparison")

    # Create school-level summary data
    school_summary = create_school_workload_summary(filtered_df)

    if not school_summary.empty:
        # Total sessions by school chart - mixed order
        fig_school_total = px.bar(
            school_summary.sort_values('Total_Sessions', ascending=True),
            x='program_name',
            y='Total_Sessions',
            color='school_category',
            title=f"Total Sessions by School ({school_type_filter})",
            color_discrete_map={
                'East London Schools': '#FFD93D',  # Yellow
                'NMB Schools': '#45B7D1'  # Blue
            },
            category_orders={'program_name': school_summary.sort_values('Total_Sessions', ascending=True)['program_name'].tolist()}
        )
        fig_school_total.update_layout(
            xaxis_tickangle=-45,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis={'categoryorder': 'array', 'categoryarray': school_summary.sort_values('Total_Sessions', ascending=True)['program_name'].tolist()}
        )
        st.plotly_chart(fig_school_total, width='stretch')

        # Average sessions per day by school chart - mixed order
        fig_school_avg = px.bar(
            school_summary.sort_values('Avg_Sessions_Per_Day', ascending=True),
            x='program_name',
            y='Avg_Sessions_Per_Day',
            color='school_category',
            title=f"Average Sessions per Day by School ({school_type_filter})",
            color_discrete_map={
                'East London Schools': '#FFD93D',  # Yellow
                'NMB Schools': '#45B7D1'  # Blue
            },
            category_orders={'program_name': school_summary.sort_values('Avg_Sessions_Per_Day', ascending=True)['program_name'].tolist()}
        )
        fig_school_avg.update_layout(
            xaxis_tickangle=-45,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis={'categoryorder': 'array', 'categoryarray': school_summary.sort_values('Avg_Sessions_Per_Day', ascending=True)['program_name'].tolist()}
        )
        st.plotly_chart(fig_school_avg, width='stretch')

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

            st.dataframe(breakdown_df, width='stretch', hide_index=True)

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
            st.plotly_chart(fig_pie, width='stretch')

        st.divider()

        st.markdown("**Number of sessions run by each EA on each weekday (Monday-Friday)**")
        st.dataframe(activity_table.drop('Work_Category', axis=1), width='stretch')

        # Add summary info
        active_weekdays = len([col for col in activity_table.columns if col not in ['Total Active Days', 'Work_Category']])
        summary_text = f"Showing {total_eas} Education Assistants across {active_weekdays} most recent weekdays"
        if filter_parts:
            summary_text += f" ({', '.join(filter_parts)} only)"
        st.info(summary_text)
    else:
        st.warning("No session data available for the activity table.")



def display_children_session_analysis(df):
    """Display session analysis from children's perspective"""

    st.header("Children's Session Participation Analysis")

    # Check if participant_id column exists
    if 'participant_id' not in df.columns:
        st.error("The 'participant_id' column is not available in the dataset.")
        return

    # Prepare date columns
    df_children = df.copy()
    df_children['session_date'] = pd.to_datetime(df_children['session_started_at']).dt.date
    df_children['session_week'] = pd.to_datetime(df_children['session_started_at']).dt.to_period('W')

    # Calculate sessions per child
    child_sessions = df_children.groupby('participant_id').agg({
        'session_id': 'nunique',  # Total unique sessions
        'session_date': 'nunique',  # Total unique days attended
        'session_week': 'nunique',  # Total weeks with sessions
        'participant_name': 'first',  # Get child's name
        'program_name': 'first',  # Get school name
        'class_name': 'first',  # Get class name
        'school_type': 'first'  # Get school type
    }).reset_index()

    child_sessions.columns = ['participant_id', 'total_sessions', 'days_attended', 'weeks_attended',
                              'child_name', 'school_name', 'class_name', 'school_type']

    # Calculate average sessions per week (only for weeks where they had at least 1 session)
    child_sessions['avg_sessions_per_week'] = (child_sessions['total_sessions'] /
                                                child_sessions['weeks_attended']).round(2)

    # OVERVIEW METRICS
    st.subheader("Overall Participation Metrics")

    # Primary School metrics
    st.markdown("**Primary Schools**")
    primary_children = child_sessions[child_sessions['school_type'] == 'Primary School']
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Children", f"{len(primary_children):,}")

    with col2:
        st.metric("Avg Sessions per Child", f"{primary_children['total_sessions'].mean():.1f}" if len(primary_children) > 0 else "0.0")

    with col3:
        st.metric("Median Sessions per Child", f"{primary_children['total_sessions'].median():.0f}" if len(primary_children) > 0 else "0")

    with col4:
        st.metric("Max Sessions (One Child)", f"{primary_children['total_sessions'].max():.0f}" if len(primary_children) > 0 else "0")

    with col5:
        st.metric("Children with 10+ Sessions", f"{(primary_children['total_sessions'] >= 10).sum():,}")

    # ECD metrics
    st.markdown("**Early Childhood Development Centers**")
    ecd_children = child_sessions[child_sessions['school_type'] == 'ECD']
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Total Children", f"{len(ecd_children):,}")

    with col2:
        st.metric("Avg Sessions per Child", f"{ecd_children['total_sessions'].mean():.1f}" if len(ecd_children) > 0 else "0.0")

    with col3:
        st.metric("Median Sessions per Child", f"{ecd_children['total_sessions'].median():.0f}" if len(ecd_children) > 0 else "0")

    with col4:
        st.metric("Max Sessions (One Child)", f"{ecd_children['total_sessions'].max():.0f}" if len(ecd_children) > 0 else "0")

    with col5:
        st.metric("Children with 10+ Sessions", f"{(ecd_children['total_sessions'] >= 10).sum():,}")

    st.divider()

    # HISTOGRAM: SESSIONS PER CHILD
    st.subheader("Distribution of Sessions per Child")

    # Create histogram with bucket size of 1
    fig_histogram = px.histogram(
        child_sessions,
        x='total_sessions',
        nbins=int(child_sessions['total_sessions'].max()) if not child_sessions.empty else 50,
        title="Number of Children by Sessions Received",
        labels={'total_sessions': 'Sessions Received', 'count': 'Number of Children'},
        color_discrete_sequence=['#2ca02c']
    )

    # Update layout for better readability
    fig_histogram.update_layout(
        xaxis_title="Sessions Received",
        yaxis_title="Number of Children",
        bargap=0.1,
        showlegend=False
    )

    st.plotly_chart(fig_histogram, width='stretch')

    # Show distribution statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        children_0_5 = ((child_sessions['total_sessions'] >= 0) & (child_sessions['total_sessions'] <= 5)).sum()
        pct_0_5 = (children_0_5 / len(child_sessions) * 100) if len(child_sessions) > 0 else 0
        st.metric("0-5 Sessions", f"{children_0_5:,}", f"{pct_0_5:.1f}%")
    with col2:
        children_6_15 = ((child_sessions['total_sessions'] >= 6) & (child_sessions['total_sessions'] <= 15)).sum()
        pct_6_15 = (children_6_15 / len(child_sessions) * 100) if len(child_sessions) > 0 else 0
        st.metric("6-15 Sessions", f"{children_6_15:,}", f"{pct_6_15:.1f}%")
    with col3:
        children_16_30 = ((child_sessions['total_sessions'] >= 16) & (child_sessions['total_sessions'] <= 30)).sum()
        pct_16_30 = (children_16_30 / len(child_sessions) * 100) if len(child_sessions) > 0 else 0
        st.metric("16-30 Sessions", f"{children_16_30:,}", f"{pct_16_30:.1f}%")
    with col4:
        children_31_plus = (child_sessions['total_sessions'] >= 31).sum()
        pct_31_plus = (children_31_plus / len(child_sessions) * 100) if len(child_sessions) > 0 else 0
        st.metric("31+ Sessions", f"{children_31_plus:,}", f"{pct_31_plus:.1f}%")

    st.divider()

    # AVERAGE SESSIONS PER WEEK HISTOGRAM
    st.subheader("Distribution of Average Sessions per Week")

    st.info("**Note**: This shows the average number of sessions per week for weeks where the child attended at least one session.")

    # Create histogram for avg sessions per week
    fig_weekly = px.histogram(
        child_sessions,
        x='avg_sessions_per_week',
        nbins=20,
        title="Number of Children by Average Weekly Sessions",
        labels={'avg_sessions_per_week': 'Avg Sessions per Week', 'count': 'Number of Children'},
        color_discrete_sequence=['#ff7f0e']
    )

    fig_weekly.update_layout(
        xaxis_title="Average Sessions per Week",
        yaxis_title="Number of Children",
        bargap=0.1,
        showlegend=False
    )

    st.plotly_chart(fig_weekly, width='stretch')

    # Show weekly statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Avg Weekly Sessions (All)", f"{child_sessions['avg_sessions_per_week'].mean():.2f}")
    with col2:
        st.metric("Median Weekly Sessions", f"{child_sessions['avg_sessions_per_week'].median():.2f}")
    with col3:
        st.metric("Children with 2+ per week", f"{(child_sessions['avg_sessions_per_week'] >= 2).sum():,}")
    with col4:
        st.metric("Children with 3+ per week", f"{(child_sessions['avg_sessions_per_week'] >= 3).sum():,}")

    st.divider()

    # BREAKDOWN BY SCHOOL TYPE
    st.subheader("Participation by School Type")

    col1, col2 = st.columns(2)

    with col1:
        # Sessions by school type
        school_type_sessions = child_sessions.groupby('school_type')['total_sessions'].agg(['count', 'mean', 'median']).round(1)
        school_type_sessions.columns = ['Number of Children', 'Avg Sessions', 'Median Sessions']
        st.markdown("**Session Participation by School Type**")
        st.dataframe(school_type_sessions, width='stretch')

    with col2:
        # Box plot showing distribution by school type
        fig_box = px.box(
            child_sessions,
            x='school_type',
            y='total_sessions',
            title="Session Distribution by School Type",
            labels={'total_sessions': 'Sessions Received', 'school_type': 'School Type'},
            color='school_type'
        )
        st.plotly_chart(fig_box, width='stretch')

    st.divider()

    # DETAILED DATA TABLE
    st.subheader("Children Session Details")

    # Add search and filter options
    col1, col2 = st.columns(2)

    with col1:
        school_type_filter = st.selectbox(
            "Filter by School Type:",
            options=["All"] + sorted(child_sessions['school_type'].unique().tolist()),
            key="children_school_type_filter"
        )

    with col2:
        min_sessions_filter = st.number_input(
            "Minimum Sessions:",
            min_value=0,
            max_value=int(child_sessions['total_sessions'].max()),
            value=0,
            key="children_min_sessions"
        )

    # Apply filters
    filtered_children = child_sessions.copy()
    if school_type_filter != "All":
        filtered_children = filtered_children[filtered_children['school_type'] == school_type_filter]
    filtered_children = filtered_children[filtered_children['total_sessions'] >= min_sessions_filter]

    # Sort by total sessions descending
    filtered_children = filtered_children.sort_values('total_sessions', ascending=False)

    st.info(f"Showing {len(filtered_children):,} children")

    # Display table
    display_columns = ['child_name', 'school_name', 'class_name', 'school_type',
                      'total_sessions', 'days_attended', 'weeks_attended', 'avg_sessions_per_week']
    display_children = filtered_children[display_columns].copy()
    display_children.columns = ['Child Name', 'School', 'Class', 'School Type',
                                'Total Sessions', 'Days Attended', 'Weeks Attended', 'Avg Sessions/Week']

    st.dataframe(display_children, width='stretch', height=400, hide_index=True)

    # Export option
    st.markdown("### Export Data")
    csv = display_children.to_csv(index=False)
    st.download_button(
        label="Download Children Session Report",
        data=csv,
        file_name=f"children_sessions_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

def display_class_session_analysis(df):
    """Display group-level session analysis showing distribution of sessions per group - NMB Schools Only"""

    st.header("Group-Level Session Analysis - NMB Schools")

    # Filter to NMB schools only (exclude East London schools and ECDs)
    el_schools_lower = [school.lower() for school in el_schools]
    ecd_list_lower = [school.lower() for school in ecd_list]

    # Keep only schools that are NOT in el_schools and NOT in ecd_list
    nmb_df = df[
        ~df['program_name'].str.lower().isin(el_schools_lower) &
        ~df['program_name'].str.lower().isin(ecd_list_lower)
    ]

    if nmb_df.empty:
        st.warning("No data found for NMB schools.")
        return

    st.info(f"Showing data for NMB schools only ({len(nmb_df):,} records, {nmb_df['program_name'].nunique()} unique schools)")

    # Check if class_name column exists
    if 'class_name' not in nmb_df.columns:
        st.error("The 'class_name' column is not available in the dataset.")
        return

    # Group by class_name and count unique session_ids
    class_sessions = nmb_df.groupby('class_name')['session_id'].nunique().reset_index()
    class_sessions.columns = ['Group Name', 'Total Sessions']

    # Calculate average sessions per group
    avg_sessions_per_group = class_sessions['Total Sessions'].mean()
    median_sessions_per_group = class_sessions['Total Sessions'].median()

    # Display key metrics
    st.subheader("Group Session Metrics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Groups", len(class_sessions))

    with col2:
        st.metric("Avg Sessions per Group", f"{avg_sessions_per_group:.1f}")

    with col3:
        st.metric("Median Sessions per Group", f"{median_sessions_per_group:.0f}")

    with col4:
        total_unique_sessions = nmb_df['session_id'].nunique()
        st.metric("Total Unique Sessions", f"{total_unique_sessions:,}")

    st.divider()

    # Create cohort buckets
    def categorize_sessions(session_count):
        if session_count <= 10:
            return "0-10 sessions"
        elif session_count <= 20:
            return "11-20 sessions"
        elif session_count <= 30:
            return "21-30 sessions"
        else:
            return "31+ sessions"

    class_sessions['Cohort'] = class_sessions['Total Sessions'].apply(categorize_sessions)

    # Count groups in each cohort
    cohort_counts = class_sessions['Cohort'].value_counts().reindex(
        ["0-10 sessions", "11-20 sessions", "21-30 sessions", "31+ sessions"],
        fill_value=0
    )

    # Display cohort distribution
    st.subheader("Group Distribution by Session Count")

    col1, col2 = st.columns([1, 1])

    with col1:
        # Create DataFrame for display
        cohort_df = pd.DataFrame({
            'Session Range': cohort_counts.index,
            'Number of Groups': cohort_counts.values,
            'Percentage': (cohort_counts.values / len(class_sessions) * 100).round(1)
        })
        st.dataframe(cohort_df, width='stretch', hide_index=True)

    with col2:
        # Create bar chart
        fig_cohort = px.bar(
            cohort_df,
            x='Session Range',
            y='Number of Groups',
            title="Distribution of Groups by Session Count",
            color='Session Range',
            color_discrete_map={
                "0-10 sessions": "#FF6B6B",
                "11-20 sessions": "#FFD93D",
                "21-30 sessions": "#6BCF7F",
                "31+ sessions": "#4D96FF"
            }
        )
        fig_cohort.update_layout(showlegend=False)
        st.plotly_chart(fig_cohort, width='stretch')

    st.divider()

    # Show detailed group list
    st.subheader("Detailed Group Session List")

    # Sort by total sessions descending
    class_sessions_sorted = class_sessions.sort_values('Total Sessions', ascending=False)

    # Add rank
    class_sessions_sorted.insert(0, 'Rank', range(1, len(class_sessions_sorted) + 1))

    # Display with search
    search_term = st.text_input("Search for a specific group:", "")

    if search_term:
        filtered_groups = class_sessions_sorted[
            class_sessions_sorted['Group Name'].str.contains(search_term, case=False, na=False)
        ]
        st.info(f"Found {len(filtered_groups)} groups matching '{search_term}'")
        st.dataframe(filtered_groups, width='stretch', hide_index=True)
    else:
        st.dataframe(class_sessions_sorted, width='stretch', hide_index=True, height=400)

    # Export option
    st.markdown("### Export Group Data")
    csv = class_sessions_sorted.to_csv(index=False)
    st.download_button(
        label="Download NMB Group Session Report",
        data=csv,
        file_name=f"nmb_group_sessions_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )


# MAIN APP STARTS HERE
st.title("2026 Sessions Analysis")
st.caption("Data updated nightly from TeamPact.")

# Load the 2026 data from parquet
@st.cache_data(ttl=3600)
def load_data():
    return load_sessions_2026()

try:
    df = load_data()

    if df.empty:
        st.warning("No data found for 2026.")
        st.info("Data is automatically refreshed nightly via cron job. If you need immediate data, contact your system administrator.")
        st.stop()

    # Filter out training/example submissions
    if 'participant_name' in df.columns:
        df = df[df['participant_name'] != 'Buyi Xaba (example)']

except Exception as e:
    st.error(f"Error loading 2026 session data: {e}")

    # Show recovery options
    st.subheader("Data Loading Issues")

    with st.expander("Error Details"):
        import traceback
        st.code(traceback.format_exc())

    with st.expander("Troubleshooting"):
        st.markdown("""
        **Common Solutions:**
        1. **Parquet file**: Verify that `data/parquet/raw/2026_sessions.parquet` exists
        2. **Data Refresh**: Data is automatically refreshed nightly via cron job
        3. **Manual Refresh**: If needed, contact your system administrator to trigger a manual data sync
        """)

    st.stop()

# School type and mentor classification are now handled in the database loading function

# CREATE TABS FOR DIFFERENT VIEWS
tab1, tab2, tab3 = st.tabs(["EA Sessions Analysis", "Children's Sessions", "Group Sessions"])

with tab1:
    display_session_analysis(df)

with tab2:
    display_children_session_analysis(df)

with tab3:
    display_class_session_analysis(df)

# RAW DATA EXPORT SECTION
st.divider()
st.header("Raw Data Export")
st.markdown(
    f"Download the complete raw 2026 dataset. "
    f"This export includes **{len(df):,} records** with all available columns "
    f"for research and analysis purposes."
)

# Show available columns
with st.expander("View available columns"):
    column_list = df.columns.tolist()
    st.write(f"**{len(column_list)} columns available:**")
    st.code(", ".join(column_list))

@st.cache_data
def convert_full_dataset_to_csv(_dataframe):
    """Cache the CSV conversion to avoid re-generating on every interaction"""
    return _dataframe.to_csv(index=False)

raw_csv = convert_full_dataset_to_csv(df)

st.download_button(
    label=f"Download Full 2026 Dataset ({len(df):,} records)",
    data=raw_csv,
    file_name=f"teampact_sessions_2026_raw_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv",
    type="primary"
)
