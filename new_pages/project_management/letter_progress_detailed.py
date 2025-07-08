import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json
import plotly.express as px
from collections import Counter

# Configuration
DJANGO_API_URL = "http://zazi-izandi.co.za/api/letter-progress/"
# DJANGO_API_URL = "http://localhost:8000/api/letter-progress/"


@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_all_letter_progress():
    """Fetch all letter progress data from Django API"""
    try:
        response = requests.get(DJANGO_API_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch data from API: {e}")
        return None


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
    
    for school_name, school_data in all_data['data_by_school'].items():
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
        # TA Section
        with st.expander(f"**{ta_name}**", expanded=True):
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

                # Show debug info if available (only in development)
                if 'debug_info' in group_data and st.checkbox(f"Show debug info for {group_name}", key=f"debug_{ta_name}_{group_name}"):
                    st.json(group_data['debug_info'])

                # Additional info for AI context (not in expander due to nesting limitation)
                st.markdown("**Session Details:**")
                activities = group_data['recent_activities']
                col1, col2 = st.columns(2)

                with col1:
                    st.caption("Recent Activities:")
                    if activities['flash_cards_used']:
                        st.write("✅ Flash cards")
                    if activities['board_game_used']:
                        st.write("✅ Board game")

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


def prepare_ai_data_complete(all_data):
    """Prepare complete data in a format optimized for AI consumption"""
    ai_data = {
        'generated_at': all_data['metadata']['generated_at'],
        'letter_sequence': all_data['letter_sequence'],
        'total_schools': all_data['metadata']['total_schools'],
        'total_tas': all_data['metadata']['total_tas'],
        'total_groups': all_data['metadata']['total_groups'],
        'schools': []
    }

    for school_name, school_data in all_data['data_by_school'].items():
        school_summary = {
            'name': school_name,
            'total_tas': school_data['summary']['total_tas'],
            'total_groups': school_data['summary']['total_groups'],
            'total_sessions': school_data['summary']['total_sessions'],
            'average_progress': school_data['summary']['average_progress'],
            'tas': []
        }

        for ta_name, ta_data in school_data['ta_progress'].items():
            ta_summary = {
                'name': ta_name,
                'mentor': ta_data.get('mentor'),
                'total_sessions': ta_data['summary']['total_sessions'],
                'average_progress': ta_data['summary']['average_progress'],
                'groups': []
            }

            for group_name, group_data in ta_data['groups'].items():
                ta_summary['groups'].append({
                    'name': group_name,
                    'progress_percentage': group_data['progress_percentage'],
                    'last_session': group_data['last_session_date'],
                    'letters_completed': group_data['progress_index'] + 1,
                    'session_count': group_data['session_count'],
                    'recent_methods': {
                        'flash_cards': group_data['recent_activities']['flash_cards_used'],
                        'board_game': group_data['recent_activities']['board_game_used']
                    }
                })

            school_summary['tas'].append(ta_summary)

        ai_data['schools'].append(school_summary)

    return ai_data


def prepare_grade_summary(all_data):
    """Prepare grade-specific summary data for dashboard"""
    grade_data = {'Grade R': [], 'Grade 1': []}
    school_grade_data = {}
    
    for school_name, school_data in all_data['data_by_school'].items():
        school_grade_data[school_name] = {'Grade R': [], 'Grade 1': []}
        
        for ta_name, ta_data in school_data['ta_progress'].items():
            grade = (ta_data.get('grade') or '').strip()
            if grade in ['Grade R', 'Grade 1']:
                ta_avg_progress = ta_data['summary']['average_progress']
                grade_data[grade].append(ta_avg_progress)
                school_grade_data[school_name][grade].append(ta_avg_progress)
    
    # Calculate averages
    summary = {
        'grade_r_avg': sum(grade_data['Grade R']) / len(grade_data['Grade R']) if grade_data['Grade R'] else 0,
        'grade_1_avg': sum(grade_data['Grade 1']) / len(grade_data['Grade 1']) if grade_data['Grade 1'] else 0,
        'school_averages': {}
    }
    
    # Calculate school averages by grade
    for school, grades in school_grade_data.items():
        summary['school_averages'][school] = {
            'Grade R': sum(grades['Grade R']) / len(grades['Grade R']) if grades['Grade R'] else 0,
            'Grade 1': sum(grades['Grade 1']) / len(grades['Grade 1']) if grades['Grade 1'] else 0
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
                title='Average Progress by School - Grade R',
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
                title='Average Progress by School - Grade 1',
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
    st.title("📚 Letter Progress by Teacher Assistant")

    # Fetch all data once
    all_data = fetch_all_letter_progress()

    if not all_data:
        st.warning("No data available. Please check your Django server connection.")
        return
    
    # Show summary for all schools
    st.header("All Schools Summary")

    # Create tabs for each school
    if all_data['schools']:
        tabs = st.tabs(all_data['schools'])

        for idx, school in enumerate(all_data['schools']):
            with tabs[idx]:
                display_school_data(all_data['data_by_school'][school], all_data['letter_sequence'])
    else:
        st.info("No school data available")
    
    # Add flagged TAs analysis section
    st.header("🚩 TA Progress Monitoring")
    st.markdown("Teacher Assistants flagged for having 3 or more groups with identical progress levels")
    
    # Analyze flagged TAs
    flagged_analysis = analyze_flagged_tas(all_data)
    
    # Display summary statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total TAs", flagged_analysis['total_tas'])
    with col2:
        st.metric("Flagged TAs", flagged_analysis['flagged_count'])
    with col3:
        st.metric("Flagged Percentage", f"{flagged_analysis['flagged_percentage']:.1f}%")
    
    # Display flagged TAs list
    if flagged_analysis['flagged_tas']:
        st.subheader("Flagged Teacher Assistants")
        
        # Create a dataframe for better display
        flagged_data = []
        for ta in flagged_analysis['flagged_tas']:
            # Format the flagged indices information
            flagged_info = []
            for index in ta['flagged_indices']:
                count = ta['progress_counts'][index]
                flagged_info.append(f"Index {index} ({count} groups)")
            
            flagged_data.append({
                'TA Name': ta['name'],
                'School': ta['school'],
                'Mentor': ta['mentor'],
                'Total Groups': ta['total_groups'],
                'Flagged Progress Levels': ', '.join(flagged_info)
            })
        
        df_flagged = pd.DataFrame(flagged_data)
        st.dataframe(df_flagged, use_container_width=True, hide_index=True)
        
        # Show detailed breakdown for each flagged TA
        with st.expander("View Detailed Group Breakdown", expanded=False):
            for ta in flagged_analysis['flagged_tas']:
                st.markdown(f"**{ta['name']}** ({ta['school']} - Mentor: {ta['mentor']})")
                
                # Get full TA data to show group details
                ta_full_data = all_data['data_by_school'][ta['school']]['ta_progress'][ta['name']]
                
                # Group by progress_index
                groups_by_progress = {}
                for group_name, group_data in ta_full_data['groups'].items():
                    progress_idx = group_data['progress_index']
                    if progress_idx not in groups_by_progress:
                        groups_by_progress[progress_idx] = []
                    groups_by_progress[progress_idx].append({
                        'name': group_name,
                        'last_session': group_data.get('last_session_date', 'N/A'),
                        'session_count': group_data.get('session_count', 0)
                    })
                
                # Display groups organized by progress_index
                for progress_idx, groups in sorted(groups_by_progress.items()):
                    count = len(groups)
                    flag_indicator = "🚩" if count >= 3 else ""
                    st.write(f"Progress Index {progress_idx}: {count} groups {flag_indicator}")
                    
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
        st.info("No TAs are currently flagged for having 3 or more groups with identical progress levels.")


main()