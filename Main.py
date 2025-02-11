import streamlit as st
import streamlit_authenticator as stauth
import importlib

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
    cookie_name,signature_key,
    cookie_expiry_days=30
)

# Display the login widget in the sidebar.
name, authentication_status, username = authenticator.login("Login", "sidebar")

# --- Define your page modules (adjust module names as needed) ---
# These are the pages you want everyone to see.
public_pages = {
    "Home": "pages.home",
    "Page 1": "pages.page1",
    "Page 2": "pages.page2",
    "Page 3": "pages.page3",
    "Page 4": "pages.page4",
}

# These pages are only for authenticated users.
restricted_pages = {
    "Extra Page 1": "pages.extra_page1",
    "Extra Page 2": "pages.extra_page2",
    "Extra Page 3": "pages.extra_page3",
}

# --- Decide which pages to show ---
if authentication_status:
    pages = {**public_pages, **restricted_pages}
    # Provide a logout button in the sidebar if logged in.
    authenticator.logout("Logout", "sidebar")
elif authentication_status is False:
    st.sidebar.error("Username/password is incorrect")
    pages = public_pages  # show only the public pages
else:  # authentication_status is None: no login attempt yet.
    pages = public_pages

# --- Build your custom navigation in the sidebar ---
selected_page = st.sidebar.selectbox("Select a page", list(pages.keys()))

# --- Dynamically import and run the selected page ---
# Each page module should have an `app()` function.
page_module = importlib.import_module(pages[selected_page])
page_module.app()
