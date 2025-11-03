"""
Data loader for 2024 programme data - shared across 2024 tools
"""
import os
import sys

# Set root directory to find data processing files
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if root_dir not in sys.path:
    sys.path.append(root_dir)

from zz_data_processing import process_zz_data_midline, process_zz_data_endline, grade1_df, gradeR_df
from data_loader import load_zazi_izandi_2024

# Load and process 2024 data once at module level for efficiency
baseline_df_2024, midline_df_2024, sessions_df_2024, baseline2_df_2024, endline_df_2024, endline2_df_2024 = load_zazi_izandi_2024()

# Create deep copies to ensure data independence
baseline_df_2024 = baseline_df_2024.copy()
midline_df_2024 = midline_df_2024.copy()
sessions_df_2024 = sessions_df_2024.copy()
endline_df_2024 = endline_df_2024.copy()

# Process the data
midline_2024, baseline_2024 = process_zz_data_midline(baseline_df_2024, midline_df_2024, sessions_df_2024)
endline_2024 = process_zz_data_endline(endline_df_2024)

