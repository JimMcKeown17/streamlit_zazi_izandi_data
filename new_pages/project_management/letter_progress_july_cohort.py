import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import sys
import os

# Ensure the project root is on the import path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
from database_utils import get_database_engine, check_table_exists, get_mentor

# Letter sequence that EAs should be teaching
LETTER_SEQUENCE = [
    'a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p',
    's', 'h', 'z', 'n', 'd', 'y', 'f', 'w', 'v', 'x',
    'g', 't', 'q', 'r', 'c', 'j'
]

def detect_grade_from_groups(group_names):
    """Detect grade from group names - returns 'Grade R', 'Grade 1', 'Grade 2', or 'Unknown'"""
    if not group_names:
        return 'Unknown'

    # Check all group names for grade indicators
    grade_counts = {}

    for group_name in group_names:
        if not group_name:
            continue

        group_name = str(group_name).strip()

        # Check for Grade 1 patterns
        if (group_name.startswith('1 ') or group_name.startswith('1A') or group_name.startswith('1B') or
            group_name.startswith('1C') or group_name.startswith('1D') or group_name.startswith('1E') or
            group_name.startswith('1F') or 'Grade 1' in group_name):
            grade_counts['Grade 1'] = grade_counts.get('Grade 1', 0) + 1

        # Check for Grade 2 patterns
        elif (group_name.startswith('2 ') or group_name.startswith('2A') or group_name.startswith('2B') or
              group_name.startswith('2C') or group_name.startswith('2D') or 'Grade 2' in group_name):
            grade_counts['Grade 2'] = grade_counts.get('Grade 2', 0) + 1

        # Check for Grade R patterns
        elif (group_name.startswith('R ') or group_name.startswith('R A') or group_name.startswith('R B') or
              group_name.startswith('R C') or group_name.startswith('PreR') or 'Grade R' in group_name):
            grade_counts['Grade R'] = grade_counts.get('Grade R', 0) + 1

    # Return the most common grade, or 'Unknown' if none found
    if grade_counts:
        return max(grade_counts, key=grade_counts.get)
    else:
        return 'Unknown'


@st.cache_data
def fetch_teampact_session_data():
    """Load 2025 session data from frozen parquet file"""
    try:
        df = load_sessions_2025()

        # Select and rename columns to match expected format
        cols = {
            'session_id': 'session_id',
            'participant_name': 'participant_name',
            'user_name': 'user_name',
            'class_name': 'group_name',
            'program_name': 'school_name',
            'session_started_at': 'session_started_at',
            'letters_taught': 'letters_taught',
            'num_letters_taught': 'num_letters_taught',
            'attended_percentage': 'attended_percentage',
            'participant_total': 'participant_total',
            'attended_total': 'attended_total',
            'session_text': 'session_text',
        }
        df = df[list(cols.keys())].rename(columns=cols)

        # Filter to sessions with letters taught
        df = df[df['letters_taught'].notna() & (df['letters_taught'] != '')]
        df = df.sort_values('session_started_at', ascending=False)

        if df.empty:
            st.warning("No session data found with letter information.")
            return None

        return df

    except Exception as e:
        st.error(f"Failed to load session data: {e}")
        return None


def calculate_letter_progress(letters_taught_str, letter_sequence):
    """Calculate progress index and percentage based on letters taught"""
    if not letters_taught_str or letters_taught_str.strip() == '':
        return -1, 0.0, None
    
    # Split letters taught by comma and clean up
    letters_list = [letter.strip().lower() for letter in letters_taught_str.split(',') if letter.strip()]
    
    if not letters_list:
        return -1, 0.0, None
    
    # Find the rightmost (highest index) letter that has been taught
    max_index = -1
    rightmost_letter = None
    
    for letter in letters_list:
        if letter in letter_sequence:
            index = letter_sequence.index(letter)
            if index > max_index:
                max_index = index
                rightmost_letter = letter
    
    # Calculate progress percentage
    progress_percentage = ((max_index + 1) / len(letter_sequence)) * 100 if max_index >= 0 else 0.0
    
    return max_index, progress_percentage, rightmost_letter


