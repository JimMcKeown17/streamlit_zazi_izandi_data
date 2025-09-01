import streamlit as st
import pandas as pd
from data_utility_functions.data_loader import load_zazi_izandi_2024, load_zazi_izandi_new_schools_2024, load_zazi_izandi_2023
from zz_data_processing import (
    process_zz_data_midline, 
    process_zz_data_endline, 
    process_zz_data_endline_new_schools,
    grade1_df, 
    gradeR_df
)
from data.mentor_schools import mentors_to_schools

def get_mentor(school_name):
    """
    Assign mentor based on school name.
    
    Args:
        school_name (str): Name of the school/program
        
    Returns:
        str: Name of the assigned mentor or 'Unknown' if not found
    """
    for mentor, schools in mentors_to_schools.items():
        if school_name in schools:
            return mentor
    return 'Unknown'

def add_mentor_column(df, school_column='school'):
    """
    Add mentor column to any dataframe based on school name.
    
    Args:
        df (pd.DataFrame): The dataframe to add mentor column to
        school_column (str): Name of the column containing school names
        
    Returns:
        pd.DataFrame: Dataframe with added mentor column
    """
    df_copy = df.copy()
    df_copy['mentor'] = df_copy[school_column].apply(get_mentor)
    return df_copy

class DataManager:
    """
    Centralized data manager that loads and processes data once per session,
    making it available across all pages with caching.
    """
    
    def __init__(self):
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables for data storage."""
        if 'data_loaded_2024' not in st.session_state:
            st.session_state.data_loaded_2024 = False
            st.session_state.data_loaded_2024_new_schools = False
            st.session_state.data_loaded_2023 = False
    
    def get_2024_data(self):
        """
        Get processed 2024 data. Loads and processes data if not already cached.
        
        Returns:
            dict: Dictionary containing all processed 2024 datasets
        """
        if not st.session_state.data_loaded_2024:
            self._load_and_process_2024_data()
        
        return {
            'baseline_df': st.session_state.baseline_df_2024,
            'midline_df': st.session_state.midline_df_2024,
            'sessions_df': st.session_state.sessions_df_2024,
            'baseline2_df': st.session_state.baseline2_df_2024,
            'endline_df': st.session_state.endline_df_2024,
            'endline2_df': st.session_state.endline2_df_2024,
            'midline_processed': st.session_state.midline_processed_2024,
            'baseline_processed': st.session_state.baseline_processed_2024,
            'endline_processed': st.session_state.endline_processed_2024,
            'grade1_df': st.session_state.grade1_df_2024,
            'gradeR_df': st.session_state.gradeR_df_2024
        }
    
    def get_2024_new_schools_data(self):
        """
        Get processed 2024 new schools data. Loads and processes data if not already cached.
        
        Returns:
            dict: Dictionary containing processed new schools dataset
        """
        if not st.session_state.data_loaded_2024_new_schools:
            self._load_and_process_2024_new_schools_data()
        
        return {
            'endline_df': st.session_state.endline_df_new_schools,
            'endline_processed': st.session_state.endline_processed_new_schools
        }
    
    def get_2023_data(self):
        """
        Get processed 2023 data. Loads and processes data if not already cached.
        
        Returns:
            dict: Dictionary containing all processed 2023 datasets
        """
        if not st.session_state.data_loaded_2023:
            self._load_and_process_2023_data()
        
        return {
            'endline_df': st.session_state.endline_df_2023,
            'sessions_df': st.session_state.sessions_df_2023
        }
    
    def _load_and_process_2024_data(self):
        """Load and process 2024 data, storing in session state."""
        with st.spinner('Loading 2024 data... (This may take a moment)'):
            # Load raw data (cached by @st.cache_data)
            baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df = load_zazi_izandi_2024()
            
            # Store raw data in session state
            st.session_state.baseline_df_2024 = baseline_df.copy()
            st.session_state.midline_df_2024 = midline_df.copy()
            st.session_state.sessions_df_2024 = sessions_df.copy()
            st.session_state.baseline2_df_2024 = baseline2_df.copy()
            st.session_state.endline_df_2024 = endline_df.copy()
            st.session_state.endline2_df_2024 = endline2_df.copy()
            
            # Process data
            midline_processed, baseline_processed = process_zz_data_midline(
                baseline_df.copy(), midline_df.copy(), sessions_df.copy()
            )
            endline_processed = process_zz_data_endline(endline_df.copy())
            
            # Store processed data in session state
            st.session_state.midline_processed_2024 = midline_processed
            st.session_state.baseline_processed_2024 = baseline_processed
            st.session_state.endline_processed_2024 = endline_processed
            st.session_state.grade1_df_2024 = grade1_df(endline_processed)
            st.session_state.gradeR_df_2024 = gradeR_df(endline_processed)
            
            # Mark as loaded
            st.session_state.data_loaded_2024 = True
    
    def _load_and_process_2024_new_schools_data(self):
        """Load and process 2024 new schools data, storing in session state."""
        with st.spinner('Loading 2024 new schools data...'):
            # Load raw data (cached by @st.cache_data)
            endline_df = load_zazi_izandi_new_schools_2024()
            
            # Store raw data in session state
            st.session_state.endline_df_new_schools = endline_df.copy()
            
            # Process data
            endline_processed = process_zz_data_endline_new_schools(endline_df.copy())
            
            # Store processed data in session state
            st.session_state.endline_processed_new_schools = endline_processed
            
            # Mark as loaded
            st.session_state.data_loaded_2024_new_schools = True
    
    def _load_and_process_2023_data(self):
        """Load and process 2023 data, storing in session state."""
        with st.spinner('Loading 2023 data...'):
            # Load raw data (cached by @st.cache_data)
            endline_df, sessions_df = load_zazi_izandi_2023()
            
            # Store data in session state
            st.session_state.endline_df_2023 = endline_df.copy()
            st.session_state.sessions_df_2023 = sessions_df.copy()
            
            # Mark as loaded
            st.session_state.data_loaded_2023 = True
    
    def clear_cache(self):
        """Clear all cached data from session state."""
        keys_to_clear = [key for key in st.session_state.keys() if key.startswith('data_loaded_') or key.endswith('_2024') or key.endswith('_2023') or key.endswith('_new_schools')]
        for key in keys_to_clear:
            del st.session_state[key]
        
        # Clear Streamlit's cache as well
        st.cache_data.clear()
        
        st.success("Data cache cleared successfully!")

# Global instance
data_manager = DataManager() 