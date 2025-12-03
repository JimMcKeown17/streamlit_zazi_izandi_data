import streamlit as st

st.set_page_config(layout="wide", page_title="ZZ Data Portal", page_icon="bar-chart")


# --- Credentials ---
credentials = {
    'zazi': 'izandi'
}

# --- Login/Logout Logic ---
if 'user' not in st.session_state:
    st.session_state.user = None

def login():
    st.sidebar.markdown("---")
    st.sidebar.header("Login")
    username = st.sidebar.text_input("Username", key="username")
    password = st.sidebar.text_input("Password", type="password", key="password")

    if st.sidebar.button("Login"):
        if username in credentials and credentials[username] == password:
            st.session_state.user = username
            st.rerun()
        else:
            st.sidebar.error("Incorrect username or password")
            st.session_state.user = None
    st.sidebar.text("Log in for more detailed views.")

def logout():
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

if st.session_state.user:
    logout()
else:
    login()

# --- Page Definitions ---
home_page = st.Page("new_pages/home_page.py", icon="🏠", title="Home", default=True)
table_of_contents_page = st.Page("new_pages/table_of_contents.py", icon="📑", title="Table of Contents", url_path="table_of_contents")


#2023 Pages
results_page_23 = st.Page("new_pages/2023/6_2023 Results.py", icon="📊", title="2023 Results", url_path="results_23")

# 2024 Pages
letter_knowledge_page_24 = st.Page("new_pages/2024/letter_knowledge_2024.py", icon="📝",title="2024 Letter Knowledge", url_path="letter_knowledge_24")
word_reading_page_24 = st.Page("new_pages/2024/word_reading_2024.py", icon="📖", title="2024 Word Reading", url_path="word_reading_24")
new_schools_page_24 = st.Page("new_pages/2024/new_schools_2024.py", icon="🏫", title="2024 New Schools", url_path="new_schools_24")
session_analysis_page_24 = st.Page("new_pages/2024/session_analysis_2024.py", icon="📈", title="2024 Session Analysis", url_path="session_analysis_24")

#2025 Pages
baseline_page_25 = st.Page("new_pages/2025/baseline_2025.py", icon="📖", title="2025 Baseline NMB (Cohort 1)", url_path="baseline_25")
midline_page_25 = st.Page("new_pages/2025/midline_2025.py", icon="📊", title="2025 Midline NMB (Cohort 1)", url_path="midline_25")
sessions_page_25 = st.Page("new_pages/2025/sessions_2025.py", icon="📈", title="2025 Sessions", url_path="sessions_25")
ecd_page_25 = st.Page("new_pages/2025/ecd_2025.py", icon="🏫", title="2025 ECD NMB Results", url_path="ecd_25")
nmb_assessments_page_25 = st.Page("new_pages/2025/nmb_assessments.py", icon="🏫", title="2025 Baseline NMB (Cohort 2)", url_path="nmb_assessments_25")
nmb_endline_cohort_page_25 = st.Page("new_pages/2025/nmb_endline_cohort_analysis.py", icon="📊", title="2025 Endline NMB (Cohort 2)", url_path="nmb_endline_cohort_25")
nmb_endline_cohort_exclude_page_25 = st.Page("new_pages/2025/nmb_endline_cohort_analysis_exclude.py", icon="📊", title="2025 Endline NMBx (Cohort 2)", url_path="nmb_endline_cohort_exclude_25")
el_assessments_page_25 = st.Page("new_pages/2025/el_assessments.py", icon="🏫", title="2025 Baseline BCM (Cohort 2)", url_path="el_assessments_25")
teampact_sessions_page_25 = st.Page("new_pages/2025/teampact_sessions_2025.py", icon="📱", title="2025 Sessions NMB (Cohort 2)", url_path="teampact_sessions_25")
east_london_sessions_page_25 = st.Page("new_pages/2025/east_london_sessions.py", icon="📱", title="2025 Sessions BCM (Cohort 2)", url_path="east_london_sessions_25")
mentor_visits_page_25 = st.Page("new_pages/2025/mentor_visits_2025.py", icon="👁️", title="2025 Mentor Visits (Cohort 2)", url_path="mentor_visits_25")
# Research & Other Pages
ai_assistant_page = st.Page("new_pages/ai_assistant.py", icon="🤖", title="Zazi Bot", url_path="ai_assistant")
research_page = st.Page("new_pages/Research & Benchmarks.py", icon="🔍", title="Research & Benchmarks", url_path="research")
year_comparisons_page = st.Page("new_pages/Year_Comparisons.py", icon="🔍", title="Year Comparisons", url_path="year_comparisons")
data_sources_page = st.Page("new_pages/data_sources.py", icon="📊", title="Data Sources", url_path="data_sources")
ea_sessions_test_page = st.Page("new_pages/ea_sessions_test.py", icon="🧪", title="EA Sessions Test", url_path="ea_sessions_test")

