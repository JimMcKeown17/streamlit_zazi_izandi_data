"""
Database query tools for the Literacy Coach Mentor system
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter
from typing import Dict, Any

# Add project root to path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from database_utils import get_database_engine
from agents import function_tool
from .prompts import LETTER_SEQUENCE


def calculate_letter_progress(letters_taught_str, letter_sequence=LETTER_SEQUENCE):
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


def detect_grade_from_groups(group_names):
    """Detect grade from group names - returns 'Grade R', 'Grade 1', 'Grade 2', or 'Unknown'"""
    if not group_names:
        return 'Unknown'
    
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


def _extract_user_id_from_context(context_str: str) -> int:
    """Extract user_id from context string like '[Coach User ID: 12345]'"""
    import re
    match = re.search(r'\[Coach User ID:\s*(\d+)\]', context_str)
    if match:
        return int(match.group(1))
    # Try to parse as direct integer
    try:
        return int(context_str)
    except:
        raise ValueError(f"Could not extract user_id from: {context_str}")


@function_tool
def get_coach_sessions(user_id: int) -> str:
    """
    Fetch all session data for a specific literacy coach from the database.
    
    Args:
        user_id: The TeamPact user_id of the literacy coach (can be integer or string with format '[Coach User ID: 123]')
    
    Returns:
        JSON string containing session data including dates, groups, letters taught, and attendance
    """
    try:
        engine = get_database_engine()
        
        query = """
        SELECT
            session_id,
            user_id,
            user_name,
            class_name as group_name,
            program_name as school_name,
            session_started_at,
            letters_taught,
            num_letters_taught,
            attended_percentage,
            participant_total,
            attended_total,
            session_text,
            session_duration_seconds
        FROM teampact_sessions_complete
        WHERE user_id = %s
        AND letters_taught IS NOT NULL
        AND letters_taught <> ''
        ORDER BY session_started_at DESC
        """
        
        df = pd.read_sql(query, engine, params=(user_id,))
        
        if df.empty:
            return f"No session data found for user_id {user_id}. This coach may not have recorded any sessions yet, or the user_id may be incorrect."
        
        # Calculate letter progress for each session
        df['progress_index'] = -1
        df['progress_percentage'] = 0.0
        df['rightmost_letter'] = None
        
        for idx, row in df.iterrows():
            progress_idx, progress_pct, rightmost = calculate_letter_progress(row['letters_taught'])
            df.at[idx, 'progress_index'] = progress_idx
            df.at[idx, 'progress_percentage'] = progress_pct
            df.at[idx, 'rightmost_letter'] = rightmost
        
        # Convert to dict for JSON serialization
        result = {
            'coach_name': df.iloc[0]['user_name'],
            'school_name': df.iloc[0]['school_name'],
            'total_sessions': len(df),
            'date_range': {
                'earliest': df['session_started_at'].min().isoformat() if pd.notna(df['session_started_at'].min()) else None,
                'latest': df['session_started_at'].max().isoformat() if pd.notna(df['session_started_at'].max()) else None
            },
            'sessions': df.to_dict('records')
        }
        
        return str(result)
        
    except Exception as e:
        return f"Error fetching coach sessions: {str(e)}"


@function_tool
def get_coach_groups(user_id: int) -> str:
    """
    Get information about all groups taught by a specific literacy coach, including their letter progress.
    
    Args:
        user_id: The TeamPact user_id of the literacy coach
    
    Returns:
        JSON string containing group information with current letter progress for each group
    """
    try:
        engine = get_database_engine()
        
        query = """
        SELECT
            user_name,
            class_name as group_name,
            program_name as school_name,
            session_started_at,
            letters_taught,
            num_letters_taught,
            attended_percentage,
            participant_total,
            session_text
        FROM teampact_sessions_complete
        WHERE user_id = %s
        AND letters_taught IS NOT NULL
        AND letters_taught <> ''
        ORDER BY session_started_at DESC
        """
        
        df = pd.read_sql(query, engine, params=(user_id,))
        
        if df.empty:
            return f"No group data found for user_id {user_id}."
        
        # Calculate letter progress for each session
        df['progress_index'] = -1
        df['progress_percentage'] = 0.0
        df['rightmost_letter'] = None
        
        for idx, row in df.iterrows():
            progress_idx, progress_pct, rightmost = calculate_letter_progress(row['letters_taught'])
            df.at[idx, 'progress_index'] = progress_idx
            df.at[idx, 'progress_percentage'] = progress_pct
            df.at[idx, 'rightmost_letter'] = rightmost
        
        # Group by class_name and get latest session for each group
        groups_info = {}
        
        for group_name in df['group_name'].unique():
            group_data = df[df['group_name'] == group_name].copy()
            latest_session = group_data.loc[group_data['session_started_at'].idxmax()]
            
            groups_info[group_name] = {
                'group_name': group_name,
                'total_sessions': len(group_data),
                'last_session_date': latest_session['session_started_at'].isoformat() if pd.notna(latest_session['session_started_at']) else None,
                'current_progress_index': int(latest_session['progress_index']) if latest_session['progress_index'] >= 0 else 0,
                'current_progress_percentage': float(latest_session['progress_percentage']),
                'rightmost_letter': latest_session['rightmost_letter'],
                'letters_in_sequence': LETTER_SEQUENCE[:int(latest_session['progress_index']) + 1] if latest_session['progress_index'] >= 0 else [],
                'average_attendance': float(group_data['attended_percentage'].mean()) if not group_data['attended_percentage'].isna().all() else 0.0,
                'participant_total': int(latest_session['participant_total']) if pd.notna(latest_session['participant_total']) else 0
            }
        
        # Detect grade
        grade = detect_grade_from_groups(list(groups_info.keys()))
        
        # Check for differentiation flag (3+ groups at same progress_index)
        progress_indices = [g['current_progress_index'] for g in groups_info.values()]
        progress_counts = Counter(progress_indices)
        has_differentiation_issue = any(count >= 3 for count in progress_counts.values())
        
        result = {
            'coach_name': df.iloc[0]['user_name'],
            'school_name': df.iloc[0]['school_name'],
            'grade': grade,
            'total_groups': len(groups_info),
            'has_differentiation_issue': has_differentiation_issue,
            'groups': list(groups_info.values())
        }
        
        return str(result)
        
    except Exception as e:
        return f"Error fetching coach groups: {str(e)}"


@function_tool
def get_coach_summary_stats(user_id: int) -> str:
    """
    Get overall summary statistics for a literacy coach's performance.
    
    Args:
        user_id: The TeamPact user_id of the literacy coach
    
    Returns:
        JSON string with summary statistics including session frequency, date range, and overall metrics
    """
    try:
        engine = get_database_engine()
        
        query = """
        SELECT
            user_name,
            program_name as school_name,
            class_name as group_name,
            session_started_at,
            letters_taught,
            attended_percentage,
            participant_total,
            session_duration_seconds
        FROM teampact_sessions_complete
        WHERE user_id = %s
        AND letters_taught IS NOT NULL
        AND letters_taught <> ''
        ORDER BY session_started_at DESC
        """
        
        df = pd.read_sql(query, engine, params=(user_id,))
        
        if df.empty:
            return f"No data found for user_id {user_id}."
        
        # Calculate date range
        earliest_date = df['session_started_at'].min()
        latest_date = df['session_started_at'].max()
        
        if pd.notna(earliest_date) and pd.notna(latest_date):
            days_active = (latest_date - earliest_date).days
            weeks_active = days_active / 7 if days_active > 0 else 0
        else:
            days_active = 0
            weeks_active = 0
        
        # Calculate session frequency
        total_sessions = len(df)
        sessions_per_week = total_sessions / weeks_active if weeks_active > 0 else 0
        
        # Group statistics
        unique_groups = df['group_name'].nunique()
        
        # Attendance statistics
        avg_attendance = df['attended_percentage'].mean() if not df['attended_percentage'].isna().all() else 0.0
        
        # Calculate letter progress
        df['progress_index'] = -1
        for idx, row in df.iterrows():
            progress_idx, _, _ = calculate_letter_progress(row['letters_taught'])
            df.at[idx, 'progress_index'] = progress_idx
        
        # Get max progress across all groups
        max_progress_index = df['progress_index'].max()
        max_progress_letter = LETTER_SEQUENCE[int(max_progress_index)] if max_progress_index >= 0 else None
        
        # Detect grade
        grade = detect_grade_from_groups(df['group_name'].tolist())
        
        # Calculate sessions in last 2 weeks
        two_weeks_ago = datetime.now() - timedelta(days=14)
        recent_sessions = df[df['session_started_at'] >= two_weeks_ago]
        sessions_last_2_weeks = len(recent_sessions)
        
        result = {
            'coach_name': df.iloc[0]['user_name'],
            'school_name': df.iloc[0]['school_name'],
            'grade': grade,
            'total_sessions': total_sessions,
            'unique_groups': unique_groups,
            'date_range': {
                'earliest': earliest_date.isoformat() if pd.notna(earliest_date) else None,
                'latest': latest_date.isoformat() if pd.notna(latest_date) else None,
                'days_active': days_active,
                'weeks_active': round(weeks_active, 1)
            },
            'session_frequency': {
                'sessions_per_week': round(sessions_per_week, 1),
                'sessions_last_2_weeks': sessions_last_2_weeks,
                'target_sessions_per_week': 3
            },
            'attendance': {
                'average_percentage': round(avg_attendance, 1),
                'target_percentage': 80
            },
            'letter_progress': {
                'max_progress_index': int(max_progress_index) if max_progress_index >= 0 else 0,
                'max_progress_letter': max_progress_letter,
                'letters_covered': LETTER_SEQUENCE[:int(max_progress_index) + 1] if max_progress_index >= 0 else [],
                'total_letters_in_sequence': len(LETTER_SEQUENCE)
            }
        }
        
        return str(result)
        
    except Exception as e:
        return f"Error fetching coach summary stats: {str(e)}"


@function_tool
def get_benchmark_comparison(user_id: int) -> str:
    """
    Compare a literacy coach's learner performance against national and programme benchmarks.
    
    Args:
        user_id: The TeamPact user_id of the literacy coach
    
    Returns:
        JSON string with benchmark comparisons and performance context
    """
    try:
        engine = get_database_engine()
        
        query = """
        SELECT
            user_name,
            program_name as school_name,
            class_name as group_name,
            session_started_at,
            letters_taught,
            attended_percentage,
            participant_total
        FROM teampact_sessions_complete
        WHERE user_id = %s
        AND letters_taught IS NOT NULL
        AND letters_taught <> ''
        ORDER BY session_started_at DESC
        """
        
        df = pd.read_sql(query, engine, params=(user_id,))
        
        if df.empty:
            return f"No data found for user_id {user_id}."
        
        # Calculate letter progress for each session
        df['progress_index'] = -1
        for idx, row in df.iterrows():
            progress_idx, _, _ = calculate_letter_progress(row['letters_taught'])
            df.at[idx, 'progress_index'] = progress_idx
        
        # Detect grade
        grade = detect_grade_from_groups(df['group_name'].tolist())
        
        # Calculate average attendance
        avg_attendance = df['attended_percentage'].mean() if not df['attended_percentage'].isna().all() else 0.0
        
        # Get max progress across all groups
        max_progress_index = df['progress_index'].max()
        letters_known = int(max_progress_index) + 1 if max_progress_index >= 0 else 0
        
        # Calculate time in programme
        earliest_date = df['session_started_at'].min()
        latest_date = df['session_started_at'].max()
        weeks_in_programme = ((latest_date - earliest_date).days / 7) if pd.notna(earliest_date) and pd.notna(latest_date) else 0
        
        # Expected progress (roughly 2 letters every 3 sessions for Grade 1)
        total_sessions = len(df)
        expected_letters = (total_sessions / 3) * 2 if grade == 'Grade 1' else (total_sessions / 4) * 1
        
        # Benchmarks
        benchmarks = {
            'national_context': {
                'eastern_cape_grade1_40lpm': 0.27,  # 27% reach 40 letters per minute
                'national_grade1_all_letters': 0.50,  # 50% know all letters
                'description': 'Only 27% of Eastern Cape Grade 1 learners reach 40 letters per minute. Nationally, fewer than 50% know all letters by year end.'
            },
            'zazi_izandi_targets': {
                '2023_benchmark_achievement': 0.74,  # 74% reached benchmark
                '2024_benchmark_achievement': 0.53,  # 53% reached benchmark
                'description': 'Zazi iZandi programme has achieved 53-74% of learners reaching reading benchmarks.'
            },
            'attendance_target': {
                'target_percentage': 80,
                'description': 'Target attendance is 80% or higher for consistent progress.'
            },
            'pacing_target': {
                'letters_per_3_sessions': 2,
                'description': 'Expected pace for Grade 1 is approximately 2 new letters every 3 sessions.'
            }
        }
        
        # Performance assessment
        attendance_status = 'excellent' if avg_attendance >= 80 else 'needs_improvement'
        pacing_status = 'on_track' if letters_known >= expected_letters * 0.8 else 'behind' if letters_known < expected_letters * 0.6 else 'slightly_behind'
        
        result = {
            'coach_name': df.iloc[0]['user_name'],
            'school_name': df.iloc[0]['school_name'],
            'grade': grade,
            'performance': {
                'letters_known': letters_known,
                'expected_letters': round(expected_letters, 1),
                'total_letters_in_sequence': len(LETTER_SEQUENCE),
                'percentage_complete': round((letters_known / len(LETTER_SEQUENCE)) * 100, 1),
                'pacing_status': pacing_status
            },
            'attendance': {
                'average_percentage': round(avg_attendance, 1),
                'target_percentage': 80,
                'status': attendance_status
            },
            'time_context': {
                'total_sessions': total_sessions,
                'weeks_in_programme': round(weeks_in_programme, 1)
            },
            'benchmarks': benchmarks,
            'comparison_notes': [
                f"This coach's learners are progressing through {letters_known} letters out of {len(LETTER_SEQUENCE)} in the sequence.",
                f"Average attendance of {round(avg_attendance, 1)}% {'meets' if avg_attendance >= 80 else 'is below'} the 80% target.",
                f"Given {total_sessions} sessions, expected progress is approximately {round(expected_letters, 1)} letters for {grade}.",
                "National context: Only 27% of Eastern Cape Grade 1 learners reach the 40 letters per minute benchmark.",
                "Zazi iZandi programmes typically achieve 53-74% of learners reaching benchmarks."
            ]
        }
        
        return str(result)
        
    except Exception as e:
        return f"Error fetching benchmark comparison: {str(e)}"

