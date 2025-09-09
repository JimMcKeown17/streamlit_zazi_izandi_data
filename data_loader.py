import pandas as pd
import os
import streamlit as st
import openpyxl
from process_survey_cto_updated import process_egra_data
import dotenv
from data_utility_functions.teampact_apis import fetch_all_survey_responses

def load_zazi_izandi_east_london_2025_tp():
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    xhosa_filename = "survey644_egra-letters-isixhosa-el_masinyusane_2025-09-09_12-43.csv"
    english_filename = "survey646_egra-letters-english-el_masinyusane_2025-09-09_12-46.csv"
    afrikaans_filename = "survey647_egra-letters-afrikaans-el_masinyusane_2025-09-09_12-46.csv"
    xhosa_path = os.path.join(ROOT_DIR, "data/Teampact", xhosa_filename)
    english_path = os.path.join(ROOT_DIR, "data/Teampact", english_filename)
    afrikaans_path = os.path.join(ROOT_DIR, "data/Teampact", afrikaans_filename)
    xhosa_df = pd.read_csv(xhosa_path)
    english_df = pd.read_csv(english_path)
    afrikaans_df = pd.read_csv(afrikaans_path)
    return xhosa_df, english_df, afrikaans_df

def load_zazi_izandi_east_london_2025_tp_api():
    """
    Load TeamPact data via API instead of CSV files
    Returns the same format as load_zazi_izandi_2025_tp() for compatibility
    """
    dotenv.load_dotenv()
    api_token = os.getenv("TEAMPACT_API_TOKEN")
    
    if not api_token:
        st.error("TEAMPACT_API_TOKEN not found in environment variables")
        return None, None, None
    
    # Survey IDs for each language
    survey_ids = {
        'xhosa': 644,
        'english': 646, 
        'afrikaans': 647
    }
    
    # Fetch data for each language
    try:
        st.info("🔄 Fetching data from TeamPact API...")
        
        with st.spinner("Fetching isiXhosa data..."):
            xhosa_responses = fetch_all_survey_responses(survey_ids['xhosa'], api_token)
        
        with st.spinner("Fetching English data..."):
            english_responses = fetch_all_survey_responses(survey_ids['english'], api_token)
        
        with st.spinner("Fetching Afrikaans data..."):
            afrikaans_responses = fetch_all_survey_responses(survey_ids['afrikaans'], api_token)
        
        if not all([xhosa_responses, english_responses, afrikaans_responses]):
            st.error("Failed to fetch data from one or more surveys")
            return None, None, None
        
        # Convert to DataFrames (API returns list of dicts, just like CSV would)
        xhosa_df = pd.json_normalize(xhosa_responses)
        english_df = pd.json_normalize(english_responses) 
        afrikaans_df = pd.json_normalize(afrikaans_responses)
        
        st.success(f"✅ API data loaded successfully!")
        st.info(f"Records: isiXhosa ({len(xhosa_df)}), English ({len(english_df)}), Afrikaans ({len(afrikaans_df)})")
        
        return xhosa_df, english_df, afrikaans_df
    
    except Exception as e:
        st.error(f"Error loading API data: {str(e)}")
        return None, None, None

def load_zazi_izandi_2025_tp():
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    xhosa_filename = "survey575_egra-letters-isixhosa_masinyusane_2025-08-19_11-02.csv"
    english_filename = "survey578_egra-letters-english_masinyusane_2025-08-19_10-59.csv"
    afrikaans_filename = "survey576_egra-letters-afrikaans_masinyusane_2025-08-19_11-01.csv"
    xhosa_path = os.path.join(ROOT_DIR, "data/Teampact", xhosa_filename)
    english_path = os.path.join(ROOT_DIR, "data/Teampact", english_filename)
    afrikaans_path = os.path.join(ROOT_DIR, "data/Teampact", afrikaans_filename)
    xhosa_df = pd.read_csv(xhosa_path)
    english_df = pd.read_csv(english_path)
    afrikaans_df = pd.read_csv(afrikaans_path)
    return xhosa_df, english_df, afrikaans_df