def process_session_data(df):
    """Process session data to calculate letter progress for each group"""
    if df.empty:
        return {}
    
    # Calculate letter progress for each session
    df['progress_index'] = -1
    df['progress_percentage'] = 0.0
    df['rightmost_letter'] = None
    
    for idx, row in df.iterrows():
        progress_idx, progress_pct, rightmost = calculate_letter_progress(
            row['letters_taught'], LETTER_SEQUENCE
        )
        df.at[idx, 'progress_index'] = progress_idx
        df.at[idx, 'progress_percentage'] = progress_pct
        df.at[idx, 'rightmost_letter'] = rightmost
    
    # Group data by school -> TA -> group structure
    data_by_school = {}
    
    for school in df['school_name'].unique():
        school_data = df[df['school_name'] == school].copy()
        
        # Initialize school structure
        data_by_school[school] = {
            'summary': {
                'total_tas': 0,
                'total_groups': 0,
                'total_sessions': 0,
                'average_progress': 0.0
            },
            'ta_progress': {}
        }
        
        for ta in school_data['user_name'].unique():
            ta_data = school_data[school_data['user_name'] == ta].copy()

            # Detect grade from group names for this TA
            grade = detect_grade_from_groups(ta_data['group_name'].tolist())

            # Initialize TA structure
            data_by_school[school]['ta_progress'][ta] = {
                'mentor': get_mentor(school),
                'grade': grade,
                'summary': {
                    'total_sessions': 0,
                    'average_progress': 0.0
                },
                'groups': {}
            }
            
            for group in ta_data['group_name'].unique():
                group_data = ta_data[ta_data['group_name'] == group].copy()
                
                # Get the most recent session for this group
                latest_session = group_data.loc[group_data['session_started_at'].idxmax()]
                
                # Calculate group statistics
                session_count = len(group_data)
                last_session_date = latest_session['session_started_at']
                
                # Use the progress from the most recent session
                progress_index = latest_session['progress_index']
                progress_percentage = latest_session['progress_percentage']
                rightmost_letter = latest_session['rightmost_letter']
                
                # Store group information
                data_by_school[school]['ta_progress'][ta]['groups'][group] = {
                    'progress_index': int(progress_index) if progress_index >= 0 else 0,
                    'progress_percentage': float(progress_percentage),
                    'session_count': session_count,
                    'last_session_date': last_session_date.isoformat() if pd.notna(last_session_date) else None,
                    'rightmost_letter': rightmost_letter,
                    'recent_activities': {
                        'flash_cards_used': False,  # Not available in current data
                        'board_game_used': False,   # Not available in current data
                        'comments': latest_session.get('session_text', '')
                    }
                }
        
        # Calculate summaries
        all_ta_progress = []
        total_sessions = 0
        total_groups = 0
        
        for ta_name, ta_info in data_by_school[school]['ta_progress'].items():
            ta_sessions = 0
            ta_progress_values = []
            
            for group_name, group_info in ta_info['groups'].items():
                ta_sessions += group_info['session_count']
                ta_progress_values.append(group_info['progress_percentage'])
                total_groups += 1
            
            total_sessions += ta_sessions
            ta_avg_progress = sum(ta_progress_values) / len(ta_progress_values) if ta_progress_values else 0.0
            all_ta_progress.append(ta_avg_progress)
            
            # Update TA summary
            data_by_school[school]['ta_progress'][ta_name]['summary']['total_sessions'] = ta_sessions
            data_by_school[school]['ta_progress'][ta_name]['summary']['average_progress'] = ta_avg_progress
        
        # Update school summary
        data_by_school[school]['summary']['total_tas'] = len(data_by_school[school]['ta_progress'])
        data_by_school[school]['summary']['total_groups'] = total_groups
        data_by_school[school]['summary']['total_sessions'] = total_sessions
        data_by_school[school]['summary']['average_progress'] = sum(all_ta_progress) / len(all_ta_progress) if all_ta_progress else 0.0
    
    return data_by_school


