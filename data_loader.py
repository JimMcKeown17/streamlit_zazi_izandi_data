import pandas as pd
import os
import streamlit as st
import openpyxl
from process_survey_cto_updated import process_egra_data
import dotenv
from data_utility_functions.teampact_apis import fetch_all_survey_responses, fetch_survey_responses_nested, process_egra_survey_data

def load_mentor_visits_2025_tp():
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    filename = "survey612_mentor-visit-tracker-copy_masinyusane_2025-09-28_12-08-26.csv"
    path = os.path.join(ROOT_DIR, "data", filename)
    df = pd.read_csv(path)
    return df

def load_zazi_izandi_ecd_endline():
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    filename = "survey723_nmb-endline-ecd_masinyusane_2025-11-05_12-59-13.csv"
    path = os.path.join(ROOT_DIR, "data/Teampact", filename)
    df = pd.read_csv(path)
    return df

def load_zazi_izandi_east_london_2025_tp():
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    xhosa_filename = "survey644_egra-letters-isixhosa-el_masinyusane_2025-09-28_12-15-34.csv"
    english_filename = "survey646_egra-letters-english-el_masinyusane_2025-09-28_12-15-22.csv"
    afrikaans_filename = "survey647_egra-letters-afrikaans-el_masinyusane_2025-09-28_12-15-09.csv"
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
        st.info("🔄 Fetching NMB Baseline data from TeamPact API...")
        
        with st.spinner("Fetching isiXhosa baseline data..."):
            xhosa_responses, xhosa_questions = fetch_survey_responses_nested(survey_ids['xhosa'], api_token)
        
        with st.spinner("Fetching English baseline data..."):
            english_responses, english_questions = fetch_survey_responses_nested(survey_ids['english'], api_token)
        
        with st.spinner("Fetching Afrikaans baseline data..."):
            afrikaans_responses, afrikaans_questions = fetch_survey_responses_nested(survey_ids['afrikaans'], api_token)
        
        if not all([xhosa_responses, english_responses, afrikaans_responses]):
            st.error("Failed to fetch data from one or more surveys")
            return None, None, None
        
        # Process the nested EGRA data
        xhosa_df = process_egra_survey_data(xhosa_responses, survey_ids['xhosa'])
        english_df = process_egra_survey_data(english_responses, survey_ids['english']) 
        afrikaans_df = process_egra_survey_data(afrikaans_responses, survey_ids['afrikaans'])
        
        st.success(f"✅ NMB Baseline API data loaded successfully!")
        st.info(f"Records: isiXhosa ({len(xhosa_df)}), English ({len(english_df)}), Afrikaans ({len(afrikaans_df)})")
        
        return xhosa_df, english_df, afrikaans_df
    
    except Exception as e:
        st.error(f"Error loading API data: {str(e)}")
        return None, None, None