def load_zazi_izandi_2025_tp_api():
    """
    Load TeamPact data via API instead of CSV files
    Returns the same format as load_zazi_izandi_2025_tp() for compatibility
    """
    dotenv.load_dotenv()
    api_token = os.getenv("TEAMPACT_API_TOKEN")
    
    if not api_token:
        st.error("TEAMPACT_API_TOKEN not found in environment variables")
        return None, None, None
    
    # Survey IDs for each language
    survey_ids = {
        'xhosa': 575,
        'english': 578, 
        'afrikaans': 576
    }
    
    # Fetch data for each language
    try:
        st.info("🔄 Fetching data from TeamPact API...")
        
        with st.spinner("Fetching isiXhosa data..."):
            xhosa_responses = fetch_all_survey_responses(survey_ids['xhosa'], api_token)
        
        with st.spinner("Fetching English data..."):
            english_responses = fetch_all_survey_responses(survey_ids['english'], api_token)
        
        with st.spinner("Fetching Afrikaans data..."):
            afrikaans_responses = fetch_all_survey_responses(survey_ids['afrikaans'], api_token)
        
        if not all([xhosa_responses, english_responses, afrikaans_responses]):
            st.error("Failed to fetch data from one or more surveys")
            return None, None, None
        
        # Convert to DataFrames (API returns list of dicts, just like CSV would)
        xhosa_df = pd.json_normalize(xhosa_responses)
        english_df = pd.json_normalize(english_responses) 
        afrikaans_df = pd.json_normalize(afrikaans_responses)
        
        st.success(f"✅ API data loaded successfully!")
        st.info(f"Records: isiXhosa ({len(xhosa_df)}), English ({len(english_df)}), Afrikaans ({len(afrikaans_df)})")
        
        return xhosa_df, english_df, afrikaans_df
    
    except Exception as e:
        st.error(f"Error loading API data: {str(e)}")
        return None, None, None

def load_zazi_izandi_2025():
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))

    @st.cache_data
    def load_egra_data(children_filename: str, ta_filename: str):
        """
        Caches the DataFrame loading and processing so it doesn't
        re-run on every Streamlit re-execution or widget change.
        """
        children_path = os.path.join(ROOT_DIR, "data", children_filename)
        ta_path       = os.path.join(ROOT_DIR, "data", ta_filename)

        df, df_ecd = process_egra_data(
            children_file=children_path,
            ta_file=ta_path
        )
        return df, df_ecd
    if 'user' in st.session_state and st.session_state.user:
        df_full, df_ecd = load_egra_data(
                    children_filename="ZZ - EGRA form [Eastern Cape]-assessment_repeat - Jun 17.csv",
                    ta_filename="ZZ - EGRA form [Eastern Cape] - Jun 17.csv"
                )
    else:
        df_full, df_ecd = load_egra_data(
                    children_filename="ZZ - EGRA form [Eastern Cape]-assessment_repeat - Jun 17 - anonymized.csv",
                    ta_filename="ZZ - EGRA form [Eastern Cape] - Jun 17 - anonymized.csv"
                )
    return df_full, df_ecd


def load_zazi_izandi_new_schools_2024():
    if 'user' in st.session_state and st.session_state.user:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        endline_path = os.path.join(base_dir, "data/New ZZ 1.0 Schools Endline Assessment 2024.xlsx")
        sheet_name_endline = "Data"
        endline_df = pd.read_excel(endline_path, sheet_name=sheet_name_endline, engine='openpyxl')
        return endline_df
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        endline_path = os.path.join(base_dir, "data/New ZZ 1.0 Schools Endline Assessment 2024 - Anonymized.xlsx")
        sheet_name_endline = "Data"
        endline_df = pd.read_excel(endline_path, sheet_name=sheet_name_endline, engine='openpyxl')
        return endline_df
