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
        from zz_data_processing import process_zz_data_midline, process_zz_data_endline, grade1_df, gradeR_df
        from data_loader import load_zazi_izandi_2024
    except ImportError as e:
        st.error(f"Import error: {e}")
        return
    
    # Execute the original page file content
    page_path = os.path.join(root_dir, "pages", "3_2024_Word Reading.py")
    with open(page_path, 'r') as f:
        content = f.read()
    
    # Remove the page config line and data loading lines to avoid conflicts
    content = content.replace('st.set_page_config(layout="wide", page_title="ZZ Data Portal")', '')
    # Remove the data loading lines since we're doing it in the wrapper
    content = content.replace('#Import Dataframes\nbaseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df = load_zazi_izandi_2024()', '')
    content = content.replace('base_dir = os.path.dirname(os.path.abspath(__file__))', '')
    content = content.replace('#Process Dataframes\nmidline, baseline = process_zz_data_midline(baseline_df, midline_df, sessions_df)\nendline = process_zz_data_endline(endline_df)\ngrade1 = grade1_df(endline)\ngradeR = gradeR_df(endline)', '')
    
    # Fix the pie chart category_orders and color issues that cause the narwhals error
    content = content.replace('category_orders={\'Group\': labels},', '')
    content = content.replace('color=\'Group\',', '')
    # Apply these replacements multiple times to catch all instances
    content = content.replace('category_orders={\'Group\': labels},', '')
    content = content.replace('color=\'Group\',', '')
    
    # Load all the dataframes that the original page needs
    try:
        baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df = load_zazi_izandi_2024()
        
        # Check if baseline2_df and endline2_df exist and have the required columns
        if baseline2_df is None or baseline2_df.empty:
            st.error("baseline2_df is empty or None")
            return
        if endline2_df is None or endline2_df.empty:
            st.error("endline2_df is empty or None") 
            return
            
        # Check for required columns
        required_cols = ['B. Word reading', 'A.Non-word reading']
        for col in required_cols:
            if col not in baseline2_df.columns or col not in endline2_df.columns:
                st.error(f"Missing required column '{col}' for Word Reading analysis")
                return
                
        # Process dataframes as the original page does
        midline, baseline = process_zz_data_midline(baseline_df, midline_df, sessions_df)
        endline = process_zz_data_endline(endline_df)
        grade1 = grade1_df(endline)
        gradeR = gradeR_df(endline)
        
    except Exception as e:
        st.error(f"Error loading or processing data: {e}")
        return
    
    # Create execution context with all necessary variables
    exec_globals = {
        'st': st,
        'pd': pd,
        'px': px,
        'process_zz_data_midline': process_zz_data_midline,
        'process_zz_data_endline': process_zz_data_endline,
        'grade1_df': grade1_df,
        'gradeR_df': gradeR_df,
        'load_zazi_izandi_2024': load_zazi_izandi_2024,
        'baseline_df': baseline_df,
        'midline_df': midline_df,
        'sessions_df': sessions_df,
        'baseline2_df': baseline2_df,
        'endline_df': endline_df,
        'endline2_df': endline2_df,
        'midline': midline,
        'baseline': baseline,
        'endline': endline,
        'grade1': grade1,
        'gradeR': gradeR,
        'os': os,
        '__name__': '__main__',
        '__file__': page_path
    }
    
    # Execute the content with proper context
    exec(content, exec_globals) 