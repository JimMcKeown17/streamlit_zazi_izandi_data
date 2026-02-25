import streamlit as st
import pandas as pd
from collections import Counter
import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
from data_loader import load_sessions_2026

LETTER_SEQUENCE = [
    'a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p',
    's', 'h', 'z', 'n', 'd', 'y', 'f', 'w', 'v', 'x',
    'g', 't', 'q', 'r', 'c', 'j'
]

@st.cache_data(ttl=3600)
def fetch_teampact_session_data():
    """Load 2026 session data from parquet file."""
    try:
        df = load_sessions_2026()

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


def calculate_letter_progress(letters_taught_str, letter_sequence):
    if not letters_taught_str or letters_taught_str.strip() == '':
        return -1, 0.0, None

    letters_list = [letter.strip().lower() for letter in letters_taught_str.split(',') if letter.strip()]

    if not letters_list:
        return -1, 0.0, None

    max_index = -1
    rightmost_letter = None

    for letter in letters_list:
        if letter in letter_sequence:
            index = letter_sequence.index(letter)
            if index > max_index:
                max_index = index
                rightmost_letter = letter

    progress_percentage = ((max_index + 1) / len(letter_sequence)) * 100 if max_index >= 0 else 0.0

    return max_index, progress_percentage, rightmost_letter


def process_session_data(df):
    if df.empty:
        return {}

    df['progress_index'] = -1

    for idx, row in df.iterrows():
        progress_idx, _, _ = calculate_letter_progress(row['letters_taught'], LETTER_SEQUENCE)
        df.at[idx, 'progress_index'] = progress_idx

    df_unique = df.drop_duplicates(subset=['session_id']).copy()

    data_by_school = {}

    for school in df_unique['school_name'].unique():
        school_data = df_unique[df_unique['school_name'] == school].copy()
        data_by_school[school] = {'ta_progress': {}}

        for ta in school_data['user_name'].unique():
            ta_data = school_data[school_data['user_name'] == ta].copy()
            data_by_school[school]['ta_progress'][ta] = {'groups': {}}

            for group in ta_data['group_name'].unique():
                group_data = ta_data[ta_data['group_name'] == group].copy()
                latest_session = group_data.loc[group_data['session_started_at'].idxmax()]
                progress_index = latest_session['progress_index']
                data_by_school[school]['ta_progress'][ta]['groups'][group] = {
                    'progress_index': int(progress_index) if progress_index >= 0 else 0
                }

    return data_by_school


def check_ta_flag(ta_data):
    progress_indices = [g['progress_index'] for g in ta_data['groups'].values()]
    progress_counts = Counter(progress_indices)
    return any(count >= 3 for count in progress_counts.values())


def analyze_flagged_tas(all_data):
    flagged_tas = []
    total_tas = 0

    for school_name, school_data in all_data.items():
        for ta_name, ta_data in school_data['ta_progress'].items():
            total_tas += 1
            if check_ta_flag(ta_data):
                progress_indices = [g['progress_index'] for g in ta_data['groups'].values()]
                progress_counts = Counter(progress_indices)
                flagged_indices = [idx for idx, cnt in progress_counts.items() if cnt >= 3]
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
    st.title("🚩 Groups on Same Letter Flag — 2026")
    st.markdown("### TAs with 3 or more groups working on the same letter")

    st.info("**What this flag means:** When a TA has 3 or more groups at the exact same letter level, "
            "it MAY indicate they aren't properly differentiating instruction based on group ability levels. "
            "Groups should be progressing at different rates based on their baseline assessments.")
    st.warning("This flag is not always a sign of a problem — early in the program, many Grade R groups "
               "may legitimately be at the beginning levels.")

    session_df = fetch_teampact_session_data()

    if session_df is None or session_df.empty:
        st.warning("No data available. Data is updated nightly — check back tomorrow.")
        return

    all_data = process_session_data(session_df)

    if not all_data:
        st.warning("No processed data available.")
        return

    flagged_analysis = analyze_flagged_tas(all_data)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total TAs", flagged_analysis['total_tas'])
    with col2:
        st.metric("🚩 Flagged TAs", flagged_analysis['flagged_count'])
    with col3:
        st.metric("Flagged %", f"{flagged_analysis['flagged_percentage']:.1f}%")

    st.divider()

    if flagged_analysis['flagged_tas']:
        st.subheader(f"📋 {flagged_analysis['flagged_count']} Flagged TAs")

        for ta in sorted(flagged_analysis['flagged_tas'], key=lambda x: (x['school'], x['name'])):
            with st.expander(f"**{ta['school']} - {ta['name']}**", expanded=False):
                st.markdown(f"**Total Groups:** {ta['total_groups']}")

                flagged_info = []
                for index in ta['flagged_indices']:
                    letter = LETTER_SEQUENCE[index] if 0 <= index < len(LETTER_SEQUENCE) else f"index {index}"
                    count = ta['progress_counts'][index]
                    flagged_info.append(f"Letter **'{letter}'** ({count} groups)")
                st.warning("⚠️ " + ", ".join(flagged_info))

                st.markdown("**Group Breakdown by Letter:**")
                groups_by_progress = {}
                for group_name, group_data in ta['groups'].items():
                    progress_idx = group_data['progress_index']
                    groups_by_progress.setdefault(progress_idx, []).append(group_name)

                for progress_idx in sorted(groups_by_progress.keys()):
                    groups = groups_by_progress[progress_idx]
                    letter = LETTER_SEQUENCE[progress_idx] if 0 <= progress_idx < len(LETTER_SEQUENCE) else f"index {progress_idx}"
                    flag_indicator = "🚩 FLAGGED" if len(groups) >= 3 else ""
                    st.write(f"**Letter '{letter}' (Index {progress_idx}):** {len(groups)} groups {flag_indicator}")
                    st.write(f"  → {', '.join(groups)}")

                st.markdown("---")
                st.caption("💡 **Recommendation:** Review baseline assessments and ensure groups are properly differentiated by ability level.")
    else:
        st.success("✅ No TAs are currently flagged — all TAs have varied group progress levels!")

    with st.expander("ℹ️ Data Source Information"):
        st.write("**Data from:** 2026 sessions parquet (updated nightly)")
        st.write(f"**Total sessions analyzed:** {len(session_df):,}")
        st.write(f"**Letter sequence:** {', '.join(LETTER_SEQUENCE)}")


main()
