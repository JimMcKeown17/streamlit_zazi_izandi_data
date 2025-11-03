"""
Tool for getting 2023 programme data
"""
import os
import sys
from agents import function_tool

# Set root directory to find data processing files
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from zz_data_process_23 import process_zz_data_23
from data_loader import load_zazi_izandi_2023


def import_2023_results():
    """Import and process 2023 results data"""
    # Import dataframes
    endline_df, sessions_df = load_zazi_izandi_2023()
    endline = process_zz_data_23(endline_df, sessions_df)
    return endline


@function_tool
def get_2023_number_of_children():
    """
    Get the number of children on the programme in 2023
    """
    endline_2023 = import_2023_results()
    number_of_children = len(endline_2023)
    return number_of_children

