import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from collections import Counter
import sys
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
from data_loader import load_sessions_2026
from database_utils import get_mentor

LETTER_SEQUENCE = [
    'a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p',
    's', 'h', 'z', 'n', 'd', 'y', 'f', 'w', 'v', 'x',
    'g', 't', 'q', 'r', 'c', 'j'
]

el_schools = [
    "Brownlee Primary School", "Bumbanani Primary School", "Chuma Junior Primary School",
    "Duncan Village Public School", "Ebhotwe Junior Full Service School",
    "Emncotsho Primary School", "Encotsheni Senior Primary School",
    "Equleni Junior Primary School", "Fanti Gaqa Senior Primary School",
    "Inkqubela Junior Primary School", "Isibane Junior Primary School",
    "Isithsaba Junior Primary School", "Jityaza Combined Primary School",
    "Khanyisa Junior Primary School", "Lunga Junior Primary School",
    "Lwandisa Junior Primary School", "Manyano Junior Primary School",
    "Masakhe Primary School", "Mdantsane Junior Primary School",
    "Misukukhanya Senior Primary School", "Mzoxolo Senior Primary School",
    "Nkangeleko Intermediate School", "Nkosinathi Primary School",
    "Nobhotwe Junior Primary School", "Nontombi Matta Junior Primary School",
    "Nontsikelelo Junior Primary School", "Nontuthuzelo Primary School",
    "Nqonqweni Primary School", "Nzuzo Junior Primary School",
    "Qaqamba Junior Primary School", "R H Godlo Junior Primary School",
    "Sakhile Senior Primary School", "Shad Mashologu Junior Primary School",
    "St John'S Road Junior Secondary School", "Thembeka Junior Primary School",
    "Vuthondaba Full Service School", "W.N. Madikizela-Mandela Primary School",
    "Zamani Junior Primary School", "Zanempucuko Senior Secondary School",
    "Zanokukhanya Junior Primary School", "Zuzile Junior Primary School"
]


def detect_grade_from_groups(group_names):
    if not group_names:
        return 'Unknown'
    grade_counts = {}
    for group_name in group_names:
        if not group_name:
            continue
        group_name = str(group_name).strip()
        if (group_name.startswith('1 ') or group_name.startswith('1A') or group_name.startswith('1B') or
                group_name.startswith('1C') or group_name.startswith('1D') or group_name.startswith('1E') or
                group_name.startswith('1F') or 'Grade 1' in group_name):
            grade_counts['Grade 1'] = grade_counts.get('Grade 1', 0) + 1
        elif (group_name.startswith('2 ') or group_name.startswith('2A') or group_name.startswith('2B') or
              group_name.startswith('2C') or group_name.startswith('2D') or 'Grade 2' in group_name):
            grade_counts['Grade 2'] = grade_counts.get('Grade 2', 0) + 1
        elif (group_name.startswith('R ') or group_name.startswith('R A') or group_name.startswith('R B') or
              group_name.startswith('R C') or group_name.startswith('PreR') or 'Grade R' in group_name):
            grade_counts['Grade R'] = grade_counts.get('Grade R', 0) + 1
    return max(grade_counts, key=grade_counts.get) if grade_counts else 'Unknown'


@st.cache_data(ttl=3600)
def fetch_session_data():
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
        available = {k: v for k, v in cols.items() if k in df.columns}
        df = df[list(available.keys())].rename(columns=available)
        df = df[df['letters_taught'].notna() & (df['letters_taught'] != '')]
        df = df.sort_values('session_started_at', ascending=False)
        return df if not df.empty else None
    except Exception as e:
        st.error(f"Failed to load session data: {e}")
        return None


def calculate_letter_progress(letters_taught_str):
    if not letters_taught_str or str(letters_taught_str).strip() == '':
        return -1, 0.0, None
    letters_list = [l.strip().lower() for l in str(letters_taught_str).split(',') if l.strip()]
    max_index, rightmost = -1, None
    for letter in letters_list:
        if letter in LETTER_SEQUENCE:
            idx = LETTER_SEQUENCE.index(letter)
            if idx > max_index:
                max_index, rightmost = idx, letter
    progress_pct = ((max_index + 1) / len(LETTER_SEQUENCE)) * 100 if max_index >= 0 else 0.0
    return max_index, progress_pct, rightmost


