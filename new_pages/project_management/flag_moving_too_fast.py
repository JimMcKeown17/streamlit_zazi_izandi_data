import streamlit as st
import pandas as pd
from datetime import datetime
from collections import Counter
import sys
import os

# Ensure the project root is on the import path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
from data_loader import load_sessions_2025

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
        df = df[df['letters_taught'].notna() & (df['letters_taught'] != '')]
        df = df.sort_values('session_started_at', ascending=False)

        if df.empty:
            st.warning("No session data found with letter information.")
            return None

        return df

    except Exception as e:
        st.error(f"Failed to load session data: {e}")
        return None


def check_grade_r_rapid_advancement(session_df, ta_name, school_name, min_sessions=3):
    """
    Check if a Grade R TA is advancing too rapidly without reviewing letters.
    Returns (is_flagged, details_dict)
    
    Note: Deduplicates by session_id since each session has multiple participant records.
    """
    # Filter sessions for this TA at this school
    ta_sessions = session_df[
        (session_df['user_name'] == ta_name) & 
        (session_df['school_name'] == school_name)
    ].copy()
    
    # CRITICAL: Deduplicate by session_id to get unique sessions
    ta_sessions_unique = ta_sessions.drop_duplicates(subset=['session_id']).copy()
    
    if ta_sessions_unique.empty or len(ta_sessions_unique) < min_sessions:
        return False, {}
    
    # Group by class/group name
    flagged_groups = []
    
    for group_name in ta_sessions_unique['group_name'].unique():
        group_sessions = ta_sessions_unique[ta_sessions_unique['group_name'] == group_name].copy()
        
        # Need at least min_sessions to analyze
        if len(group_sessions) < min_sessions:
            continue
        
        # Sort by date
        group_sessions = group_sessions.sort_values('session_started_at')
        
        # Get list of letters taught in each unique session
        letters_per_session = []
        session_dates = []
        for _, session in group_sessions.iterrows():
            if pd.notna(session['letters_taught']) and session['letters_taught'].strip():
                letters = set([l.strip().lower() for l in session['letters_taught'].split(',') if l.strip()])
                letters_per_session.append(letters)
                session_dates.append(session['session_started_at'])
        
        if len(letters_per_session) < min_sessions:
            continue
        
        # Check for rapid advancement pattern
        review_count = 0
        new_letter_count = 0
        transitions = []
        
        for i in range(1, len(letters_per_session)):
            previous_letters = letters_per_session[i-1]
            current_letters = letters_per_session[i]
            
            # Check if any letters overlap (review)
            overlap = previous_letters & current_letters
            
            if overlap:
                review_count += 1
                transitions.append({
                    'date': session_dates[i],
                    'previous': ', '.join(sorted(previous_letters)),
                    'current': ', '.join(sorted(current_letters)),
                    'overlap': ', '.join(sorted(overlap)),
                    'has_review': True
                })
            else:
                # No overlap - all new letters
                new_letter_count += 1
                transitions.append({
                    'date': session_dates[i],
                    'previous': ', '.join(sorted(previous_letters)),
                    'current': ', '.join(sorted(current_letters)),
                    'overlap': 'None',
                    'has_review': False
                })
        
        # Flag if there's almost never any review (e.g., >70% of sessions introduce only new letters)
        total_transitions = review_count + new_letter_count
        if total_transitions > 0:
            no_review_percentage = (new_letter_count / total_transitions) * 100
            
            # Flag if >70% of sessions have no review of previous letters
            if no_review_percentage > 70 and total_transitions >= (min_sessions - 1):
                flagged_groups.append({
                    'group_name': group_name,
                    'total_sessions': len(group_sessions),
                    'sessions_analyzed': total_transitions,
                    'no_review_sessions': new_letter_count,
                    'review_sessions': review_count,
                    'no_review_percentage': no_review_percentage,
                    'transitions': transitions
                })
    
    if flagged_groups:
        return True, {'flagged_groups': flagged_groups}
    return False, {}


