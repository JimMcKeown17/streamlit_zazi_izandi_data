import streamlit as st
import pandas as pd
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


def detect_grade_from_groups(group_names):
    if not group_names:
        return 'Unknown'
    grade_counts = {}
    for group_name in group_names:
        if not group_name:
            continue
        g = str(group_name).strip()
        if (g.startswith('1 ') or g.startswith('1A') or g.startswith('1B') or
                g.startswith('1C') or g.startswith('1D') or g.startswith('1E') or
                g.startswith('1F') or 'Grade 1' in g):
            grade_counts['Grade 1'] = grade_counts.get('Grade 1', 0) + 1
        elif (g.startswith('2 ') or g.startswith('2A') or g.startswith('2B') or
              g.startswith('2C') or g.startswith('2D') or 'Grade 2' in g):
            grade_counts['Grade 2'] = grade_counts.get('Grade 2', 0) + 1
        elif (g.startswith('R ') or g.startswith('R A') or g.startswith('R B') or
              g.startswith('R C') or g.startswith('PreR') or 'Grade R' in g):
            grade_counts['Grade R'] = grade_counts.get('Grade R', 0) + 1
    return max(grade_counts, key=grade_counts.get) if grade_counts else 'Unknown'


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


def check_grade_r_rapid_advancement(session_df, ta_name, school_name, min_sessions=3):
    ta_sessions = session_df[
        (session_df['user_name'] == ta_name) &
        (session_df['school_name'] == school_name)
    ].copy()
    ta_sessions_unique = ta_sessions.drop_duplicates(subset=['session_id']).copy()

    if ta_sessions_unique.empty or len(ta_sessions_unique) < min_sessions:
        return False, {}

    flagged_groups = []

    for group_name in ta_sessions_unique['group_name'].unique():
        group_sessions = ta_sessions_unique[ta_sessions_unique['group_name'] == group_name].copy()
        if len(group_sessions) < min_sessions:
            continue

        group_sessions = group_sessions.sort_values('session_started_at')

        letters_per_session = []
        session_dates = []
        for _, session in group_sessions.iterrows():
            if pd.notna(session['letters_taught']) and session['letters_taught'].strip():
                letters = set([l.strip().lower() for l in session['letters_taught'].split(',') if l.strip()])
                letters_per_session.append(letters)
                session_dates.append(session['session_started_at'])

        if len(letters_per_session) < min_sessions:
            continue

        review_count = new_letter_count = 0
        transitions = []

        for i in range(1, len(letters_per_session)):
            previous_letters = letters_per_session[i - 1]
            current_letters = letters_per_session[i]
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
                new_letter_count += 1
                transitions.append({
                    'date': session_dates[i],
                    'previous': ', '.join(sorted(previous_letters)),
                    'current': ', '.join(sorted(current_letters)),
                    'overlap': 'None',
                    'has_review': False
                })

        total_transitions = review_count + new_letter_count
        if total_transitions > 0:
            no_review_pct = (new_letter_count / total_transitions) * 100
            if no_review_pct > 70 and total_transitions >= (min_sessions - 1):
                flagged_groups.append({
                    'group_name': group_name,
                    'total_sessions': len(group_sessions),
                    'sessions_analyzed': total_transitions,
                    'no_review_sessions': new_letter_count,
                    'review_sessions': review_count,
                    'no_review_percentage': no_review_pct,
                    'transitions': transitions
                })

    if flagged_groups:
        return True, {'flagged_groups': flagged_groups}
    return False, {}


def analyze_rapid_advancement_tas(session_df, target_grade='Grade R'):
    flagged_tas = []
    total_tas = 0
    df_unique = session_df.drop_duplicates(subset=['session_id']).copy()

    for school in df_unique['school_name'].unique():
        school_data = df_unique[df_unique['school_name'] == school]
        for ta_name in school_data['user_name'].unique():
            ta_data = school_data[school_data['user_name'] == ta_name]
            grade = detect_grade_from_groups(ta_data['group_name'].tolist())
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


def render_grade_section(rapid_advancement, grade_label):
    col1, col2, col3 = st.columns(3)
    col1.metric(f"Total {grade_label} TAs", rapid_advancement['total_tas'])
    col2.metric("⚡ Flagged TAs", rapid_advancement['flagged_count'])
    col3.metric("Flagged %", f"{rapid_advancement['flagged_percentage']:.1f}%")
    st.divider()

    if rapid_advancement['flagged_tas']:
        st.subheader(f"📋 {rapid_advancement['flagged_count']} Flagged {grade_label} TAs")
        for ta in sorted(rapid_advancement['flagged_tas'], key=lambda x: (x['school'], x['name'])):
            with st.expander(f"**{ta['school']} - {ta['name']}**", expanded=False):
                for group_info in ta['flagged_groups']:
                    st.markdown(f"### Group: {group_info['group_name']}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Sessions", group_info['total_sessions'])
                    c2.metric("No Review Sessions", group_info['no_review_sessions'])
                    c3.metric("No Review %", f"{group_info['no_review_percentage']:.0f}%")
                    st.warning(f"⚠️ {group_info['no_review_percentage']:.0f}% of sessions introduced only new letters with no review")
                    st.markdown("**Session-to-Session Analysis:**")
                    for i, transition in enumerate(group_info['transitions'], 1):
                        date_str = (transition['date'].strftime('%Y-%m-%d')
                                    if isinstance(transition['date'], pd.Timestamp)
                                    else str(transition['date']))
                        if transition['has_review']:
                            st.success(f"**Session {i + 1}** ({date_str}): ✅ Has Review")
                        else:
                            st.error(f"**Session {i + 1}** ({date_str}): ❌ No Review")
                        st.write(f"  • Previous session: {transition['previous']}")
                        st.write(f"  • This session: {transition['current']}")
                        st.write(f"  • Letters reviewed: {transition['overlap']}")
                    st.markdown("---")
                st.caption("💡 **Recommendation:** Emphasize reviewing previous letters in each session. "
                           "Learners may need to see letters 5-10 times before mastery.")
    else:
        st.success(f"✅ No {grade_label} TAs are flagged for rapid advancement!")


def main():
    st.title("⚡ Moving Too Fast Flag — 2026")
    st.markdown("### TAs advancing through letters too quickly without adequate review")

    st.info("**What this flag means:** When a TA has >70% of sessions introducing only new letters "
            "with no review of previously taught letters. "
            "**Methodology:** Analyzes session-to-session transitions. If letters taught in one session "
            "have NO overlap with the previous session, that counts as 'no review'. "
            "Flags TAs when this happens >70% of the time.")

    session_df = fetch_teampact_session_data()

    if session_df is None or session_df.empty:
        st.warning("No data available. Data is updated nightly — check back tomorrow.")
        return

    st.header("📚 Grade R Analysis")
    render_grade_section(analyze_rapid_advancement_tas(session_df, 'Grade R'), 'Grade R')

    st.markdown("---")
    st.header("📚 Grade 1 Analysis")
    render_grade_section(analyze_rapid_advancement_tas(session_df, 'Grade 1'), 'Grade 1')

    st.markdown("---")
    with st.expander("ℹ️ Data Source Information"):
        st.write("**Data from:** 2026 sessions parquet (updated nightly)")
        st.write(f"**Total sessions analyzed:** {len(session_df):,}")
        st.write("**Minimum sessions required:** 3 sessions per group")
        st.write("**Flag threshold:** >70% of sessions with no review")


main()
