import streamlit as st

# Ensure wide layout
st.set_page_config(layout="wide", page_title="ZZ Data Portal")

# Initialize session state for the user
if 'user' not in st.session_state:
    st.session_state.user = None

# Sidebar Login
st.sidebar.header("Login")
username = st.sidebar.text_input("Username", key="username")
password = st.sidebar.text_input("Password", type="password", key="password")

# Login handling
if st.sidebar.button("Login"):
    if username == "zazi" and password == "izandi":
        st.session_state.user = username
        st.sidebar.success(f"Logged in as {username}")
    else:
        st.sidebar.error("Incorrect username or password")

# Logout handling
if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

# Import the page functions
from pages_nav.home_page import show as home_show
from pages_nav.page_2025_midline import show as midline_2025_show
from pages_nav.page_2025_baseline import show as baseline_2025_show
from pages_nav.page_2024_letter_knowledge import show as letter_knowledge_show
from pages_nav.page_2024_word_reading import show as word_reading_show
from pages_nav.page_2024_new_schools import show as new_schools_show
from pages_nav.page_2024_sessions import show as sessions_show
from pages_nav.page_2023_results import show as results_2023_show
from pages_nav.page_research import show as research_show
from pages_nav.page_egra_comparisons import show as egra_comparisons_show

# Define page structure
if st.session_state.user:
    # All pages available when logged in
    pages = {
        "Home": [
            st.Page(home_show, title="Home", icon="🏠", url_path="home")
        ],
        "2025 Results": [
            st.Page(midline_2025_show, title="Midline", icon="📊", url_path="2025_midline"),
            st.Page(baseline_2025_show, title="Baseline", icon="📋", url_path="2025_baseline"),
        ],
        "2024 Results": [
            st.Page(letter_knowledge_show, title="Letter Knowledge", icon="📝", url_path="2024_letter_knowledge"),
            st.Page(word_reading_show, title="Word Reading", icon="📖", url_path="2024_word_reading"),
            st.Page(new_schools_show, title="New Schools Analysis", icon="🏫", url_path="2024_new_schools"),
            st.Page(sessions_show, title="Sessions Analysis", icon="📈", url_path="2024_sessions"),
        ],
        "2023 Results": [
            st.Page(results_2023_show, title="2023 Analysis", icon="📋", url_path="2023_results"),
        ],
        "Research & Benchmarks": [
            st.Page(research_show, title="Research & Benchmarks", icon="🔬", url_path="research"),
            st.Page(egra_comparisons_show, title="Year Comparisons", icon="📊", url_path="egra_comparisons"),
        ]
    }
else:
    # Only home page available when not logged in
    pages = {
        "Home": [
            st.Page(home_show, title="Home", icon="🏠", url_path="home")
        ]
    }

# Create navigation
pg = st.navigation(pages)
pg.run()
