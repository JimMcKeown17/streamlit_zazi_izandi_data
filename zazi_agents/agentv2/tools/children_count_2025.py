"""
Tool for getting 2025 programme data
"""
import os
import sys
import pandas as pd
from agents import function_tool

# Set root directory to find data processing files
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from process_survey_cto_updated import process_egra_data
from data_loader import load_zazi_izandi_2025


def import_2025_results():
    """Import and process 2025 results data"""
    # Load data
    df_full, df_ecd = load_zazi_izandi_2025()
    df_full['submission_date'] = pd.to_datetime(df_full['date'])

    # Create initial and midline datasets for comparison charts
    initial_df = df_full[df_full['submission_date'] < pd.Timestamp('2025-04-15')]
    midline_df = df_full[df_full['submission_date'] >= pd.Timestamp('2025-04-15')]
    
    return midline_df


@function_tool
def get_2025_number_of_children():
    """
    Get the number of children on the programme in 2025
    """
    midline_2025 = import_2025_results()
    number_of_children = len(midline_2025)
    return number_of_children