def process_session_data(df):
    if df.empty:
        return {}
    df = df.copy()
    df['progress_index'] = -1
    df['progress_percentage'] = 0.0
    df['rightmost_letter'] = None
    for idx, row in df.iterrows():
        pi, pp, rl = calculate_letter_progress(row['letters_taught'])
        df.at[idx, 'progress_index'] = pi
        df.at[idx, 'progress_percentage'] = pp
        df.at[idx, 'rightmost_letter'] = rl

    data_by_school = {}
    for school in df['school_name'].unique():
        school_data = df[df['school_name'] == school].copy()
        data_by_school[school] = {'summary': {'total_tas': 0, 'total_groups': 0, 'total_sessions': 0, 'average_progress': 0.0}, 'ta_progress': {}}

        for ta in school_data['user_name'].unique():
            ta_data = school_data[school_data['user_name'] == ta].copy()
            grade = detect_grade_from_groups(ta_data['group_name'].tolist())
            data_by_school[school]['ta_progress'][ta] = {
                'mentor': get_mentor(school), 'grade': grade,
                'summary': {'total_sessions': 0, 'average_progress': 0.0}, 'groups': {}
            }
            for group in ta_data['group_name'].unique():
                group_data = ta_data[ta_data['group_name'] == group].copy()
                unique = group_data.drop_duplicates(subset=['session_id']).copy()
                latest = unique.loc[unique['session_started_at'].idxmax()]
                data_by_school[school]['ta_progress'][ta]['groups'][group] = {
                    'progress_index': int(latest['progress_index']) if latest['progress_index'] >= 0 else 0,
                    'progress_percentage': float(latest['progress_percentage']),
                    'session_count': len(unique),
                    'last_session_date': latest['session_started_at'].isoformat() if pd.notna(latest['session_started_at']) else None,
                    'rightmost_letter': latest['rightmost_letter'],
                    'recent_activities': {'flash_cards_used': False, 'board_game_used': False, 'comments': latest.get('session_text', '')}
                }

        all_ta_progress, total_sessions, total_groups = [], 0, 0
        for ta_name, ta_info in data_by_school[school]['ta_progress'].items():
            ta_sessions, ta_progress_vals = 0, []
            for g_info in ta_info['groups'].values():
                ta_sessions += g_info['session_count']
                ta_progress_vals.append(g_info['progress_percentage'])
                total_groups += 1
            total_sessions += ta_sessions
            ta_avg = sum(ta_progress_vals) / len(ta_progress_vals) if ta_progress_vals else 0.0
            all_ta_progress.append(ta_avg)
            data_by_school[school]['ta_progress'][ta_name]['summary']['total_sessions'] = ta_sessions
            data_by_school[school]['ta_progress'][ta_name]['summary']['average_progress'] = ta_avg

        data_by_school[school]['summary']['total_tas'] = len(data_by_school[school]['ta_progress'])
        data_by_school[school]['summary']['total_groups'] = total_groups
        data_by_school[school]['summary']['total_sessions'] = total_sessions
        data_by_school[school]['summary']['average_progress'] = sum(all_ta_progress) / len(all_ta_progress) if all_ta_progress else 0.0

    return data_by_school


def check_ta_flag(ta_data):
    counts = Counter(g['progress_index'] for g in ta_data['groups'].values())
    return any(c >= 3 for c in counts.values())


def check_rapid_advancement(session_df, ta_name, school_name, min_sessions=3):
    ta_sessions = session_df[(session_df['user_name'] == ta_name) & (session_df['school_name'] == school_name)].copy()
    unique = ta_sessions.drop_duplicates(subset=['session_id']).copy()
    if unique.empty or len(unique) < min_sessions:
        return False, {}
    flagged_groups = []
    for group_name in unique['group_name'].unique():
        group_sessions = unique[unique['group_name'] == group_name].sort_values('session_started_at')
        if len(group_sessions) < min_sessions:
            continue
        letters_per_session = [
            set(l.strip().lower() for l in str(s['letters_taught']).split(',') if l.strip())
            for _, s in group_sessions.iterrows()
            if pd.notna(s['letters_taught']) and str(s['letters_taught']).strip()
        ]
        if len(letters_per_session) < min_sessions:
            continue
        review_count = sum(1 for i in range(1, len(letters_per_session)) if letters_per_session[i-1] & letters_per_session[i])
        new_count = (len(letters_per_session) - 1) - review_count
        total = review_count + new_count
        if total > 0 and (new_count / total) * 100 > 70 and total >= (min_sessions - 1):
            flagged_groups.append({'group_name': group_name, 'total_sessions': len(group_sessions), 'no_review_percentage': (new_count / total) * 100})
    return (len(flagged_groups) > 0), {'flagged_groups': flagged_groups} if flagged_groups else {}


def render_letter_grid(progress_index, rightmost_letter=None):
    cols = st.columns(26)
    for idx, letter in enumerate(LETTER_SEQUENCE):
        with cols[idx]:
            if idx <= progress_index:
                color = '#ff9800' if rightmost_letter and letter == rightmost_letter else '#ffc107'
                border = '2px solid #ff6b00' if rightmost_letter and letter == rightmost_letter else '1px solid #ddd'
                st.markdown(f"<div style='background-color:{color};border:{border};padding:4px;text-align:center;border-radius:4px;'><b>{letter}</b></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='background-color:#f8f9fa;border:1px solid #ddd;padding:4px;text-align:center;border-radius:4px;'>{letter}</div>", unsafe_allow_html=True)