def load_zazi_izandi_2024():
    if 'user' in st.session_state and st.session_state.user:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        baseline_path = os.path.join(base_dir, "data/Zazi iZandi Children's database (Baseline)7052024.xlsx")
        sheet_name_baseline = "ZZ Childrens Database"
        midline_path = os.path.join(base_dir, "data/Zazi iZandi Midline Assessments database (1).xlsx")
        sheet_name_midline = "Childrens database"
        endline_path = os.path.join(base_dir, "data/20241115 - Zazi iZandi 2024 Endline Assessment  - 1.0.xlsx")
        sheet_name_endline = "Endline Assessment"
        baseline_df = pd.read_excel(baseline_path, sheet_name=sheet_name_baseline, engine='openpyxl')
        midline_df = pd.read_excel(midline_path, sheet_name=sheet_name_midline, engine='openpyxl')
        endline_df = pd.read_excel(endline_path, sheet_name=sheet_name_endline, engine='openpyxl')
        sessions_path = os.path.join(base_dir, "data/Zazi iZandi Children's Session Tracker-08062024.xlsx")
        sheet_name_sessions = "ZZ sessions"
        sessions_df = pd.read_excel(sessions_path, sheet_name=sheet_name_sessions, engine='openpyxl')
        sheet_name_zz2 = "ZZ 2.0 Baseline"
        baseline_zz2_path = os.path.join(base_dir, "data/ZZ 2.0 Baseline Assessment.xlsx")
        baseline2_df = pd.read_excel(baseline_zz2_path, sheet_name=sheet_name_zz2, engine='openpyxl')
        sheet_name_zz2_endline = "ZZ 2.0 Endline"
        endline_zz2_path = os.path.join(base_dir, "data/20241112 - Zazi iZandi 2.0 Endline Assessment.xlsx")
        endline2_df = pd.read_excel(endline_zz2_path, sheet_name=sheet_name_zz2_endline, engine='openpyxl')
        return baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        baseline_path = os.path.join(base_dir, "data/Zazi iZandi Children's database (Baseline)7052024 - anonymized.xlsx")
        sheet_name_baseline = "ZZ Childrens Database"
        midline_path = os.path.join(base_dir, "data/Zazi iZandi Midline Assessments database (1) - anonymized.xlsx")
        sheet_name_midline = "Childrens database"
        endline_path = os.path.join(base_dir, "data/20241115 - Zazi iZandi 2024 Endline Assessment  - 1.0 - anonymized.xlsx")
        sheet_name_endline = "Endline Assessment"
        baseline_df = pd.read_excel(baseline_path, sheet_name=sheet_name_baseline, engine='openpyxl')
        midline_df = pd.read_excel(midline_path, sheet_name=sheet_name_midline, engine='openpyxl')
        endline_df = pd.read_excel(endline_path, sheet_name=sheet_name_endline, engine='openpyxl')
        sessions_path = os.path.join(base_dir, "data/Zazi iZandi Children's Session Tracker-08062024.xlsx")
        sheet_name_sessions = "ZZ sessions"
        sessions_df = pd.read_excel(sessions_path, sheet_name=sheet_name_sessions, engine='openpyxl')
        sheet_name_zz2 = "ZZ 2.0 Baseline"
        baseline_zz2_path = os.path.join(base_dir, "data/ZZ 2.0 Baseline Assessment.xlsx")
        sheet_name_zz2_endline = "ZZ 2.0 Endline"
        baseline2_df = pd.read_excel(baseline_zz2_path, sheet_name=sheet_name_zz2, engine='openpyxl')
        endline_zz2_path = os.path.join(base_dir, "data/20241112 - Zazi iZandi 2.0 Endline Assessment - Anonymized.xlsx")
        endline2_df = pd.read_excel(endline_zz2_path, sheet_name=sheet_name_zz2_endline, engine='openpyxl')
        return baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df

def load_zazi_izandi_2023():
    if 'user' in st.session_state and st.session_state.user:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        endline_path = os.path.join(dir_path, "data/ZZ Children's Database 2023 (Endline) 20231130.xlsx")
        sheet_name_endline = "Database"
        endline_df = pd.read_excel(endline_path, sheet_name=sheet_name_endline, engine='openpyxl')

        sessions_path = os.path.join(dir_path, "data/Zazi iZandi Session Tracker 20231124.xlsx")
        sheet_name_sessions = "Zazi iZandi Sessions"
        sessions_df = pd.read_excel(sessions_path, sheet_name=sheet_name_sessions, engine='openpyxl')
        return endline_df, sessions_df
    else:
        dir_path = os.path.dirname(os.path.abspath(__file__))
        endline_path = os.path.join(dir_path, "data/ZZ Children's Database 2023 (Endline) 20231130 - anonymized.xlsx")
        sheet_name_endline = "Database"
        endline_df = pd.read_excel(endline_path, sheet_name=sheet_name_endline, engine='openpyxl')

        sessions_path = os.path.join(dir_path, "data/Zazi iZandi Session Tracker 20231124.xlsx")
        sheet_name_sessions = "Zazi iZandi Sessions"
        sessions_df = pd.read_excel(sessions_path, sheet_name=sheet_name_sessions, engine='openpyxl')
        return endline_df, sessions_df

