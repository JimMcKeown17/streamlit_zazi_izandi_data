import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import sys
import os
import json

# Add the project root to the path so we can import modules
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Import data sources
try:
    from data_loader import load_sessions_2025
    from data.mentor_schools import mentors_to_schools
except ImportError as e:
    st.error(f"Import error: {e}")

# Configuration for letter progress API
DJANGO_API_URL = "http://zazi-izandi.co.za/api/letter-progress/"

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_letter_progress_data():
    """Fetch letter progress data from Django API"""
    try:
        response = requests.get(DJANGO_API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch letter progress data: {e}")
        return None

def get_expected_letters_for_group(letter_sequence, group_progress_index):
    """Get the expected letters a group should be working on based on their progress"""
    if group_progress_index < 0 or group_progress_index >= len(letter_sequence):
        return []
    
    # Return current letter and next few letters they should be working on
    current_index = group_progress_index
    expected_letters = []
    
    # Add current letter
    if current_index < len(letter_sequence):
        expected_letters.append(letter_sequence[current_index])
    
    # Add next 1-2 letters for review/preparation
    for i in range(1, 3):
        if current_index + i < len(letter_sequence):
            expected_letters.append(letter_sequence[current_index + i])
    
    return expected_letters

def analyze_teaching_sequence(session_data, letter_progress_data):
    """Analyze if letters being taught follow the correct sequence"""
    sequence_results = []
    
    if not letter_progress_data:
        st.warning("No letter sequence data available - using basic analysis")
        letter_sequence = ['s', 'a', 't', 'i', 'p', 'n', 'c', 'k', 'e', 'h', 'r', 'm', 'd', 'g', 'o', 'u', 'l', 'f', 'b', 'j', 'z', 'w', 'v', 'x', 'y', 'q']  # Default sequence
    else:
        letter_sequence = letter_progress_data.get('letter_sequence', [])
    
    # Debug: Show letter sequence
    st.write("🔍 **Letter Sequence Being Used:**")
    st.write(f"Total letters in sequence: {len(letter_sequence)}")
    st.write(f"Sequence: {', '.join(letter_sequence[:10])}..." if len(letter_sequence) > 10 else f"Sequence: {', '.join(letter_sequence)}")
    
    # Group sessions by EA and group to track progress
    session_groups = session_data.groupby(['user_name', 'class_name'])
    
    st.write(f"🔍 **Found {len(session_groups)} unique EA-Group combinations**")
    
    for (ea_name, class_name), group_sessions in session_groups:
        # Extract group name from class_name
        if 'Group' in class_name:
            group_part = class_name.split('-')[1] if '-' in class_name else class_name
            group_name = group_part.strip()
        else:
            group_name = "Group Unknown"
        
        # Sort sessions by date to track progression
        group_sessions_sorted = group_sessions.sort_values('session_started_at')
        
        # Track which letters have been taught by this group
        letters_taught_so_far = set()
        
        for _, session in group_sessions_sorted.iterrows():
            letters_in_session = session.get('letters_taught', '')
            session_date = session.get('session_started_at', '')
            school_name = session.get('program_name', '')
            
            if letters_in_session and isinstance(letters_in_session, str):
                session_letters = [letter.strip().lower() for letter in letters_in_session.split(',')]
            else:
                session_letters = []
            
            # Analyze each letter taught in this session
            for letter in session_letters:
                if letter in letter_sequence:
                    letter_index = letter_sequence.index(letter)
                    
                    # Check if this letter should be taught yet based on sequence
                    letters_before = set(letter_sequence[:letter_index])
                    
                    # Calculate how many prerequisite letters have been taught
                    prereq_taught = len(letters_before.intersection(letters_taught_so_far))
                    prereq_total = len(letters_before)
                    
                    # This is a simple heuristic - letter is "correct" if most prerequisites have been covered
                    sequence_adherence = prereq_taught / prereq_total if prereq_total > 0 else 1.0
                    
                    # Add to tracking
                    letters_taught_so_far.add(letter)
                    
                    sequence_results.append({
                        'ea_name': ea_name,
                        'group_name': group_name,
                        'class_name': class_name,
                        'school': school_name,
                        'session_date': session_date,
                        'letter_taught': letter,
                        'letter_sequence_index': letter_index,
                        'prerequisite_letters_taught': prereq_taught,
                        'prerequisite_letters_total': prereq_total,
                        'sequence_adherence_score': sequence_adherence,
                        'letters_taught_so_far': len(letters_taught_so_far),
                        'session_id': session.get('session_id', ''),
                        'duration': session.get('total_duration_minutes', 0),
                        'session_text': session.get('session_text', ''),
                        'all_session_letters': letters_in_session
                    })
    
    st.write(f"🔍 **Analysis Complete:** Generated {len(sequence_results)} letter teaching records")
    
    return pd.DataFrame(sequence_results)

def display_ea_overview(sequence_df):
    """Display overview of EA performance"""
    st.subheader("📋 Education Assistant Overview")
    
    if sequence_df.empty:
        st.warning("No sequence analysis data available.")
        return
    
    # Calculate EA-level statistics
    ea_stats = sequence_df.groupby('ea_name').agg({
        'sequence_adherence_score': 'mean',
        'session_id': 'nunique',
        'group_name': 'nunique',
        'letter_taught': 'count',
        'letter_sequence_index': 'max'
    }).round(3)
    
    ea_stats.columns = ['Avg_Sequence_Adherence', 'Total_Sessions', 'Unique_Groups', 'Total_Letters_Taught', 'Max_Letter_Index']
    ea_stats = ea_stats.reset_index()
    ea_stats['Sequence_Adherence_Percentage'] = (ea_stats['Avg_Sequence_Adherence'] * 100).round(1)
    
    # Sort by sequence adherence descending
    ea_stats = ea_stats.sort_values('Avg_Sequence_Adherence', ascending=False)
    
    # Format the display table
    display_ea_stats = ea_stats.copy()
    display_ea_stats['Avg_Sequence_Adherence'] = display_ea_stats['Avg_Sequence_Adherence'].round(3)
    display_ea_stats = display_ea_stats[['ea_name', 'Sequence_Adherence_Percentage', 'Total_Sessions', 'Unique_Groups', 'Total_Letters_Taught', 'Max_Letter_Index']]
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        avg_adherence = sequence_df['sequence_adherence_score'].mean() * 100
        st.metric("Overall Sequence Adherence", f"{avg_adherence:.1f}%")
    
    with col2:
        total_eas = sequence_df['ea_name'].nunique()
        st.metric("Total EAs Analyzed", total_eas)
    
    with col3:
        high_adherence_eas = (ea_stats['Avg_Sequence_Adherence'] >= 0.8).sum()
        st.metric("EAs with >80% Adherence", high_adherence_eas)
    
    with col4:
        total_letters = len(sequence_df)
        st.metric("Total Letters Analyzed", total_letters)
    
    # Display EA performance table
    st.subheader("EA Performance Summary")
    
    # Color code the sequence adherence column
    def highlight_adherence(val):
        if val >= 80:
            return 'background-color: #ccffcc'  # Light green
        elif val >= 60:
            return 'background-color: #ffffcc'  # Light yellow
        else:
            return 'background-color: #ffcccc'  # Light red
    
    styled_table = display_ea_stats.style.map(
        highlight_adherence, 
        subset=['Sequence_Adherence_Percentage']
    )
    
    st.dataframe(styled_table, width='stretch')
    
    # Sequence adherence distribution chart
    st.subheader("Letter Sequence Adherence Distribution")
    fig = px.histogram(
        ea_stats, 
        x='Sequence_Adherence_Percentage', 
        nbins=10,
        title="Distribution of EA Letter Sequence Adherence",
        labels={'Sequence_Adherence_Percentage': 'Sequence Adherence (%)', 'count': 'Number of EAs'}
    )
    st.plotly_chart(fig, width='stretch')

def display_individual_ea_analysis(sequence_df, session_data):
    """Display detailed analysis for individual EAs"""
    st.subheader("🎯 Individual EA Analysis")
    
    if sequence_df.empty:
        st.warning("No data available for individual analysis.")
        return
    
    # EA selector
    ea_names = sorted(sequence_df['ea_name'].unique())
    selected_ea = st.selectbox("Select Education Assistant:", ea_names)
    
    if not selected_ea:
        return
    
    # Filter data for selected EA
    ea_data = sequence_df[sequence_df['ea_name'] == selected_ea]
    ea_sessions = session_data[session_data['user_name'] == selected_ea]
    
    # EA overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_adherence = ea_data['sequence_adherence_score'].mean() * 100
        st.metric("Average Sequence Adherence", f"{avg_adherence:.1f}%")
    
    with col2:
        unique_sessions = ea_data['session_id'].nunique()
        st.metric("Unique Sessions", unique_sessions)
    
    with col3:
        unique_groups = ea_data['group_name'].nunique()
        st.metric("Groups Taught", unique_groups)
    
    with col4:
        total_letters = len(ea_data)
        st.metric("Letters Taught", total_letters)
    
    # Daily activity for selected EA
    st.subheader(f"Daily Teaching Activity - {selected_ea}")
    
    # Convert session_date to datetime and create daily summary
    ea_data['session_date'] = pd.to_datetime(ea_data['session_date'])
    daily_activity = ea_data.groupby(ea_data['session_date'].dt.date).agg({
        'sequence_adherence_score': 'mean',
        'session_id': 'nunique',
        'group_name': 'nunique'
    }).reset_index()
    daily_activity.columns = ['Date', 'Avg_Adherence', 'Sessions', 'Groups']
    daily_activity['Adherence_Percentage'] = daily_activity['Avg_Adherence'] * 100
    
    # Plot daily adherence trend
    if not daily_activity.empty:
        fig = px.line(
            daily_activity,
            x='Date',
            y='Adherence_Percentage',
            title=f"Letter Sequence Adherence Over Time - {selected_ea}",
            labels={'Adherence_Percentage': 'Sequence Adherence (%)', 'Date': 'Date'}
        )
        fig.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="Target: 80%")
        fig.update_layout(yaxis=dict(range=[0, 100]))
        st.plotly_chart(fig, width='stretch')
    
    # Group-level analysis for selected EA
    st.subheader(f"Group-Level Performance - {selected_ea}")
    
    group_stats = ea_data.groupby('group_name').agg({
        'sequence_adherence_score': 'mean',
        'session_id': 'nunique',
        'letter_taught': 'count',
        'letter_sequence_index': 'max'
    }).round(3)
    
    group_stats.columns = ['Avg_Adherence', 'Sessions', 'Letters_Taught', 'Max_Letter_Index']
    group_stats['Adherence_Percentage'] = (group_stats['Avg_Adherence'] * 100).round(1)
    group_stats = group_stats.reset_index()
    group_stats = group_stats.sort_values('Avg_Adherence', ascending=False)
    
    st.dataframe(group_stats, width='stretch')
    
    # Recent sessions detail
    st.subheader(f"Recent Letter Teaching - {selected_ea}")
    
    # Show last 20 letter teaching records
    recent_letters = ea_data.sort_values('session_date', ascending=False).head(20)
    
    display_columns = [
        'session_date', 'group_name', 'letter_taught', 'letter_sequence_index',
        'sequence_adherence_score', 'prerequisite_letters_taught', 'prerequisite_letters_total'
    ]
    
    # Format the display
    recent_display = recent_letters[display_columns].copy()
    recent_display['session_date'] = pd.to_datetime(recent_display['session_date']).dt.strftime('%Y-%m-%d %H:%M')
    recent_display['sequence_adherence_score'] = (recent_display['sequence_adherence_score'] * 100).round(1)
    recent_display.columns = [
        'Session Date', 'Group', 'Letter Taught', 'Letter Index',
        'Adherence %', 'Prerequisites Met', 'Prerequisites Total'
    ]
    
    st.dataframe(recent_display, width='stretch')

