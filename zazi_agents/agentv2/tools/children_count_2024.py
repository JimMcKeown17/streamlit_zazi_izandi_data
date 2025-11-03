"""
Tool for getting 2024 programme data
"""
import os
import sys
from agents import function_tool

# Set root directory to find data processing files
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from zz_data_processing import process_zz_data_midline, process_zz_data_endline, grade1_df, gradeR_df
from data_loader import load_zazi_izandi_2024


def import_2024_results():
    """Import and process 2024 results data"""
    baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df = load_zazi_izandi_2024()
    
    # Create deep copies to ensure data independence between tabs
    baseline_df = baseline_df.copy()
    midline_df = midline_df.copy()
    sessions_df = sessions_df.copy()
    endline_df = endline_df.copy()

    midline, baseline = process_zz_data_midline(baseline_df, midline_df, sessions_df)
    endline = process_zz_data_endline(endline_df)
    grade1 = grade1_df(endline)
    gradeR = gradeR_df(endline)
    
    return endline


@function_tool
def get_2024_number_of_children():
    """
    Get the number of children on the programme in 2024
    """
    endline_2024 = import_2024_results()
    number_of_children = len(endline_2024)
    return number_of_children