# Project Management Pages
letter_progress_25 = st.Page("new_pages/project_management/letter_progress.py", icon="🔍", title="Letter Progress (Jan-Jun)", url_path="letter_progress_25")
letter_progress_detailed_25 = st.Page("new_pages/project_management/letter_progress_detailed.py", icon="🔍", title="Letter Progress Detailed (Cohort 1)", url_path="letter_progress_detailed_25")
letter_progress_july_cohort = st.Page("new_pages/project_management/letter_progress_july_cohort.py", icon="📚", title="Letter Progress (Cohort 2)", url_path="letter_progress_july_cohort")
letter_progress_detailed_july_cohort = st.Page("new_pages/project_management/letter_progress_detailed_july_cohort.py", icon="📚", title="Letter Progress Detailed (Cohort 2)", url_path="letter_progress_detailed_july_cohort")
school_reports_page = st.Page("new_pages/project_management/school_reports.py", icon="📊", title="School Reports", url_path="school_reports")
session_quality_review_page = st.Page("new_pages/project_management/session_quality_review.py", icon="📚", title="Session Quality Review", url_path="session_quality_review")
flag_same_letter_groups_page = st.Page("new_pages/project_management/flag_same_letter_groups.py", icon="🚩", title="Check: Same Letter Groups", url_path="flag_same_letter_groups")
flag_moving_too_fast_page = st.Page("new_pages/project_management/flag_moving_too_fast.py", icon="⚡", title="Check: Moving Too Fast", url_path="flag_moving_too_fast")
# --- Navigation ---
pages_2024_public = [letter_knowledge_page_24, word_reading_page_24, new_schools_page_24, session_analysis_page_24]
pages_2024_internal = []

pages_2025_public = [ ecd_page_25, baseline_page_25, midline_page_25 ]
pages_2025_internal = [nmb_assessments_page_25, nmb_endline_cohort_page_25, nmb_endline_cohort_exclude_page_25, teampact_sessions_page_25, east_london_sessions_page_25, el_assessments_page_25]

pages_research_public = [research_page]
pages_research_internal = [ai_assistant_page, year_comparisons_page, data_sources_page]

pages_2023 = [results_page_23]

pages_project_management = []
pages_project_management_internal = [letter_progress_july_cohort, letter_progress_detailed_july_cohort, mentor_visits_page_25, flag_same_letter_groups_page, flag_moving_too_fast_page]

pages_2024 = pages_2024_public
if st.session_state.user:
    pages_2024 += pages_2024_internal
    
pages_2025 = pages_2025_public
if st.session_state.user:
    pages_2025 += pages_2025_internal
    
pages_research = pages_research_public
if st.session_state.user:
    pages_research += pages_research_internal
    
pages_project_management = pages_project_management
if st.session_state.user:
    pages_project_management += pages_project_management_internal


if st.session_state.user:
    pages = {
        "Home": [home_page, table_of_contents_page],
        "Project Management": pages_project_management,
        "2025 Results": pages_2025,
        "2024 Results": pages_2024,
        "2023 Results": pages_2023,
        "Research & Benchmarks": pages_research,
    }
else:
    pages = {
        "Home": [home_page, table_of_contents_page],
        "2025 Results": pages_2025,
        "2024 Results": pages_2024,
        "2023 Results": pages_2023,
        "Research & Benchmarks": pages_research,
    }


pg = st.navigation(pages)

if not st.session_state.user:
     st.warning("Please log in to access internal content.")

pg.run()
