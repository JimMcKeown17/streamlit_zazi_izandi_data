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
        baseline_df = pd.read_excel(baseline_path, sheet_name=sheet_name_baseline)
        midline_df = pd.read_excel(midline_path, sheet_name=sheet_name_midline)
        sessions_path = os.path.join(base_dir, "data/Zazi iZandi Children's Session Tracker-08062024.xlsx")
        sheet_name_sessions = "ZZ sessions"
        sessions_df = pd.read_excel(sessions_path, sheet_name=sheet_name_sessions)
        return baseline_df, midline_df, sessions_df
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        baseline_path = os.path.join(base_dir, "data/Zazi iZandi Children's database (Baseline)7052024 - anonymized.xlsx")
        sheet_name_baseline = "ZZ Childrens Database"
        midline_path = os.path.join(base_dir, "data/Zazi iZandi Midline Assessments database (1) - anonymized.xlsx")
        sheet_name_midline = "Childrens database"
        baseline_df = pd.read_excel(baseline_path, sheet_name=sheet_name_baseline)
        midline_df = pd.read_excel(midline_path, sheet_name=sheet_name_midline)
        sessions_path = os.path.join(base_dir, "data/Zazi iZandi Children's Session Tracker-08062024.xlsx")
        sheet_name_sessions = "ZZ sessions"
        sessions_df = pd.read_excel(sessions_path, sheet_name=sheet_name_sessions)
        return baseline_df, midline_df, sessions_df

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
        endline_path = os.path.join(dir_path, "data/ZZ Children's Database 2023 (Endline) 20231130.xlsx")
        sheet_name_endline = "Database"
        endline_df = pd.read_excel(endline_path, sheet_name=sheet_name_endline)

        sessions_path = os.path.join(dir_path, "data/Zazi iZandi Session Tracker 20231124.xlsx")
        sheet_name_sessions = "Zazi iZandi Sessions"
        sessions_df = pd.read_excel(sessions_path, sheet_name=sheet_name_sessions)
        return endline_df, sessions_df