def prepare_grade_summary(all_data):
    """Prepare grade-specific summary data for dashboard"""
    grade_data = {'Grade R': [], 'Grade 1': [], 'Grade 2': []}
    school_grade_data = {}

    for school_name, school_data in all_data.items():
        school_grade_data[school_name] = {'Grade R': [], 'Grade 1': [], 'Grade 2': []}

        for ta_name, ta_data in school_data['ta_progress'].items():
            grade = (ta_data.get('grade') or '').strip()
            if grade in ['Grade R', 'Grade 1', 'Grade 2']:
                ta_avg_progress = ta_data['summary']['average_progress']
                grade_data[grade].append(ta_avg_progress)
                school_grade_data[school_name][grade].append(ta_avg_progress)

    # Calculate averages
    summary = {
        'grade_r_avg': sum(grade_data['Grade R']) / len(grade_data['Grade R']) if grade_data['Grade R'] else 0,
        'grade_1_avg': sum(grade_data['Grade 1']) / len(grade_data['Grade 1']) if grade_data['Grade 1'] else 0,
        'grade_2_avg': sum(grade_data['Grade 2']) / len(grade_data['Grade 2']) if grade_data['Grade 2'] else 0,
        'school_averages': {}
    }
    
    # Calculate school averages by grade
    for school, grades in school_grade_data.items():
        summary['school_averages'][school] = {
            'Grade R': sum(grades['Grade R']) / len(grades['Grade R']) if grades['Grade R'] else 0,
            'Grade 1': sum(grades['Grade 1']) / len(grades['Grade 1']) if grades['Grade 1'] else 0,
            'Grade 2': sum(grades['Grade 2']) / len(grades['Grade 2']) if grades['Grade 2'] else 0
        }
    
    return summary


def create_grade_charts(grade_summary):
    """Create bar charts for grade progress by school"""
    school_data = []
    
    for school, grades in grade_summary['school_averages'].items():
        if grades['Grade R'] > 0:  # Only include schools with Grade R data
            school_data.append({
                'School': school,
                'Grade': 'Grade R',
                'Average Progress': grades['Grade R']
            })
        if grades['Grade 1'] > 0:  # Only include schools with Grade 1 data
            school_data.append({
                'School': school,
                'Grade': 'Grade 1',
                'Average Progress': grades['Grade 1']
            })
        if grades['Grade 2'] > 0:  # Only include schools with Grade 2 data
            school_data.append({
                'School': school,
                'Grade': 'Grade 2',
                'Average Progress': grades['Grade 2']
            })
    
    if school_data:
        df = pd.DataFrame(school_data)
        
        # Create separate charts for each grade
        grade_r_df = df[df['Grade'] == 'Grade R']
        grade_1_df = df[df['Grade'] == 'Grade 1']
        grade_2_df = df[df['Grade'] == 'Grade 2']

        charts = {}

        if not grade_r_df.empty:
            # Sort by Average Progress descending
            grade_r_df = grade_r_df.sort_values('Average Progress', ascending=False)
            charts['R'] = px.bar(
                grade_r_df,
                x='School',
                y='Average Progress',
                title='Average Progress by School - Grade R (Recent 2 Weeks)',
                color_discrete_sequence=['#ffc107']
            )
            charts['R'].update_layout(
                xaxis_title="School",
                yaxis_title="Average Progress (%)",
                yaxis=dict(range=[0, 100])
            )

        if not grade_1_df.empty:
            # Sort by Average Progress descending
            grade_1_df = grade_1_df.sort_values('Average Progress', ascending=False)
            charts['1'] = px.bar(
                grade_1_df,
                x='School',
                y='Average Progress',
                title='Average Progress by School - Grade 1 (Recent 2 Weeks)',
                color_discrete_sequence=['#28a745']
            )
            charts['1'].update_layout(
                xaxis_title="School",
                yaxis_title="Average Progress (%)",
                yaxis=dict(range=[0, 100])
            )

        if not grade_2_df.empty:
            # Sort by Average Progress descending
            grade_2_df = grade_2_df.sort_values('Average Progress', ascending=False)
            charts['2'] = px.bar(
                grade_2_df,
                x='School',
                y='Average Progress',
                title='Average Progress by School - Grade 2 (Recent 2 Weeks)',
                color_discrete_sequence=['#17a2b8']
            )
            charts['2'].update_layout(
                xaxis_title="School",
                yaxis_title="Average Progress (%)",
                yaxis=dict(range=[0, 100])
            )
        
        return charts
    
    return {}


