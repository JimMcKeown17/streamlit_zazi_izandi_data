import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json
import plotly.express as px

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
    st.title("📚 Letter Progress Dashboard")

    # Fetch all data once
    all_data = fetch_all_letter_progress()

    if not all_data:
        st.warning("No data available. Please check your Django server connection.")
        return

    # Display overall metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total TAs", all_data['metadata']['total_tas'])
    with col2:
        st.metric("Total Groups", all_data['metadata']['total_groups'])
    with col3:
        st.metric("Total Schools", all_data['metadata']['total_schools'])
    # Prepare grade summary data
    grade_summary = prepare_grade_summary(all_data)
    
    # Grade averages
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "Grade R Average Progress", 
            f"{grade_summary['grade_r_avg']:.1f}%",
            help="Average progress across all Grade R TAs"
        )
    with col2:
        st.metric(
            "Grade 1 Average Progress", 
            f"{grade_summary['grade_1_avg']:.1f}%", 
            help="Average progress across all Grade 1 TAs"
        )
    with col3:
        # Calculate overall average
        all_grades = []
        for school_data in all_data['data_by_school'].values():
            for ta_data in school_data['ta_progress'].values():
                grade = (ta_data.get('grade') or '').strip()
                if grade in ['Grade R', 'Grade 1']:
                    all_grades.append(ta_data['summary']['average_progress'])
        
        overall_avg = sum(all_grades) / len(all_grades) if all_grades else 0
        st.metric(
            "Overall Average Progress",
            f"{overall_avg:.1f}%",
            help="Average progress across all grades"
        )
    
    # Grade progress charts
    charts = create_grade_charts(grade_summary)
    
    if charts:
        st.subheader("Progress by School and Grade")
        
        if 'R' in charts:
            st.plotly_chart(charts['R'], width='stretch')
        
        if '1' in charts:
            st.plotly_chart(charts['1'], width='stretch')
    
    st.divider()
    

main()