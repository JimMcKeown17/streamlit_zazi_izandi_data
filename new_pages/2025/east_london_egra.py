import streamlit as st
import pandas as pd
import sys
import os
import traceback
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# Load environment variables from .env file
load_dotenv(os.path.join(project_root, '.env'))

from api.east_london_egra_api import fetch_east_london_egra_data

def display_east_london_egra():
    """Display East London EGRA data from surveys 644, 646, 647"""
    
    st.title("East London EGRA Assessments")
    st.write("Data from surveys 644 (isiXhosa), 646 (English), 647 (Afrikaans)")
    
    # Check if API token is available
    api_token = os.getenv('TEAMPACT_API_TOKEN')
    if not api_token:
        st.error("❌ TEAMPACT_API_TOKEN not found in environment variables")
        st.write("Please ensure your .env file contains the API token")
        return
    else:
        st.success(f"✅ API Token loaded (length: {len(api_token)} chars)")
    
    # Add loading message
    with st.spinner("Fetching data from TeamPact API..."):
        try:
            # Fetch the data
            xhosa_df, english_df, afrikaans_df = fetch_east_london_egra_data()
            
            if all(df is not None for df in [xhosa_df, english_df, afrikaans_df]):
                
                # Display summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Records", len(xhosa_df) + len(english_df) + len(afrikaans_df))
                with col2:
                    st.metric("isiXhosa", len(xhosa_df))
                with col3:
                    st.metric("English", len(english_df))
                with col4:
                    st.metric("Afrikaans", len(afrikaans_df))
                
                st.divider()
                
                # Helper function to make dataframes Streamlit-compatible
                def prepare_df_for_display(df, name):
                    if df.empty:
                        return df
                    
                    # Create a copy to avoid modifying original
                    display_df = df.copy()
                    
                    # Convert complex columns to strings for display
                    for col in display_df.columns:
                        if display_df[col].dtype == 'object':
                            # Check if column contains complex objects
                            sample = display_df[col].iloc[0] if len(display_df) > 0 else None
                            if isinstance(sample, (list, dict)):
                                display_df[col] = display_df[col].astype(str)
                    
                    return display_df
                
                # Display isiXhosa data
                st.subheader("isiXhosa EGRA Data (Survey 644)")
                st.write(f"Total records: {len(xhosa_df)}")
                if not xhosa_df.empty:
                    display_xhosa = prepare_df_for_display(xhosa_df, "isiXhosa")
                    st.dataframe(display_xhosa, width='stretch')
                else:
                    st.warning("No isiXhosa data available")
                
                st.divider()
                
                # Display English data
                st.subheader("English EGRA Data (Survey 646)")
                st.write(f"Total records: {len(english_df)}")
                if not english_df.empty:
                    display_english = prepare_df_for_display(english_df, "English")
                    st.dataframe(display_english, width='stretch')
                else:
                    st.warning("No English data available")
                
                st.divider()
                
                # Display Afrikaans data
                st.subheader("Afrikaans EGRA Data (Survey 647)")
                st.write(f"Total records: {len(afrikaans_df)}")
                if not afrikaans_df.empty:
                    display_afrikaans = prepare_df_for_display(afrikaans_df, "Afrikaans")
                    st.dataframe(display_afrikaans, width='stretch')
                else:
                    st.warning("No Afrikaans data available")
                
            else:
                st.error("Failed to fetch data from one or more surveys")
                
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")
            st.error("Full error details:")
            st.code(traceback.format_exc())

if __name__ == "__main__":
    display_east_london_egra()
