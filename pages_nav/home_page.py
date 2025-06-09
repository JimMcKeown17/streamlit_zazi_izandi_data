import streamlit as st
from display_home import display_home

def show():
    # Initialize session state for the user (matching the original Home.py logic)
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    display_home() 