import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from collections import Counter
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

# East London Schools List
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

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_teampact_session_data():
    """Fetch session data from TeamPact database"""
    try:
        if not check_table_exists():
            st.error("TeamPact sessions table not found. Please ensure data has been synced.")
            return None
        
        engine = get_database_engine()
        
        # Query to get session data with letters taught (recent 2 weeks)
        query = """
        SELECT
            session_id,
            participant_name,
            user_name,
            class_name as group_name,
            program_name as school_name,
            session_started_at,
            letters_taught,
            num_letters_taught,
            attended_percentage,
            participant_total,
            attended_total,
            session_text
        FROM teampact_sessions_complete
        WHERE letters_taught IS NOT NULL
        AND letters_taught <> ''
        AND session_started_at >= NOW() - INTERVAL '14 days'
        ORDER BY session_started_at DESC
        """
        
        df = pd.read_sql(query, engine)
        
        if df.empty:
            st.warning("No session data found with letter information for recent 2 weeks.")
            return None
            
        return df
        
    except Exception as e:
        st.error(f"Failed to fetch data from database: {e}")
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


def check_ta_flag(ta_data):
    """Check if a TA should be flagged for having 3+ groups with same progress_index"""
    progress_indices = []
    for group_data in ta_data['groups'].values():
        progress_indices.append(group_data['progress_index'])
    
    # Count occurrences of each progress_index
    progress_counts = Counter(progress_indices)
    
    # Check if any progress_index appears 3 or more times
    for count in progress_counts.values():
        if count >= 3:
            return True
    return False


def analyze_flagged_tas(all_data):
    """Analyze all TAs and return flagged ones with statistics"""
    flagged_tas = []
    total_tas = 0
    
    for school_name, school_data in all_data.items():
        for ta_name, ta_data in school_data['ta_progress'].items():
            total_tas += 1
            is_flagged = check_ta_flag(ta_data)
            
            if is_flagged:
                # Get progress_index counts for flagged TA
                progress_indices = [group_data['progress_index'] for group_data in ta_data['groups'].values()]
                progress_counts = Counter(progress_indices)
                
                # Find which progress_index values have 3+ occurrences
                flagged_indices = [index for index, count in progress_counts.items() if count >= 3]
                
                flagged_tas.append({
                    'name': ta_name,
                    'school': school_name,
                    'mentor': ta_data.get('mentor', 'N/A'),
                    'total_groups': len(ta_data['groups']),
                    'flagged_indices': flagged_indices,
                    'progress_counts': dict(progress_counts)
                })
    
    flagged_percentage = (len(flagged_tas) / total_tas * 100) if total_tas > 0 else 0
    
    return {
        'flagged_tas': flagged_tas,
        'total_tas': total_tas,
        'flagged_count': len(flagged_tas),
        'flagged_percentage': flagged_percentage
    }


def render_letter_grid(letters_sequence, progress_index, rightmost_letter=None):
    """Render the letter progress grid"""
    cols = st.columns(26)  # 26 letters

    for idx, letter in enumerate(letters_sequence):
        with cols[idx]:
            if idx <= progress_index:
                # Completed letter - yellow background
                # Highlight the rightmost letter differently if provided
                if rightmost_letter and letter == rightmost_letter:
                    st.markdown(
                        f"<div style='background-color: #ff9800; border: 2px solid #ff6b00; "
                        f"padding: 4px; text-align: center; border-radius: 4px;'>"
                        f"<b>{letter}</b></div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<div style='background-color: #ffc107; border: 1px solid #ddd; "
                        f"padding: 4px; text-align: center; border-radius: 4px;'>"
                        f"<b>{letter}</b></div>",
                        unsafe_allow_html=True
                    )
            else:
                # Not completed letter - gray background
                st.markdown(
                    f"<div style='background-color: #f8f9fa; border: 1px solid #ddd; "
                    f"padding: 4px; text-align: center; border-radius: 4px;'>"
                    f"{letter}</div>",
                    unsafe_allow_html=True
                )


