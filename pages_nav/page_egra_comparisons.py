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
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError as e:
        st.error(f"Import error: {e}")
        return
    
    # Execute the original page file content
    page_path = os.path.join(root_dir, "pages", "9_Year_Comparisons.py")
    with open(page_path, 'r') as f:
        content = f.read()
    
    # Remove the page config line to avoid conflicts
    content = content.replace('st.set_page_config(layout="wide", page_title="Year Comparisons")', '')
    
    # Create execution context with all necessary variables
    exec_globals = {
        'st': st,
        'pd': pd,
        'px': px,
        'plt': plt,
        'np': np,
        'os': os,
        '__name__': '__main__',
        '__file__': page_path
    }
    
    # Execute the content with proper context
    exec(content, exec_globals) 