def analyze_rapid_advancement_tas(session_df, target_grade='Grade R'):
    """Analyze TAs for rapid advancement without review for a specific grade"""
    flagged_tas = []
    total_tas = 0
    
    # Get unique TAs
    df_unique = session_df.drop_duplicates(subset=['session_id']).copy()
    
    # Group by school and TA
    for school in df_unique['school_name'].unique():
        school_data = df_unique[df_unique['school_name'] == school]
        
        for ta_name in school_data['user_name'].unique():
            ta_data = school_data[school_data['user_name'] == ta_name]
            
            # Detect grade
            grade = detect_grade_from_groups(ta_data['group_name'].tolist())
            
            # Only check TAs of the target grade
            if grade == target_grade:
                total_tas += 1
                is_flagged, details = check_grade_r_rapid_advancement(session_df, ta_name, school)
                
                if is_flagged:
                    flagged_tas.append({
                        'name': ta_name,
                        'school': school,
                        'flagged_groups': details.get('flagged_groups', [])
                    })
    
    flagged_percentage = (len(flagged_tas) / total_tas * 100) if total_tas > 0 else 0
    
    return {
        'flagged_tas': flagged_tas,
        'total_tas': total_tas,
        'flagged_count': len(flagged_tas),
        'flagged_percentage': flagged_percentage
    }


