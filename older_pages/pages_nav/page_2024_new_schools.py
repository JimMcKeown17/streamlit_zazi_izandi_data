import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

def show():
    # Check authentication 
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Add the root directory to path for imports
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    
    # Import necessary modules
    try:
        from zz_data_processing import process_zz_data_endline_new_schools, grade1_df, gradeR_df
        from data_loader import load_zazi_izandi_new_schools_2024
    except ImportError as e:
        st.error(f"Import error: {e}")
        return
    
    # Execute the original page file content
    page_path = os.path.join(root_dir, "pages", "4_2024_New_Schools_1.0.py")
    with open(page_path, 'r') as f:
        content = f.read()
    
    # Remove the page config line to avoid conflicts
    content = content.replace('st.set_page_config(layout="wide", page_title="ZZ Data Portal")', '')
    
    # Create execution context with all necessary variables
    exec_globals = {
        'st': st,
        'pd': pd,
        'px': px,
        'process_zz_data_endline_new_schools': process_zz_data_endline_new_schools,
        'grade1_df': grade1_df,
        'gradeR_df': gradeR_df,
        'load_zazi_izandi_new_schools_2024': load_zazi_izandi_new_schools_2024,
        'os': os,
        '__name__': '__main__',
        '__file__': page_path
    }
    
    # Execute the content with proper context
    exec(content, exec_globals) 