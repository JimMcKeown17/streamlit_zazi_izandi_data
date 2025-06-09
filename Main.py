import streamlit as st
import streamlit_authenticator as stauth

cookie_name = st.secrets["auth"]["cookie_name"]
signature_key = st.secrets["auth"]["signature_key"]

# --- Page configuration ---
st.set_page_config(layout="wide", page_title="ZZ Data Portal")

# --- Load credentials from secrets ---
# Your .streamlit/secrets.toml should have a [credentials] section as shown above.
credentials = st.secrets["credentials"]
names = credentials["names"]
usernames = credentials["usernames"]
passwords = credentials["passwords"]  # In production, store hashed passwords!

# Generate hashed passwords for demonstration.
# (Run this once to generate hashed passwords, then store and reuse the hashed versions.)
hashed_passwords = stauth.Hasher(passwords).generate()

# --- Initialize the authenticator ---
authenticator = stauth.Authenticate(
    names, usernames, hashed_passwords,
    cookie_name, signature_key,
    cookie_expiry_days=30
)

# Display the login widget in the sidebar.
name, authentication_status, username = authenticator.login("Login", "sidebar")

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

# --- Define page structure ---
if authentication_status:
    # All pages available when authenticated
    pages = {
        "Home": [
            st.Page(home_show, title="Home", icon="🏠")
        ],
        "2025 Results": [
            st.Page(midline_2025_show, title="Midline", icon="📊"),
            st.Page(baseline_2025_show, title="Baseline", icon="📋"),
        ],
        "2024 Results": [
            st.Page(letter_knowledge_show, title="Letter Knowledge", icon="📝"),
            st.Page(word_reading_show, title="Word Reading", icon="📖"),
            st.Page(new_schools_show, title="New Schools Analysis", icon="🏫"),
            st.Page(sessions_show, title="Sessions Analysis", icon="📈"),
        ],
        "2023 Results": [
            st.Page(results_2023_show, title="2023 Analysis", icon="📋"),
        ],
        "Research & Benchmarks": [
            st.Page(research_show, title="Research & Benchmarks", icon="🔬"),
        ]
    }
    # Provide a logout button in the sidebar if logged in.
    authenticator.logout("Logout", "sidebar")
elif authentication_status is False:
    st.sidebar.error("Username/password is incorrect")
    pages = {
        "Home": [
            st.Page(home_show, title="Home", icon="🏠")
        ]
    }
else:  # authentication_status is None: no login attempt yet.
    pages = {
        "Home": [
            st.Page(home_show, title="Home", icon="🏠")
        ]
    }

# --- Create navigation ---
pg = st.navigation(pages)
pg.run()