def main():
    st.title("⚡ Moving Too Fast Flag")
    st.markdown("### TAs advancing through letters too quickly without adequate review")
    
    st.info("**What this flag means:** When a TA has >70% of their sessions introduce only new letters "
            "with no review of previously taught letters, it indicates the TA may be moving through the letters too quickly. "
            "**Methodology:** Analyzes session-to-session transitions. If letters taught in one session have NO overlap "
            "with the previous session's letters, that's counted as 'no review'. Flags TAs when this happens >70% of the time.\n\n"
            "**Recommendation:** Emphasize the importance of reviewing previous letters in each session. "
            "Learners may need to see letters 5-10 times before mastery, especially early in the program. There should almost always be multiple sessions early on where the TA is running sessions while practicing the same letters multiple times in a row.")
    
    # Fetch data
    session_df = fetch_teampact_session_data()
    
    if session_df is None or session_df.empty:
        st.warning("No data available. Please check your database connection.")
        return
    
    # ============================================
    # GRADE R SECTION
    # ============================================
    st.header("📚 Grade R Analysis")
    
    # Analyze rapid advancement for Grade R
    rapid_advancement_r = analyze_rapid_advancement_tas(session_df, target_grade='Grade R')
    
    # Display summary statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Grade R TAs", rapid_advancement_r['total_tas'])
    with col2:
        st.metric("⚡ Flagged TAs", rapid_advancement_r['flagged_count'])
    with col3:
        st.metric("Flagged %", f"{rapid_advancement_r['flagged_percentage']:.1f}%")
    
    st.divider()
    
    # Display flagged TAs
    if rapid_advancement_r['flagged_tas']:
        st.subheader(f"📋 {rapid_advancement_r['flagged_count']} Flagged Grade R TAs")
        
        # Sort by school name for better organization
        flagged_tas_sorted = sorted(rapid_advancement_r['flagged_tas'], key=lambda x: (x['school'], x['name']))
        
        for ta in flagged_tas_sorted:
            with st.expander(f"**{ta['school']} - {ta['name']}**", expanded=False):
                for group_info in ta['flagged_groups']:
                    st.markdown(f"### Group: {group_info['group_name']}")
                    
                    # Summary metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Sessions", group_info['total_sessions'])
                    with col2:
                        st.metric("No Review Sessions", group_info['no_review_sessions'])
                    with col3:
                        st.metric("No Review %", f"{group_info['no_review_percentage']:.0f}%")
                    
                    st.warning(f"⚠️ {group_info['no_review_percentage']:.0f}% of sessions introduced only new letters with no review")
                    
                    # Show session-to-session transitions
                    st.markdown("**Session-to-Session Analysis:**")
                    
                    for i, transition in enumerate(group_info['transitions'], 1):
                        date_str = transition['date'].strftime('%Y-%m-%d') if isinstance(transition['date'], pd.Timestamp) else str(transition['date'])
                        
                        if transition['has_review']:
                            st.success(f"**Session {i+1}** ({date_str}): ✅ Has Review")
                        else:
                            st.error(f"**Session {i+1}** ({date_str}): ❌ No Review")
                        
                        st.write(f"  • Previous session: {transition['previous']}")
                        st.write(f"  • This session: {transition['current']}")
                        st.write(f"  • Letters reviewed: {transition['overlap']}")
                    
                    st.markdown("---")
                
                st.caption("💡 **Recommendation:** Emphasize the importance of reviewing previous letters in each session. "
                          "Grade R learners may need to see letters 5-10 times before mastery, especially early in the program.")
    else:
        st.success("✅ No Grade R TAs are flagged for rapid advancement - all are providing adequate review!")
    
    # ============================================
    # GRADE 1 SECTION
    # ============================================
    st.markdown("---")
    st.header("📚 Grade 1 Analysis")
    
    # Analyze rapid advancement for Grade 1
    rapid_advancement_1 = analyze_rapid_advancement_tas(session_df, target_grade='Grade 1')
    
    # Display summary statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Grade 1 TAs", rapid_advancement_1['total_tas'])
    with col2:
        st.metric("⚡ Flagged TAs", rapid_advancement_1['flagged_count'])
    with col3:
        st.metric("Flagged %", f"{rapid_advancement_1['flagged_percentage']:.1f}%")
    
    st.divider()
    
    # Display flagged TAs
    if rapid_advancement_1['flagged_tas']:
        st.subheader(f"📋 {rapid_advancement_1['flagged_count']} Flagged Grade 1 TAs")
        
        # Sort by school name for better organization
        flagged_tas_sorted = sorted(rapid_advancement_1['flagged_tas'], key=lambda x: (x['school'], x['name']))
        
        for ta in flagged_tas_sorted:
            with st.expander(f"**{ta['school']} - {ta['name']}**", expanded=False):
                for group_info in ta['flagged_groups']:
                    st.markdown(f"### Group: {group_info['group_name']}")
                    
                    # Summary metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Sessions", group_info['total_sessions'])
                    with col2:
                        st.metric("No Review Sessions", group_info['no_review_sessions'])
                    with col3:
                        st.metric("No Review %", f"{group_info['no_review_percentage']:.0f}%")
                    
                    st.warning(f"⚠️ {group_info['no_review_percentage']:.0f}% of sessions introduced only new letters with no review")
                    
                    # Show session-to-session transitions
                    st.markdown("**Session-to-Session Analysis:**")
                    
                    for i, transition in enumerate(group_info['transitions'], 1):
                        date_str = transition['date'].strftime('%Y-%m-%d') if isinstance(transition['date'], pd.Timestamp) else str(transition['date'])
                        
                        if transition['has_review']:
                            st.success(f"**Session {i+1}** ({date_str}): ✅ Has Review")
                        else:
                            st.error(f"**Session {i+1}** ({date_str}): ❌ No Review")
                        
                        st.write(f"  • Previous session: {transition['previous']}")
                        st.write(f"  • This session: {transition['current']}")
                        st.write(f"  • Letters reviewed: {transition['overlap']}")
                    
                    st.markdown("---")
                
                st.caption("💡 **Recommendation:** Emphasize the importance of reviewing previous letters in each session. "
                          "Grade 1 learners may need to see letters 5-10 times before mastery, especially early in the program.")
    else:
        st.success("✅ No Grade 1 TAs are flagged for rapid advancement - all are providing adequate review!")
    
    # Show data source info
    st.markdown("---")
    with st.expander("ℹ️ Data Source Information"):
        st.write(f"**Data from:** TeamPact Sessions Database (last 30 days)")
        st.write(f"**Total sessions analyzed:** {len(session_df)}")
        st.write(f"**Grade R TAs analyzed:** {rapid_advancement_r['total_tas']}")
        st.write(f"**Grade 1 TAs analyzed:** {rapid_advancement_1['total_tas']}")
        st.write(f"**Minimum sessions required:** 3 sessions per group")
        st.write(f"**Flag threshold:** >70% of sessions with no review")


if __name__ == "__main__":
    main()
else:
    main()