def main():
    st.title("📚 Letter Progress Dashboard - Recent 2 Weeks")

    # Add info about data source
    st.info("This dashboard shows letter progress data from TeamPact sessions for the most recent 2 weeks of data.")

    try:
        # Check if table exists
        if not check_table_exists():
            st.error("The TeamPact sessions table does not exist. Please run the data sync process first.")
            return

        # Fetch data from database (most recent 2 weeks)
        session_df = fetch_teampact_session_data()

        if session_df is None:
            st.error("Failed to fetch data from database.")
            return
        elif session_df.empty:
            st.warning("No session data found for the recent 2 weeks. Please check if sessions have been recorded recently.")
            return
        # Process data into the format expected by the visualization functions
        all_data = process_session_data(session_df)

        if not all_data:
            st.warning("No processed data available.")
            return

        # Create metadata structure for consistency with original
        metadata = {
            'total_schools': len(all_data),
            'total_tas': sum(school['summary']['total_tas'] for school in all_data.values()),
            'total_groups': sum(school['summary']['total_groups'] for school in all_data.values()),
            'generated_at': datetime.now().isoformat()
        }

        # Display overall metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total TAs", metadata['total_tas'])
        with col2:
            st.metric("Total Groups", metadata['total_groups'])
        with col3:
            st.metric("Total Schools", metadata['total_schools'])

        # Prepare grade summary data
        grade_summary = prepare_grade_summary(all_data)

        # Grade averages
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Grade R Average Progress",
                f"{grade_summary['grade_r_avg']:.1f}%",
                help="Average progress across all Grade R TAs in recent 2 weeks"
            )
        with col2:
            st.metric(
                "Grade 1 Average Progress",
                f"{grade_summary['grade_1_avg']:.1f}%",
                help="Average progress across all Grade 1 TAs in recent 2 weeks"
            )
        with col3:
            st.metric(
                "Grade 2 Average Progress",
                f"{grade_summary['grade_2_avg']:.1f}%",
                help="Average progress across all Grade 2 TAs in recent 2 weeks"
            )
        with col4:
            # Calculate overall average
            all_grades = []
            for school_data in all_data.values():
                for ta_data in school_data['ta_progress'].values():
                    grade = (ta_data.get('grade') or '').strip()
                    if grade in ['Grade R', 'Grade 1', 'Grade 2']:
                        all_grades.append(ta_data['summary']['average_progress'])

            overall_avg = sum(all_grades) / len(all_grades) if all_grades else 0
            st.metric(
                "Overall Average Progress",
                f"{overall_avg:.1f}%",
                help="Average progress across all grades in recent 2 weeks"
            )

        # Grade progress charts
        charts = create_grade_charts(grade_summary)

        if charts:
            st.subheader("Progress by School and Grade - Recent 2 Weeks")

            if 'R' in charts:
                st.plotly_chart(charts['R'], width='stretch')

            if '1' in charts:
                st.plotly_chart(charts['1'], width='stretch')

            if '2' in charts:
                st.plotly_chart(charts['2'], width='stretch')

        st.divider()

        # Show data source information
        with st.expander("Data Source Information"):
            st.write(f"**Data fetched from:** TeamPact Sessions Database")
            st.write(f"**Total sessions processed:** {len(session_df)}")
            st.write(f"**Date range:** Recent 2 weeks")
            st.write(f"**Letter sequence used:** {', '.join(LETTER_SEQUENCE)}")

            # Show sample of raw data
            if not session_df.empty:
                st.write("**Sample session data:**")
                sample_df = session_df[['user_name', 'school_name', 'group_name', 'letters_taught', 'session_started_at']].head(5)
                st.dataframe(sample_df, width='stretch', hide_index=True)

    except Exception as e:
        st.error(f"Error during page execution: {e}")
        st.write("Please check the error details and try refreshing the page.")
        import traceback
        st.code(traceback.format_exc())
        return


main()