def display_summary_statistics(sequence_df):
    """Display summary statistics about letter sequence adherence"""
    st.subheader("📊 Letter Sequence Summary Statistics")
    
    if sequence_df.empty:
        st.warning("No data available for summary statistics.")
        return
    
    # Overall statistics
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Overall Performance Metrics**")
        
        total_letters = len(sequence_df)
        high_adherence_letters = (sequence_df['sequence_adherence_score'] >= 0.8).sum()
        medium_adherence_letters = ((sequence_df['sequence_adherence_score'] >= 0.6) & (sequence_df['sequence_adherence_score'] < 0.8)).sum()
        low_adherence_letters = (sequence_df['sequence_adherence_score'] < 0.6).sum()
        
        st.metric("Total Letters Analyzed", total_letters)
        st.metric("High Adherence Letters (≥80%)", f"{high_adherence_letters} ({high_adherence_letters/total_letters*100:.1f}%)")
        st.metric("Medium Adherence Letters (60-79%)", f"{medium_adherence_letters} ({medium_adherence_letters/total_letters*100:.1f}%)")
        st.metric("Low Adherence Letters (<60%)", f"{low_adherence_letters} ({low_adherence_letters/total_letters*100:.1f}%)")
    
    with col2:
        st.markdown("**Letter Progression Statistics**")
        
        unique_sessions = sequence_df['session_id'].nunique()
        unique_eas = sequence_df['ea_name'].nunique()
        unique_groups = sequence_df['group_name'].nunique()
        avg_letter_index = sequence_df['letter_sequence_index'].mean()
        
        st.metric("Unique Sessions", unique_sessions)
        st.metric("Education Assistants", unique_eas)
        st.metric("Learning Groups", unique_groups)
        st.metric("Average Letter Index", f"{avg_letter_index:.1f}")
    
    # Adherence by school
    st.subheader("Letter Sequence Adherence by School")
    
    school_stats = sequence_df.groupby('school').agg({
        'sequence_adherence_score': 'mean',
        'session_id': 'nunique',
        'ea_name': 'nunique'
    }).round(3)
    
    school_stats.columns = ['Avg_Adherence', 'Total_Sessions', 'Unique_EAs']
    school_stats['Adherence_Percentage'] = (school_stats['Avg_Adherence'] * 100).round(1)
    school_stats = school_stats.reset_index()
    school_stats = school_stats.sort_values('Avg_Adherence', ascending=False)
    
    # Bar chart of school performance
    fig = px.bar(
        school_stats,
        x='school',
        y='Adherence_Percentage',
        title="Average Letter Sequence Adherence by School",
        labels={'Adherence_Percentage': 'Sequence Adherence (%)', 'school': 'School'}
    )
    fig.add_hline(y=80, line_dash="dash", line_color="green", annotation_text="Target: 80%")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, width='stretch')
    
    # Display school table
    st.dataframe(school_stats, width='stretch')

