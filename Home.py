import streamlit as st
from display_home import display_home

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
    st.experimental_rerun()

# Display the home page
display_home()