def display_school_data(school_data, session_df, school_name):
    summary = school_data['summary']
    c1, c2, c3 = st.columns(3)
    c1.metric("School Average Progress", f"{summary['average_progress']:.1f}%")
    c2.metric("Total Sessions", summary['total_sessions'])
    c3.metric("Active TAs", summary['total_tas'])
    st.divider()

    for ta_name, ta_data in school_data['ta_progress'].items():
        is_flagged = check_ta_flag(ta_data)
        is_rapid, rapid_details = (False, {})
        if ta_data.get('grade') == 'Grade R' and session_df is not None:
            is_rapid, rapid_details = check_rapid_advancement(session_df, ta_name, school_name)

        flag_emoji = ("🚩 " if is_flagged else "") + ("⚡ " if is_rapid else "")
        with st.expander(f"{flag_emoji}**{ta_name}**", expanded=True):
            c1, c2, c3, c4 = st.columns(4)
            if ta_data.get('grade'):
                c1.caption(f"Grade: {ta_data['grade']}")
            if ta_data.get('mentor'):
                c2.caption(f"Mentor: {ta_data['mentor']}")
            c3.caption(f"Sessions: {ta_data['summary']['total_sessions']}")
            c4.caption(f"Avg Progress: {ta_data['summary']['average_progress']:.1f}%")

            if is_flagged:
                counts = Counter(g['progress_index'] for g in ta_data['groups'].values())
                flagged = [LETTER_SEQUENCE[i] if 0 <= i < len(LETTER_SEQUENCE) else f"idx {i}" for i, c in counts.items() if c >= 3]
                st.warning(f"⚠️ **Alert:** 3+ groups on the same letter: {', '.join(flagged)}")

            if is_rapid and rapid_details:
                st.error("⚡ **Rapid Advancement:** This Grade R TA may be introducing new letters too quickly without review.")
                for g in rapid_details.get('flagged_groups', []):
                    st.markdown(f"- **{g['group_name']}**: {g['no_review_percentage']:.0f}% of sessions introduced only new letters")

            for group_name, group_data in ta_data['groups'].items():
                st.markdown(f"### {group_name}")
                c1, c2, c3 = st.columns(3)
                if group_data.get('last_session_date'):
                    try:
                        c1.caption(f"Last session: {datetime.fromisoformat(group_data['last_session_date']).strftime('%Y-%m-%d')}")
                    except Exception:
                        pass
                c2.caption(f"Progress: {group_data['progress_percentage']:.0f}%")
                if group_data.get('rightmost_letter'):
                    c2.caption(f"Current letter: {group_data['rightmost_letter']}")
                c3.caption(f"Sessions: {group_data['session_count']}")
                render_letter_grid(group_data['progress_index'], group_data.get('rightmost_letter'))
                comment = (group_data['recent_activities'] or {}).get('comments', '')
                if comment:
                    st.caption(f"Notes: {str(comment)[:100]}{'...' if len(str(comment)) > 100 else ''}")
                st.markdown("---")


def main():
    st.title("📚 Letter Progress Detailed 2026")
    st.info("Detailed letter progress per EA and group. Data updated nightly from TeamPact.")

    region_filter = st.radio("Show schools:", ["All Schools", "East London Schools", "NMB Schools"], horizontal=True)

    session_df = fetch_session_data()
    if session_df is None or session_df.empty:
        st.warning("No 2026 session data available yet.")
        return

    if region_filter == "East London Schools":
        el_lower = [s.lower() for s in el_schools]
        session_df = session_df[session_df['school_name'].str.lower().isin(el_lower)]
    elif region_filter == "NMB Schools":
        el_lower = [s.lower() for s in el_schools]
        session_df = session_df[~session_df['school_name'].str.lower().isin(el_lower)]

    if session_df.empty:
        st.warning("No session data found for the selected region.")
        return

    st.info(f"Showing {len(session_df):,} sessions from {session_df['school_name'].nunique()} schools")

    all_data = process_session_data(session_df)
    if not all_data:
        st.warning("No processed data available.")
        return

    selected_school = st.selectbox("Select a school:", sorted(all_data.keys()))

    if selected_school:
        st.header(f"📊 {selected_school}")
        display_school_data(all_data[selected_school], session_df, selected_school)

        # Recent sessions table
        st.header(f"📝 Recent Sessions — {selected_school}")
        school_sessions = session_df[session_df['school_name'] == selected_school].copy()
        if not school_sessions.empty:
            school_sessions['Date'] = pd.to_datetime(school_sessions['session_started_at']).dt.strftime('%Y-%m-%d %H:%M')
            display_cols = ['Date', 'user_name', 'group_name', 'letters_taught', 'num_letters_taught', 'session_text']
            rename = {'user_name': 'EA', 'group_name': 'Group', 'letters_taught': 'Letters', 'num_letters_taught': 'Count', 'session_text': 'Notes'}
            cols_present = [c for c in display_cols if c in school_sessions.columns]
            st.dataframe(school_sessions[cols_present].rename(columns=rename).sort_values('Date', ascending=False), use_container_width=True, hide_index=True)

        # Flagged TAs summary
        st.divider()
        st.subheader(f"🚩 Flagged TAs at {selected_school}")
        school_analysis = {ta: data for ta, data in all_data[selected_school]['ta_progress'].items() if check_ta_flag(data)}
        if school_analysis:
            st.warning(f"⚠️ {len(school_analysis)} TA(s) flagged at this school")
        else:
            st.success("✅ No TAs flagged at this school")


main()
