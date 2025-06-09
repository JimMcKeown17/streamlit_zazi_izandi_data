import streamlit as st
from pages_code.letter_knowledge_24 import letter_knowledge_page
from pages_code.word_reading_24 import word_reading_page
from pages_code.sessions_analysis_24 import sessions_analysis_page
from pages_code.new_schools_zz1_24 import new_schools_page

# from pages_code.sessions_analysis_24 import sessions_ana  lysis_page

st.set_page_config(layout="wide", page_title="ZZ Data Portal")

# Header
col1, col2 = st.columns(2)
with col1:
    st.image('assets/Zazi iZandi logo.png', width=250)
with col2:
    st.title('2024 Results Dashboard')

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Letter Knowledge", "Word Reading", "Sessions Analysis", "New Schools"])

with tab1:
    letter_knowledge_page()

with tab2:
    word_reading_page()
    
with tab3:
    sessions_analysis_page()

with tab4:
    new_schools_page()