def normalize_endline_columns(df, language_suffix):
    """
    Normalize endline CSV columns to match baseline format
    The endline CSVs have different column names and structure
    """
    # Rename columns to match baseline format WITH language suffix
    # The baseline has format: "Total cells correct - EGRA Letters - isiXhosa"
    # The endline has two formats:
    #   - isiXhosa: "Total cells correct - NMB Schools Endline isiXhosa" (no parentheses)
    #   - English/Afrikaans: "Total cells correct - NMB Schools Endline (English)" (with parentheses)
    # We need to convert to baseline format so duplicate_columns_without_language() works
    
    # Try both patterns (with and without parentheses)
    column_mapping = {
        'Participant ID': 'User ID',
        # Without parentheses (isiXhosa)
        f'Total cells correct - NMB Schools Endline {language_suffix}': f'Total cells correct - EGRA Letters - {language_suffix}',
        f'Total cells incorrect - NMB Schools Endline {language_suffix}': f'Total cells incorrect - EGRA Letters - {language_suffix}',
        f'Total cells attempted - NMB Schools Endline {language_suffix}': f'Total cells attempted - EGRA Letters - {language_suffix}',
        f'Total cells not attempted - NMB Schools Endline {language_suffix}': f'Total cells not attempted - EGRA Letters - {language_suffix}',
        f'Assessment Complete? - NMB Schools Endline {language_suffix}': f'Assessment Complete? - EGRA Letters - {language_suffix}',
        f'Stop rule reached? - NMB Schools Endline {language_suffix}': f'Stop rule reached? - EGRA Letters - {language_suffix}',
        f'Timer elapsed? - NMB Schools Endline {language_suffix}': f'Timer elapsed? - EGRA Letters - {language_suffix}',
        f'Time elapsed at completion - NMB Schools Endline {language_suffix}': f'Time elapsed at completion - EGRA Letters - {language_suffix}',
        # With parentheses (English/Afrikaans)
        f'Total cells correct - NMB Schools Endline ({language_suffix})': f'Total cells correct - EGRA Letters - {language_suffix}',
        f'Total cells incorrect - NMB Schools Endline ({language_suffix})': f'Total cells incorrect - EGRA Letters - {language_suffix}',
        f'Total cells attempted - NMB Schools Endline ({language_suffix})': f'Total cells attempted - EGRA Letters - {language_suffix}',
        f'Total cells not attempted - NMB Schools Endline ({language_suffix})': f'Total cells not attempted - EGRA Letters - {language_suffix}',
        f'Assessment Complete? - NMB Schools Endline ({language_suffix})': f'Assessment Complete? - EGRA Letters - {language_suffix}',
        f'Stop rule reached? - NMB Schools Endline ({language_suffix})': f'Stop rule reached? - EGRA Letters - {language_suffix}',
        f'Timer elapsed? - NMB Schools Endline ({language_suffix})': f'Timer elapsed? - EGRA Letters - {language_suffix}',
        f'Time elapsed at completion - NMB Schools Endline ({language_suffix})': f'Time elapsed at completion - EGRA Letters - {language_suffix}'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Derive Grade from Class Name (first character)
    if 'Class Name' in df.columns:
        df['Grade '] = df['Class Name'].astype(str).str[0].apply(lambda x: f'Grade {x}' if x else '')
    else:
        df['Grade '] = ''
    
    # Add missing columns that process_teampact_data expects
    if 'Email' not in df.columns:
        df['Email'] = ''
    if 'Class' not in df.columns:
        df['Class'] = ''
    if 'Learner First Name' not in df.columns:
        df['Learner First Name'] = ''
    if 'Learner Surname ' not in df.columns:
        df['Learner Surname '] = ''
    if 'Learner Gender' not in df.columns:
        df['Learner Gender'] = ''
    if 'Learner EMIS' not in df.columns:
        df['Learner EMIS'] = ''
    
    return df

def load_zazi_izandi_nmb_2025_endline_tp_csv():
    """
    Load NMB 2025 endline data from CSV files
    Returns DataFrames for isiXhosa, English, and Afrikaans
    """
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    
    # CSV filenames for NMB endline assessments
    xhosa_filename = "survey725_nmb-schools-endline-isixhosa_masinyusane_2025-11-04_10-59-29.csv"
    english_filename = "survey726_nmb-schools-endline-english_masinyusane_2025-11-04_11-21-19.csv"
    afrikaans_filename = "survey727_nmb-schools-endline-afrikaans_masinyusane_2025-11-04_11-21-58.csv"
    
    xhosa_path = os.path.join(ROOT_DIR, "data/Teampact", xhosa_filename)
    english_path = os.path.join(ROOT_DIR, "data/Teampact", english_filename)
    afrikaans_path = os.path.join(ROOT_DIR, "data/Teampact", afrikaans_filename)
    
    xhosa_df = pd.read_csv(xhosa_path)
    english_df = pd.read_csv(english_path)
    afrikaans_df = pd.read_csv(afrikaans_path)
    
    # Normalize column names to match baseline format
    xhosa_df = normalize_endline_columns(xhosa_df, 'isiXhosa')
    english_df = normalize_endline_columns(english_df, 'English')
    afrikaans_df = normalize_endline_columns(afrikaans_df, 'Afrikaans')
    
    return xhosa_df, english_df, afrikaans_df

def load_zazi_izandi_nmb_2025_endline_tp():
    """
    Load NMB 2025 endline data via TeamPact API
    Handles nested survey response structure with EGRA assessment data
    Returns DataFrames for isiXhosa, English, and Afrikaans
    """
    dotenv.load_dotenv()
    api_token = os.getenv("TEAMPACT_API_TOKEN")
    
    if not api_token:
        st.error("TEAMPACT_API_TOKEN not found in environment variables")
        return None, None, None
    
    # Survey IDs for NMB endline assessments
    survey_ids = {
        'xhosa': 725,
        'english': 726, 
        'afrikaans': 727
    }
    
    # Fetch data for each language
    try:
        st.info("🔄 Fetching NMB Endline data from TeamPact API...")
        
        with st.spinner("Fetching isiXhosa endline data..."):
            xhosa_responses, xhosa_questions = fetch_survey_responses_nested(survey_ids['xhosa'], api_token)
        
        with st.spinner("Fetching English endline data..."):
            english_responses, english_questions = fetch_survey_responses_nested(survey_ids['english'], api_token)
        
        with st.spinner("Fetching Afrikaans endline data..."):
            afrikaans_responses, afrikaans_questions = fetch_survey_responses_nested(survey_ids['afrikaans'], api_token)
        
        if not all([xhosa_responses, english_responses, afrikaans_responses]):
            st.error("Failed to fetch data from one or more surveys")
            return None, None, None
        
        # Process the nested EGRA data
        xhosa_df = process_egra_survey_data(xhosa_responses, survey_ids['xhosa'])
        english_df = process_egra_survey_data(english_responses, survey_ids['english']) 
        afrikaans_df = process_egra_survey_data(afrikaans_responses, survey_ids['afrikaans'])
        
        st.success(f"✅ NMB Endline API data loaded successfully!")
        st.info(f"Records: isiXhosa ({len(xhosa_df)}), English ({len(english_df)}), Afrikaans ({len(afrikaans_df)})")
        
        return xhosa_df, english_df, afrikaans_df
    
    except Exception as e:
        st.error(f"Error loading NMB Endline API data: {str(e)}")
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
    """
    Load 2024 data from Parquet (fast) or Excel (fallback).
    
    Returns raw DataFrames. Processing should be done separately.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try loading from parquet first (10-50x faster)
    parquet_dir = os.path.join(base_dir, "data/parquet/raw")
    parquet_files = {
        'baseline': os.path.join(parquet_dir, "2024_baseline.parquet"),
        'midline': os.path.join(parquet_dir, "2024_midline.parquet"),
        'sessions': os.path.join(parquet_dir, "2024_sessions.parquet"),
        'baseline2': os.path.join(parquet_dir, "2024_baseline2.parquet"),
        'endline': os.path.join(parquet_dir, "2024_endline.parquet"),
        'endline2': os.path.join(parquet_dir, "2024_endline2.parquet"),
    }
    
    # Check if all parquet files exist
    if all(os.path.exists(path) for path in parquet_files.values()):
        baseline_df = pd.read_parquet(parquet_files['baseline'])
        midline_df = pd.read_parquet(parquet_files['midline'])
        sessions_df = pd.read_parquet(parquet_files['sessions'])
        baseline2_df = pd.read_parquet(parquet_files['baseline2'])
        endline_df = pd.read_parquet(parquet_files['endline'])
        endline2_df = pd.read_parquet(parquet_files['endline2'])
        
        # Convert key columns to proper numeric types
        numeric_cols = ['Mcode', 'Number of Sessions']
        for df in [baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df]:
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df
    
    # Fallback to Excel loading if parquet not found
    if 'user' in st.session_state and st.session_state.user:
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
    """
    Load 2023 data from Parquet (fast) or Excel (fallback).
    
    Returns processed DataFrame directly if available in parquet,
    otherwise loads and processes from Excel files.
    """
    dir_path = os.path.dirname(os.path.abspath(__file__))
    
    # Try loading from parquet first (10-50x faster)
    parquet_path = os.path.join(dir_path, "data/parquet/raw/2023_endline.parquet")
    sessions_parquet_path = os.path.join(dir_path, "data/parquet/raw/2023_sessions.parquet")
    
    if os.path.exists(parquet_path) and os.path.exists(sessions_parquet_path):
        endline_df = pd.read_parquet(parquet_path)
        sessions_df = pd.read_parquet(sessions_parquet_path)
        
        # Convert key columns to proper numeric types
        numeric_cols = ['Mcode']
        for col in numeric_cols:
            if col in endline_df.columns:
                endline_df[col] = pd.to_numeric(endline_df[col], errors='coerce')
            if col in sessions_df.columns:
                sessions_df[col] = pd.to_numeric(sessions_df[col], errors='coerce')
        
        return endline_df, sessions_df
    
    # Fallback to Excel loading if parquet not found
    if 'user' in st.session_state and st.session_state.user:
        endline_path = os.path.join(dir_path, "data/ZZ Children's Database 2023 (Endline) 20231130.xlsx")
        sheet_name_endline = "Database"
        endline_df = pd.read_excel(endline_path, sheet_name=sheet_name_endline, engine='openpyxl')

        sessions_path = os.path.join(dir_path, "data/Zazi iZandi Session Tracker 20231124.xlsx")
        sheet_name_sessions = "Zazi iZandi Sessions"
        sessions_df = pd.read_excel(sessions_path, sheet_name=sheet_name_sessions, engine='openpyxl')
        return endline_df, sessions_df
    else:
        endline_path = os.path.join(dir_path, "data/ZZ Children's Database 2023 (Endline) 20231130 - anonymized.xlsx")
        sheet_name_endline = "Database"
        endline_df = pd.read_excel(endline_path, sheet_name=sheet_name_endline, engine='openpyxl')

        sessions_path = os.path.join(dir_path, "data/Zazi iZandi Session Tracker 20231124.xlsx")
        sheet_name_sessions = "Zazi iZandi Sessions"
        sessions_df = pd.read_excel(sessions_path, sheet_name=sheet_name_sessions, engine='openpyxl')
        return endline_df, sessions_df


# ---- 2025 Parquet Loaders (frozen data) ----

def _get_parquet_path(filename):
    """Get absolute path to a parquet file in data/parquet/raw/"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "parquet", "raw", filename)


@st.cache_data
def load_sessions_2025():
    """Load frozen 2025 session data from parquet file.
    Returns DataFrame with school_type and mentor columns added."""
    from database_utils import get_school_type, get_mentor
    path = _get_parquet_path("2025_sessions.parquet")
    df = pd.read_parquet(path)
    df['school_type'] = df['program_name'].apply(get_school_type)
    df['mentor'] = df['program_name'].apply(get_mentor)
    return df


@st.cache_data
def load_assessments_endline_2025():
    """Load frozen 2025 endline assessment data from parquet file."""
    path = _get_parquet_path("2025_assessment_endline.parquet")
    return pd.read_parquet(path)


@st.cache_data(ttl=3600)
def load_sessions_2026():
    """Load 2026 session data from parquet file (updated nightly by backup_2026_to_parquet).
    Returns DataFrame with school_type and mentor columns added."""
    from database_utils import get_school_type, get_mentor
    path = _get_parquet_path("2026_sessions.parquet")
    df = pd.read_parquet(path)
    df['school_type'] = df['program_name'].apply(get_school_type)
    df['mentor'] = df['program_name'].apply(get_mentor)
    return df


@st.cache_data(ttl=3600)
def load_assessments_2026():
    """Load 2026 baseline assessment data from parquet (updated nightly)."""
    path = _get_parquet_path("2026_assessments.parquet")
    return pd.read_parquet(path)


@st.cache_data(ttl=3600)
def load_mentor_visits_2026():
    """Load 2026 mentor visit data from parquet (updated nightly)."""
    path = _get_parquet_path("2026_mentor_visits.parquet")
    df = pd.read_parquet(path)
    for col in ['response_start_at', 'response_end_at']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    df['Response Date'] = df['response_start_at']
    return df