def display_session_quality_review():
    """Main function to display the session quality review page"""
    # Authentication guard
    if 'user' not in st.session_state or st.session_state.user is None:
        st.error("Please log in to access this page")
        return
    
    st.title("📚 Session Quality Review")
    st.markdown("Monitor Education Assistant performance and letter sequence adherence")
    
    # Load data
    with st.spinner("Loading session and letter progress data..."):
        # Load session data
        try:
            session_data = load_sessions_2025()
            if session_data.empty:
                st.warning("No session data found. Please check the database connection.")
                return
        except Exception as e:
            st.error(f"Error loading session data: {e}")
            return
        
        # Debug: Show session data info
        with st.expander("🔍 Debug Info - Session Data"):
            st.write(f"Session data shape: {session_data.shape}")
            st.write("Column names:")
            st.write(list(session_data.columns))
            st.write("Sample row:")
            if not session_data.empty:
                st.write(session_data.iloc[0].to_dict())
        
        # Load letter progress data
        letter_progress_data = fetch_letter_progress_data()
        if not letter_progress_data:
            st.warning("Could not load letter progress data. Some features may be limited.")
        else:
            with st.expander("🔍 Debug Info - Letter Progress Data"):
                st.write("Letter progress data keys:")
                st.write(list(letter_progress_data.keys()) if letter_progress_data else "None")
                if letter_progress_data and 'data_by_school' in letter_progress_data:
                    schools = list(letter_progress_data['data_by_school'].keys())
                    st.write(f"Schools in letter progress: {schools[:5]}...")  # Show first 5
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Date range filter
    max_date = pd.to_datetime(session_data['session_started_at']).max().date()
    min_date = max_date - timedelta(days=30)
    
    date_range = st.sidebar.date_input(
        "Select date range:",
        value=(min_date, max_date),
        min_value=pd.to_datetime(session_data['session_started_at']).min().date(),
        max_value=max_date
    )
    
    # Filter session data by date
    if len(date_range) == 2:
        start_date, end_date = date_range
        session_data['session_date'] = pd.to_datetime(session_data['session_started_at']).dt.date
        session_data = session_data[
            (session_data['session_date'] >= start_date) & 
            (session_data['session_date'] <= end_date)
        ]
    
    # School filter
    if 'program_name' in session_data.columns:
        school_options = ['All Schools'] + sorted(session_data['program_name'].unique())
        selected_school = st.sidebar.selectbox("Select School:", school_options)
        
        if selected_school != 'All Schools':
            session_data = session_data[session_data['program_name'] == selected_school]
    
    # EA filter
    ea_options = ['All EAs'] + sorted(session_data['user_name'].unique())
    selected_ea = st.sidebar.selectbox("Select EA:", ea_options)
    
    if selected_ea != 'All EAs':
        session_data = session_data[session_data['user_name'] == selected_ea]
    
    st.sidebar.markdown(f"**Filtered Sessions:** {len(session_data)}")
    
    # Analyze teaching sequence
    with st.spinner("Analyzing letter sequence adherence..."):
        sequence_df = analyze_teaching_sequence(session_data, letter_progress_data)
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 EA Overview", "🎯 Individual Analysis", "📊 Summary Statistics"])
    
    with tab1:
        display_ea_overview(sequence_df)
    
    with tab2:
        display_individual_ea_analysis(sequence_df, session_data)
    
    with tab3:
        display_summary_statistics(sequence_df)
    
    # Export functionality
    st.divider()
    st.subheader("📥 Export Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not sequence_df.empty:
            csv_sequence = sequence_df.to_csv(index=False)
            st.download_button(
                label="Download Letter Sequence Analysis",
                data=csv_sequence,
                file_name=f"letter_sequence_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    with col2:
        csv_sessions = session_data.to_csv(index=False)
        st.download_button(
            label="Download Filtered Session Data",
            data=csv_sessions,
            file_name=f"filtered_sessions_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

# Call the main function
display_session_quality_review()