def create_recent_sessions_table(session_df, selected_school):
    """Create a table of recent sessions for the selected school"""
    if session_df is None or session_df.empty:
        return None

    # Filter sessions for the selected school
    school_sessions = session_df[session_df['school_name'] == selected_school].copy()

    if school_sessions.empty:
        return None

    # Format the datetime and prepare display columns
    school_sessions['formatted_date'] = pd.to_datetime(school_sessions['session_started_at']).dt.strftime('%Y-%m-%d %H:%M')

    # Select and rename columns for display
    display_sessions = school_sessions[[
        'formatted_date', 'user_name', 'group_name', 'participant_name',
        'letters_taught', 'num_letters_taught', 'session_text'
    ]].rename(columns={
        'formatted_date': 'Date & Time',
        'user_name': 'EA Name',
        'group_name': 'Group',
        'participant_name': 'Student',
        'letters_taught': 'Letters Worked On',
        'num_letters_taught': 'Letter Count',
        'session_text': 'Comments'
    })

    # Sort by date descending
    display_sessions = display_sessions.sort_values('Date & Time', ascending=False)

    return display_sessions


def display_school_data(school_data, letter_sequence):
    """Display data for a single school"""
    # School summary
    summary = school_data['summary']
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("School Average Progress", f"{summary['average_progress']:.1f}%")
    with col2:
        st.metric("Total Sessions", summary['total_sessions'])
    with col3:
        st.metric("Active TAs", summary['total_tas'])

    st.divider()

    # Display TA progress
    for ta_name, ta_data in school_data['ta_progress'].items():
        # Check if this TA should be flagged
        is_flagged = check_ta_flag(ta_data)
        flag_emoji = "🚩 " if is_flagged else ""
        
        # TA Section
        with st.expander(f"{flag_emoji}**{ta_name}**", expanded=True):
            # TA info
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            with col1:
                if ta_data.get('grade'):
                    st.caption(f"Grade: {ta_data['grade']}")
            with col2:
                if ta_data.get('mentor'):
                    st.caption(f"Mentor: {ta_data['mentor']}")
            with col3:
                st.caption(f"Sessions: {ta_data['summary']['total_sessions']}")
            with col4:
                st.caption(f"Avg Progress: {ta_data['summary']['average_progress']:.1f}%")
            
            # Show warning if TA is flagged
            if is_flagged:
                progress_indices = [group_data['progress_index'] for group_data in ta_data['groups'].values()]
                progress_counts = Counter(progress_indices)
                flagged_indices = [index for index, count in progress_counts.items() if count >= 3]
                
                warning_text = "⚠️ **Alert:** This TA has 3 or more groups working on the same letter: "
                flagged_letters = []
                for idx in flagged_indices:
                    letter = LETTER_SEQUENCE[idx] if 0 <= idx < len(LETTER_SEQUENCE) else f"index {idx}"
                    count = progress_counts[idx]
                    flagged_letters.append(f"'{letter}' ({count} groups)")
                warning_text += ", ".join(flagged_letters)
                st.warning(warning_text)

            # Groups
            for group_name, group_data in ta_data['groups'].items():
                st.markdown(f"### {group_name}")

                # Group info
                col1, col2, col3 = st.columns([2, 2, 2])
                with col1:
                    last_date = group_data.get('last_session_date')
                    if last_date:
                        date_str = datetime.fromisoformat(last_date).strftime('%Y-%m-%d')
                        st.caption(f"Last session: {date_str}")

                with col2:
                    st.caption(f"Progress: {group_data['progress_percentage']:.0f}%")
                    # Show rightmost letter if available
                    if 'rightmost_letter' in group_data and group_data['rightmost_letter']:
                        st.caption(f"Current letter: {group_data['rightmost_letter']}")

                with col3:
                    st.caption(f"Sessions: {group_data['session_count']}")

                # Letter progress grid - pass rightmost_letter if available
                render_letter_grid(
                    letter_sequence, 
                    group_data['progress_index'],
                    group_data.get('rightmost_letter')
                )

                # Additional info for session details
                st.markdown("**Session Details:**")
                activities = group_data['recent_activities']
                col1, col2 = st.columns(2)

                with col1:
                    st.caption("Activities:")
                    if activities['flash_cards_used']:
                        st.write("✅ Flash cards")
                    if activities['board_game_used']:
                        st.write("✅ Board game")
                    if not activities['flash_cards_used'] and not activities['board_game_used']:
                        st.write("📊 Activity data not available")

                with col2:
                    st.caption("Session Info:")
                    if activities['comments']:
                        # Truncate long comments to keep display clean
                        comment = activities['comments']
                        if len(comment) > 50:
                            st.write(f"Notes: {comment[:50]}...")
                        else:
                            st.write(f"Notes: {comment}")

                st.markdown("---")


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
    
    if school_data:
        df = pd.DataFrame(school_data)
        
        # Create separate charts for each grade
        grade_r_df = df[df['Grade'] == 'Grade R']
        grade_1_df = df[df['Grade'] == 'Grade 1']
        
        charts = {}
        
        if not grade_r_df.empty:
            # Sort by Average Progress descending
            grade_r_df = grade_r_df.sort_values('Average Progress', ascending=False)
            charts['R'] = px.bar(
                grade_r_df, 
                x='School', 
                y='Average Progress',
                title='Average Progress by School - Grade R (July Cohort)',
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
                title='Average Progress by School - Grade 1 (July Cohort)',
                color_discrete_sequence=['#28a745']
            )
            charts['1'].update_layout(
                xaxis_title="School",
                yaxis_title="Average Progress (%)",
                yaxis=dict(range=[0, 100])
            )
        
        return charts
    
    return {}


