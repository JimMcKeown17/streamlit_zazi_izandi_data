import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

# Configuration
# DJANGO_API_URL = "http://zazi-izandi.co.za/api/letter-progress/"
DJANGO_API_URL = "http://localhost:8000/api/letter-progress/"


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


def render_letter_grid(letters_sequence, progress_index):
    """Render the letter progress grid"""
    cols = st.columns(26)  # 26 letters

    for idx, letter in enumerate(letters_sequence):
        with cols[idx]:
            if idx <= progress_index:
                # Completed letter - yellow background
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

                with col3:
                    st.caption(f"Sessions: {group_data['session_count']}")

                # Letter progress grid
                render_letter_grid(letter_sequence, group_data['progress_index'])

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


def main():
    st.title("📚 Letter Progress Dashboard")

    # Fetch all data once
    all_data = fetch_all_letter_progress()

    if not all_data:
        st.warning("No data available. Please check your Django server connection.")
        return

    # School filter
    col1, col2, col3 = st.columns([2, 3, 3])
    with col1:
        schools = ["All Schools"] + all_data.get('schools', [])
        selected_school = st.selectbox(
            "Select School",
            schools,
            index=0
        )

    # Display overall metrics
    with col2:
        if selected_school == "All Schools":
            st.metric("Total TAs", all_data['metadata']['total_tas'])
        else:
            school_data = all_data['data_by_school'].get(selected_school, {})
            st.metric("Total TAs", school_data.get('summary', {}).get('total_tas', 0))

    with col3:
        if selected_school == "All Schools":
            st.metric("Total Groups", all_data['metadata']['total_groups'])
        else:
            school_data = all_data['data_by_school'].get(selected_school, {})
            st.metric("Total Groups", school_data.get('summary', {}).get('total_groups', 0))

    st.divider()

    # Display data based on selection
    if selected_school == "All Schools":
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
    else:
        # Show data for selected school
        school_data = all_data['data_by_school'].get(selected_school)
        if school_data:
            display_school_data(school_data, all_data['letter_sequence'])
        else:
            st.info(f"No data available for {selected_school}")


main()