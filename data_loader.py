import pandas as pd
import os
import streamlit as st

def load_zazi_izandi_2024():
    if 'user' in st.session_state and st.session_state.user:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        baseline_path = os.path.join(base_dir, "data/Zazi iZandi Children's database (Baseline)7052024.xlsx")
        sheet_name_baseline = "ZZ Childrens Database"
        midline_path = os.path.join(base_dir, "data/Zazi iZandi Midline Assessments database (1).xlsx")
        sheet_name_midline = "Childrens database"
        endline_path = os.path.join(base_dir, "data/20241115 - Zazi iZandi 2024 Endline Assessment  - 1.0.xlsx")
        sheet_name_endline = "Endline Assessment"
        baseline_df = pd.read_excel(baseline_path, sheet_name=sheet_name_baseline)
        midline_df = pd.read_excel(midline_path, sheet_name=sheet_name_midline)
        endline_df = pd.read_excel(endline_path, sheet_name=sheet_name_endline)
        sessions_path = os.path.join(base_dir, "data/Zazi iZandi Children's Session Tracker-08062024.xlsx")
        sheet_name_sessions = "ZZ sessions"
        sessions_df = pd.read_excel(sessions_path, sheet_name=sheet_name_sessions)
        sheet_name_zz2 = "ZZ 2.0 Baseline"
        baseline_zz2_path = os.path.join(base_dir, "data/ZZ 2.0 Baseline Assessment.xlsx")
        baseline2_df = pd.read_excel(baseline_zz2_path, sheet_name=sheet_name_zz2)
        sheet_name_zz2_endline = "ZZ 2.0 Endline"
        endline_zz2_path = os.path.join(base_dir, "data/20241112 - Zazi iZandi 2.0 Endline Assessment.xlsx")
        endline2_df = pd.read_excel(endline_zz2_path, sheet_name=sheet_name_zz2_endline)
        return baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        baseline_path = os.path.join(base_dir, "data/Zazi iZandi Children's database (Baseline)7052024 - anonymized.xlsx")
        sheet_name_baseline = "ZZ Childrens Database"
        midline_path = os.path.join(base_dir, "data/Zazi iZandi Midline Assessments database (1) - anonymized.xlsx")
        sheet_name_midline = "Childrens database"
        endline_path = os.path.join(base_dir, "data/20241115 - Zazi iZandi 2024 Endline Assessment  - 1.0 - anonymized.xlsx")
        sheet_name_endline = "Endline Assessment"
        baseline_df = pd.read_excel(baseline_path, sheet_name=sheet_name_baseline)
        midline_df = pd.read_excel(midline_path, sheet_name=sheet_name_midline)
        endline_df = pd.read_excel(endline_path, sheet_name=sheet_name_endline)
        sessions_path = os.path.join(base_dir, "data/Zazi iZandi Children's Session Tracker-08062024.xlsx")
        sheet_name_sessions = "ZZ sessions"
        sessions_df = pd.read_excel(sessions_path, sheet_name=sheet_name_sessions)
        sheet_name_zz2 = "ZZ 2.0 Baseline"
        baseline_zz2_path = os.path.join(base_dir, "data/ZZ 2.0 Baseline Assessment.xlsx")
        sheet_name_zz2_endline = "ZZ 2.0 Endline"
        baseline2_df = pd.read_excel(baseline_zz2_path, sheet_name=sheet_name_zz2)
        endline_zz2_path = os.path.join(base_dir, "data/20241112 - Zazi iZandi 2.0 Endline Assessment - Anonymized.xlsx")
        endline2_df = pd.read_excel(endline_zz2_path, sheet_name=sheet_name_zz2_endline)
        return baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df

def load_zazi_izandi_2023():
    if 'user' in st.session_state and st.session_state.user:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        endline_path = os.path.join(dir_path, "data/ZZ Children's Database 2023 (Endline) 20231130.xlsx")
        sheet_name_endline = "Database"
        endline_df = pd.read_excel(endline_path, sheet_name=sheet_name_endline)

        sessions_path = os.path.join(dir_path, "data/Zazi iZandi Session Tracker 20231124.xlsx")
        sheet_name_sessions = "Zazi iZandi Sessions"
        sessions_df = pd.read_excel(sessions_path, sheet_name=sheet_name_sessions)
        return endline_df, sessions_df
    else:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        endline_path = os.path.join(dir_path, "data/ZZ Children's Database 2023 (Endline) 20231130 - anonymized.xlsx")
        sheet_name_endline = "Database"
        endline_df = pd.read_excel(endline_path, sheet_name=sheet_name_endline)

        sessions_path = os.path.join(dir_path, "data/Zazi iZandi Session Tracker 20231124.xlsx")
        sheet_name_sessions = "Zazi iZandi Sessions"
        sessions_df = pd.read_excel(sessions_path, sheet_name=sheet_name_sessions)
        return endline_df, sessions_df

