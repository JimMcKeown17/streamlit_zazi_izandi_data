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


#2023 Pages
results_page_23 = st.Page("new_pages/2023/6_2023 Results.py", icon="📊", title="2023 Results", url_path="results_23")

# 2024 Pages
letter_knowledge_page_24 = st.Page("new_pages/2024/letter_knowledge_2024.py", icon="📝",title="2024 Letter Knowledge", url_path="letter_knowledge_24")
word_reading_page_24 = st.Page("new_pages/2024/word_reading_2024.py", icon="📖", title="2024 Word Reading", url_path="word_reading_24")
new_schools_page_24 = st.Page("new_pages/2024/new_schools_2024.py", icon="🏫", title="2024 New Schools", url_path="new_schools_24")
session_analysis_page_24 = st.Page("new_pages/2024/session_analysis_2024.py", icon="📈", title="2024 Session Analysis", url_path="session_analysis_24")

#2025 Pages
baseline_page_25 = st.Page("new_pages/2025/baseline_2025.py", icon="📖", title="2025 Baseline", url_path="baseline_25")
midline_page_25 = st.Page("new_pages/2025/midline_2025.py", icon="📊", title="2025 Midline", url_path="midline_25")
sessions_page_25 = st.Page("new_pages/2025/sessions_2025.py", icon="📈", title="2025 Sessions", url_path="sessions_25")
midline_ecd_page_25 = st.Page("new_pages/2025/midline_2025_ecd.py", icon="🏫", title="2025 ECD Midline", url_path="midline_ecd_25")
letter_progress_25 = st.Page("new_pages/2025/letter_progress.py", icon="🔍", title="2025 Letter Progress", url_path="letter_progress_25")

# Research & Other Pages
research_page = st.Page("new_pages/Research & Benchmarks.py", icon="🔍", title="Research & Benchmarks", url_path="research")
year_comparisons_page = st.Page("new_pages/Year_Comparisons.py", icon="🔍", title="Year Comparisons", url_path="year_comparisons")

# --- Navigation ---
pages_2024_public = [letter_knowledge_page_24, word_reading_page_24, new_schools_page_24, session_analysis_page_24]
pages_2024_internal = []

pages_2025_public = [ midline_page_25, baseline_page_25,sessions_page_25, midline_ecd_page_25, ]
pages_2025_internal = [letter_progress_25]

pages_research_public = [research_page]
pages_research_internal = [year_comparisons_page]

pages_2023 = [results_page_23]

pages_2024 = pages_2024_public
if st.session_state.user:
    pages_2024 += pages_2024_internal
    
pages_2025 = pages_2025_public
if st.session_state.user:
    pages_2025 += pages_2025_internal
    
pages_research = pages_research_public
if st.session_state.user:
    pages_research += pages_research_internal
    

pages = {
    "Home": [home_page],
    "2025": pages_2025,
    "2024": pages_2024,
    "2023": pages_2023,
    "Research & Benchmarks": pages_research,
}


pg = st.navigation(pages)

if not st.session_state.user:
     st.warning("Please log in to access internal content.")

pg.run()
