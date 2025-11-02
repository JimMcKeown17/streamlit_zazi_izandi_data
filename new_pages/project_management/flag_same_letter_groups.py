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
from database_utils import get_database_engine, check_table_exists

# Letter sequence that EAs should be teaching
LETTER_SEQUENCE = [
    'a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p',
    's', 'h', 'z', 'n', 'd', 'y', 'f', 'w', 'v', 'x',
    'g', 't', 'q', 'r', 'c', 'j'
]

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_teampact_session_data():
    """Fetch session data from TeamPact database"""
    try:
        if not check_table_exists():
            st.error("TeamPact sessions table not found. Please ensure data has been synced.")
            return None
        
        engine = get_database_engine()
        
        # Query to get session data with letters taught (recent 30 days)
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
        AND session_started_at >= NOW() - INTERVAL '30 days'
        ORDER BY session_started_at DESC
        """
        
        df = pd.read_sql(query, engine)
        
        if df.empty:
            st.warning("No session data found with letter information for recent 30 days.")
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
    """Process session data to get group progress by TA"""
    if df.empty:
        return {}
    
    # Calculate letter progress for each session
    df['progress_index'] = -1
    
    for idx, row in df.iterrows():
        progress_idx, _, _ = calculate_letter_progress(row['letters_taught'], LETTER_SEQUENCE)
        df.at[idx, 'progress_index'] = progress_idx
    
    # Deduplicate by session_id
    df_unique = df.drop_duplicates(subset=['session_id']).copy()
    
    # Group data by school -> TA -> group structure
    data_by_school = {}
    
    for school in df_unique['school_name'].unique():
        school_data = df_unique[df_unique['school_name'] == school].copy()
        data_by_school[school] = {'ta_progress': {}}
        
        for ta in school_data['user_name'].unique():
            ta_data = school_data[school_data['user_name'] == ta].copy()
            data_by_school[school]['ta_progress'][ta] = {'groups': {}}
            
            for group in ta_data['group_name'].unique():
                group_data = ta_data[ta_data['group_name'] == group].copy()
                
                # Get the most recent session for this group
                latest_session = group_data.loc[group_data['session_started_at'].idxmax()]
                progress_index = latest_session['progress_index']
                
                data_by_school[school]['ta_progress'][ta]['groups'][group] = {
                    'progress_index': int(progress_index) if progress_index >= 0 else 0
                }
    
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
                    'total_groups': len(ta_data['groups']),
                    'flagged_indices': flagged_indices,
                    'progress_counts': dict(progress_counts),
                    'groups': ta_data['groups']
                })
    
    flagged_percentage = (len(flagged_tas) / total_tas * 100) if total_tas > 0 else 0
    
    return {
        'flagged_tas': flagged_tas,
        'total_tas': total_tas,
        'flagged_count': len(flagged_tas),
        'flagged_percentage': flagged_percentage
    }


def main():
    st.title("🚩 Groups on Same Letter Flag")
    st.markdown("### TAs with 3 or more groups working on the same letter")
    
    st.info("**What this flag means:** When a TA has 3 or more groups at the exact same letter level, "
            "it MAY indicate they aren't properly differentiating instruction based on group ability levels. "
            "Groups should be progressing at different rates based on their baseline assessments.")
    st.warning("This flag is not always a sign of a problem, so it should be used as a guide, not a definitive indicator. For example, in the beginning of the program, many Grade R children groups may be at the beginning levels and thus are doing the same letters.")
    
    # Fetch data
    session_df = fetch_teampact_session_data()
    
    if session_df is None or session_df.empty:
        st.warning("No data available. Please check your database connection.")
        return
    
    # Process data
    all_data = process_session_data(session_df)
    
    if not all_data:
        st.warning("No processed data available.")
        return
    
    # Analyze flagged TAs
    flagged_analysis = analyze_flagged_tas(all_data)
    
    # Display summary statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total TAs", flagged_analysis['total_tas'])
    with col2:
        st.metric("🚩 Flagged TAs", flagged_analysis['flagged_count'])
    with col3:
        st.metric("Flagged %", f"{flagged_analysis['flagged_percentage']:.1f}%")
    
    st.divider()
    
    # Display flagged TAs
    if flagged_analysis['flagged_tas']:
        st.subheader(f"📋 {flagged_analysis['flagged_count']} Flagged TAs")
        
        # Sort by school name for better organization
        flagged_tas_sorted = sorted(flagged_analysis['flagged_tas'], key=lambda x: (x['school'], x['name']))
        
        for ta in flagged_tas_sorted:
            with st.expander(f"**{ta['school']} - {ta['name']}**", expanded=False):
                st.markdown(f"**Total Groups:** {ta['total_groups']}")
                
                # Show which letters are flagged
                flagged_info = []
                for index in ta['flagged_indices']:
                    letter = LETTER_SEQUENCE[index] if 0 <= index < len(LETTER_SEQUENCE) else f"index {index}"
                    count = ta['progress_counts'][index]
                    flagged_info.append(f"Letter **'{letter}'** ({count} groups)")
                
                st.warning("⚠️ " + ", ".join(flagged_info))
                
                # Show detailed group breakdown by progress level
                st.markdown("**Group Breakdown by Letter:**")
                
                # Organize groups by progress_index
                groups_by_progress = {}
                for group_name, group_data in ta['groups'].items():
                    progress_idx = group_data['progress_index']
                    if progress_idx not in groups_by_progress:
                        groups_by_progress[progress_idx] = []
                    groups_by_progress[progress_idx].append(group_name)
                
                # Display groups organized by progress_index
                for progress_idx in sorted(groups_by_progress.keys()):
                    groups = groups_by_progress[progress_idx]
                    count = len(groups)
                    letter = LETTER_SEQUENCE[progress_idx] if 0 <= progress_idx < len(LETTER_SEQUENCE) else f"index {progress_idx}"
                    flag_indicator = "🚩 FLAGGED" if count >= 3 else ""
                    
                    st.write(f"**Letter '{letter}' (Index {progress_idx}):** {count} groups {flag_indicator}")
                    
                    # Show group names
                    group_list = ", ".join(groups)
                    st.write(f"  → {group_list}")
                
                st.markdown("---")
                st.caption("💡 **Recommendation:** Review baseline assessments and ensure groups are properly differentiated by ability level.")
    else:
        st.success("✅ No TAs are currently flagged - all TAs have varied group progress levels!")
    
    # Show data source info
    with st.expander("ℹ️ Data Source Information"):
        st.write(f"**Data from:** TeamPact Sessions Database (last 30 days)")
        st.write(f"**Total sessions analyzed:** {len(session_df)}")
        st.write(f"**Letter sequence:** {', '.join(LETTER_SEQUENCE)}")


if __name__ == "__main__":
    main()
else:
    main()