def main():
    st.title("📚 Letter Progress by Teacher Assistant - Recent 2 Weeks")

    # Add info about data source
    st.info("This dashboard shows detailed letter progress data from TeamPact sessions for the most recent 2 weeks.")

    # Region filter at the top
    st.subheader("Select Region")
    region_filter = st.radio(
        "Choose schools to display:",
        options=["All Schools", "East London Schools", "NMB Schools"],
        horizontal=True,
        help="Filter schools by region: East London or NMB (Nelson Mandela Bay)"
    )

    # Fetch data from database
    session_df = fetch_teampact_session_data()

    if session_df is None or session_df.empty:
        st.warning("No data available. Please check your database connection and ensure session data has been synced.")
        return

    # Apply region filter to the dataframe
    if region_filter == "East London Schools":
        # Convert to lowercase for case-insensitive comparison
        el_schools_lower = [school.lower() for school in el_schools]
        session_df = session_df[session_df['school_name'].str.lower().isin(el_schools_lower)]
        if session_df.empty:
            st.warning("No data found for East London schools in the recent 2 weeks.")
            return
        st.info(f"Showing {len(session_df)} sessions from {len(session_df['school_name'].unique())} East London schools")
    elif region_filter == "NMB Schools":
        # Filter out East London schools
        el_schools_lower = [school.lower() for school in el_schools]
        session_df = session_df[~session_df['school_name'].str.lower().isin(el_schools_lower)]
        if session_df.empty:
            st.warning("No data found for NMB schools in the recent 2 weeks.")
            return
        st.info(f"Showing {len(session_df)} sessions from {len(session_df['school_name'].unique())} NMB schools")
    else:
        # All schools
        st.info(f"Showing {len(session_df)} sessions from {len(session_df['school_name'].unique())} schools (all regions)")

    # Process data into the format expected by the visualization functions
    all_data = process_session_data(session_df)

    if not all_data:
        st.warning("No processed data available.")
        return
    
    # Show overall flagged TAs summary at the top
    st.header("🚩 TA Progress Monitoring Summary")
    st.markdown("Overview of Teacher Assistants who have 3 or more groups working on the same letter")
    
    # Analyze all flagged TAs across all schools
    all_flagged_analysis = analyze_flagged_tas(all_data)
    
    # Display summary statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total TAs", all_flagged_analysis['total_tas'])
    with col2:
        st.metric("🚩 Flagged TAs", all_flagged_analysis['flagged_count'])
    with col3:
        st.metric("Flagged %", f"{all_flagged_analysis['flagged_percentage']:.1f}%")
    
    # Show list of all flagged TAs
    if all_flagged_analysis['flagged_tas']:
        with st.expander(f"View All {all_flagged_analysis['flagged_count']} Flagged TAs", expanded=False):
            flagged_data = []
            for ta in all_flagged_analysis['flagged_tas']:
                # Format the flagged indices information
                flagged_info = []
                for index in ta['flagged_indices']:
                    letter = LETTER_SEQUENCE[index] if 0 <= index < len(LETTER_SEQUENCE) else f"idx {index}"
                    count = ta['progress_counts'][index]
                    flagged_info.append(f"'{letter}' ({count} groups)")
                
                flagged_data.append({
                    'TA Name': ta['name'],
                    'School': ta['school'],
                    'Mentor': ta['mentor'],
                    'Total Groups': ta['total_groups'],
                    'Flagged Letters': ', '.join(flagged_info)
                })
            
            df_flagged = pd.DataFrame(flagged_data)
            st.dataframe(df_flagged, width='stretch', hide_index=True)
    else:
        st.success("✅ No TAs are currently flagged - all TAs have varied group progress levels!")
    
    st.divider()

    # School selector
    schools = sorted(list(all_data.keys()))
    if not schools:
        st.info("No school data available")
        return

    selected_school = st.selectbox(
        "Select a school to view detailed progress:",
        schools,
        help="Choose a school to see detailed EA and group progress information"
    )

    if selected_school:
        st.header(f"📊 {selected_school} - Detailed Progress")

        # Display school data
        display_school_data(all_data[selected_school], LETTER_SEQUENCE)

        # Add recent sessions table
        st.header(f"📝 Recent Sessions at {selected_school}")

        recent_sessions = create_recent_sessions_table(session_df, selected_school)

        if recent_sessions is not None and not recent_sessions.empty:
            st.dataframe(recent_sessions, width='stretch', hide_index=True)

            # Show session count
            st.caption(f"Showing {len(recent_sessions)} sessions from the past 2 weeks")
        else:
            st.info(f"No recent sessions found for {selected_school}")

    # Add school-specific flagged TAs summary
    st.divider()
    st.subheader(f"🚩 Flagged TAs at {selected_school}")
    
    # Analyze flagged TAs for the selected school only
    school_flagged_analysis = analyze_flagged_tas({selected_school: all_data[selected_school]})

    if school_flagged_analysis['flagged_tas']:
        st.warning(f"⚠️ {school_flagged_analysis['flagged_count']} out of {school_flagged_analysis['total_tas']} TAs at this school are flagged ({school_flagged_analysis['flagged_percentage']:.1f}%)")
        
        # Show detailed breakdown for each flagged TA
        st.markdown("**Detailed Group Breakdown by Progress Level:**")
        for ta in school_flagged_analysis['flagged_tas']:
            st.markdown(f"**{ta['name']}** (Mentor: {ta['mentor']})")

            # Get full TA data to show group details
            ta_full_data = all_data[selected_school]['ta_progress'][ta['name']]

            # Group by progress_index
            groups_by_progress = {}
            for group_name, group_data in ta_full_data['groups'].items():
                progress_idx = group_data['progress_index']
                if progress_idx not in groups_by_progress:
                    groups_by_progress[progress_idx] = []
                groups_by_progress[progress_idx].append({
                    'name': group_name,
                    'last_session': group_data.get('last_session_date', 'N/A'),
                    'session_count': group_data.get('session_count', 0),
                    'rightmost_letter': group_data.get('rightmost_letter', 'N/A')
                })

            # Display groups organized by progress_index
            for progress_idx, groups in sorted(groups_by_progress.items()):
                count = len(groups)
                flag_indicator = "🚩 FLAGGED" if count >= 3 else ""
                letter = LETTER_SEQUENCE[progress_idx] if 0 <= progress_idx < len(LETTER_SEQUENCE) else f"index {progress_idx}"
                st.write(f"**Letter '{letter}' (Index {progress_idx}):** {count} groups {flag_indicator}")

                if count >= 3:  # Show details for flagged progress levels
                    group_details = []
                    for group in groups:
                        last_session = group['last_session']
                        if last_session and last_session != 'N/A':
                            try:
                                last_session = datetime.fromisoformat(last_session).strftime('%Y-%m-%d')
                            except:
                                pass
                        group_details.append(f"  • {group['name']} (Sessions: {group['session_count']}, Last: {last_session})")
                    st.text('\n'.join(group_details))

            st.markdown("---")
    else:
        st.success(f"✅ No TAs at {selected_school} are currently flagged - all TAs have varied group progress levels!")
    
    # Show data source information
    with st.expander("Data Source Information"):
        st.write(f"**Data fetched from:** TeamPact Sessions Database")
        st.write(f"**Total sessions processed:** {len(session_df)}")
        st.write(f"**Date range:** July 2025 onwards")
        st.write(f"**Letter sequence used:** {', '.join(LETTER_SEQUENCE)}")
        
        # Show sample of raw data
        if not session_df.empty:
            st.write("**Sample session data:**")
            sample_df = session_df[['user_name', 'school_name', 'group_name', 'letters_taught', 'session_started_at']].head(5)
            st.dataframe(sample_df, width='stretch', hide_index=True)


main()