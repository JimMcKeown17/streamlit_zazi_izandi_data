import pandas as pd
import os
import streamlit as st
import openpyxl
from process_survey_cto_updated import process_egra_data
import dotenv
from data_utility_functions.teampact_apis import fetch_all_survey_responses, fetch_survey_responses_nested, process_egra_survey_data
from data_privacy import is_authenticated, mask_dataframe

DATAQUEST_SCHOOLS_2025 = {
    "Aaron Gqadu Primary School",
    "Ben Sinuka Primary School",
    "Coega Primary School",
    "Dumani Primary School",
    "Ebongweni Public Primary School",
    "Elufefeni Primary School",
    "Empumalanga Primary School",
    "Enkululekweni Primary School",
    "Esitiyeni Public Primary School",
    "Fumisukoma Primary School",
    "Ilinge Primary School",
    "Isaac Booi Senior Primary School",
    "James Ntungwana Primary School",
    "Jarvis Gqamlana Public Primary School",
    "Joe Slovo Primary School",
    "Little Flower Primary School",
    "Magqabi Primary School",
    "Mjuleni Junior Primary School",
    "Mngcunube Primary School",
    "Molefe Senior Primary School",
    "Noninzi Luzipho Primary School",
    "Ntlemeza Primary School",
    "Phindubuye Primary School",
    "Seyisi Primary School",
    "Sikhothina Primary School",
    "Soweto-On-Sea Primary School",
    "Stephen Nkomo Senior Primary School",
    "W B Tshume Primary School",
}

EAST_LONDON_SCHOOLS_2025 = {
    "Brownlee Primary School",
    "Bumbanani Primary School",
    "Chuma Junior Primary School",
    "Duncan Village Public School",
    "Ebhotwe Junior Full Service School",
    "Emncotsho Primary School",
    "Encotsheni Senior Primary School",
    "Equleni Junior Primary School",
    "Fanti Gaqa Senior Primary School",
    "Inkqubela Junior Primary School",
    "Isibane Junior Primary School",
    "Isithsaba Junior Primary School",
    "Jityaza Combined Primary School",
    "Khanyisa Junior Primary School",
    "Lunga Junior Primary School",
    "Lwandisa Junior Primary School",
    "Manyano Junior Primary School",
    "Masakhe Primary School",
    "Mdantsane Junior Primary School",
    "Misukukhanya Senior Primary School",
    "Mzoxolo Senior Primary School",
    "Nkangeleko Intermediate School",
    "Nkosinathi Primary School",
    "Nobhotwe Junior Primary School",
    "Nontombi Matta Junior Primary School",
    "Nontsikelelo Junior Primary School",
    "Nontuthuzelo Primary School",
    "Nqonqweni Primary School",
    "Nzuzo Junior Primary School",
    "Qaqamba Junior Primary School",
    "R H Godlo Junior Primary School",
    "Sakhile Senior Primary School",
    "Shad Mashologu Junior Primary School",
    "St John'S Road Junior Secondary School",
    "Thembeka Junior Primary School",
    "Vuthondaba Full Service School",
    "W.N. Madikizela-Mandela Primary School",
    "Zamani Junior Primary School",
    "Zanempucuko Senior Secondary School",
    "Zanokukhanya Junior Primary School",
    "Zuzile Junior Primary School",
}


def _mask_frames(*frames, dataset_key):
    return tuple(mask_dataframe(frame, dataset_key=dataset_key) for frame in frames)


def _base_dir():
    return os.path.dirname(os.path.abspath(__file__))


def _get_programme_area(program_name):
    if program_name in EAST_LONDON_SCHOOLS_2025:
        return "BCM"
    return "NMB"


def _is_dataquest_school(program_name):
    return program_name in DATAQUEST_SCHOOLS_2025

def load_mentor_visits_2025_tp():
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    filename = "survey612_mentor-visit-tracker-copy_masinyusane_2025-09-28_12-08-26.csv"
    path = os.path.join(ROOT_DIR, "data", filename)
    df = pd.read_csv(path)
    return mask_dataframe(df, dataset_key="mentor_visits_2025")

def load_zazi_izandi_ecd_endline():
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
    filename = "survey723_nmb-endline-ecd_masinyusane_2025-11-05_12-59-13.csv"
    path = os.path.join(ROOT_DIR, "data/Teampact", filename)
    df = pd.read_csv(path)
    return mask_dataframe(df, dataset_key="ecd_endline_2025")

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
    return _mask_frames(xhosa_df, english_df, afrikaans_df, dataset_key="east_london_baseline_2025")

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
        
        return _mask_frames(xhosa_df, english_df, afrikaans_df, dataset_key="east_london_baseline_2025")
    
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
    return _mask_frames(xhosa_df, english_df, afrikaans_df, dataset_key="nmb_baseline_2025_tp")

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
        
        return _mask_frames(xhosa_df, english_df, afrikaans_df, dataset_key="nmb_baseline_2025_tp")
    
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
    
    return _mask_frames(xhosa_df, english_df, afrikaans_df, dataset_key="nmb_endline_2025_tp")

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
        
        return _mask_frames(xhosa_df, english_df, afrikaans_df, dataset_key="nmb_endline_2025_tp")
    
    except Exception as e:
        st.error(f"Error loading NMB Endline API data: {str(e)}")
        return None, None, None

def load_zazi_izandi_2025():
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))

    @st.cache_data
    def load_egra_data():
        """
        Caches the DataFrame loading and processing so it doesn't
        re-run on every Streamlit re-execution or widget change.
        """
        children_path = os.path.join(ROOT_DIR, "data", "ZZ - EGRA form [Eastern Cape]-assessment_repeat - Jun 17.csv")
        ta_path = os.path.join(ROOT_DIR, "data", "ZZ - EGRA form [Eastern Cape] - Jun 17.csv")

        df, df_ecd = process_egra_data(
            children_file=children_path,
            ta_file=ta_path
        )
        return df, df_ecd
    df_full, df_ecd = load_egra_data()
    return _mask_frames(df_full, df_ecd, dataset_key="survey_cto_2025")


def load_zazi_izandi_new_schools_2024():
    @st.cache_data
    def _load_new_schools_excel():
        endline_path = os.path.join(_base_dir(), "data/New ZZ 1.0 Schools Endline Assessment 2024.xlsx")
        return pd.read_excel(endline_path, sheet_name="Data", engine='openpyxl')

    endline_df = _load_new_schools_excel()
    return mask_dataframe(endline_df, dataset_key="new_schools_2024")


@st.cache_data
def _load_zazi_izandi_2024_from_parquet():
    base_dir = _base_dir()
    parquet_dir = os.path.join(base_dir, "data/parquet/raw")
    parquet_files = {
        'baseline': os.path.join(parquet_dir, "2024_baseline.parquet"),
        'midline': os.path.join(parquet_dir, "2024_midline.parquet"),
        'sessions': os.path.join(parquet_dir, "2024_sessions.parquet"),
        'baseline2': os.path.join(parquet_dir, "2024_baseline2.parquet"),
        'endline': os.path.join(parquet_dir, "2024_endline.parquet"),
        'endline2': os.path.join(parquet_dir, "2024_endline2.parquet"),
    }
    if not all(os.path.exists(path) for path in parquet_files.values()):
        return None

    baseline_df = pd.read_parquet(parquet_files['baseline'])
    midline_df = pd.read_parquet(parquet_files['midline'])
    sessions_df = pd.read_parquet(parquet_files['sessions'])
    baseline2_df = pd.read_parquet(parquet_files['baseline2'])
    endline_df = pd.read_parquet(parquet_files['endline'])
    endline2_df = pd.read_parquet(parquet_files['endline2'])

    numeric_cols = ['Mcode', 'Number of Sessions']
    for df in [baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df]:
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

    return baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df


@st.cache_data
def _load_zazi_izandi_2024_from_excel():
    base_dir = _base_dir()
    baseline_path = os.path.join(base_dir, "data/Zazi iZandi Children's database (Baseline)7052024.xlsx")
    midline_path = os.path.join(base_dir, "data/Zazi iZandi Midline Assessments database (1).xlsx")
    endline_path = os.path.join(base_dir, "data/20241115 - Zazi iZandi 2024 Endline Assessment  - 1.0.xlsx")
    sessions_path = os.path.join(base_dir, "data/Zazi iZandi Children's Session Tracker-08062024.xlsx")
    baseline_zz2_path = os.path.join(base_dir, "data/ZZ 2.0 Baseline Assessment.xlsx")
    endline_zz2_path = os.path.join(base_dir, "data/20241112 - Zazi iZandi 2.0 Endline Assessment.xlsx")

    baseline_df = pd.read_excel(baseline_path, sheet_name="ZZ Childrens Database", engine='openpyxl')
    midline_df = pd.read_excel(midline_path, sheet_name="Childrens database", engine='openpyxl')
    endline_df = pd.read_excel(endline_path, sheet_name="Endline Assessment", engine='openpyxl')
    sessions_df = pd.read_excel(sessions_path, sheet_name="ZZ sessions", engine='openpyxl')
    baseline2_df = pd.read_excel(baseline_zz2_path, sheet_name="ZZ 2.0 Baseline", engine='openpyxl')
    endline2_df = pd.read_excel(endline_zz2_path, sheet_name="ZZ 2.0 Endline", engine='openpyxl')
    return baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df


def load_zazi_izandi_2024():
    """
    Load 2024 data from Parquet (fast) or Excel (fallback).
    
    Returns raw DataFrames. Processing should be done separately.
    """
    if is_authenticated():
        frames = _load_zazi_izandi_2024_from_excel()
    else:
        frames = _load_zazi_izandi_2024_from_parquet() or _load_zazi_izandi_2024_from_excel()
    return _mask_frames(*frames, dataset_key="zazi_izandi_2024")


@st.cache_data
def _load_zazi_izandi_2023_from_parquet():
    dir_path = _base_dir()
    parquet_path = os.path.join(dir_path, "data/parquet/raw/2023_endline.parquet")
    sessions_parquet_path = os.path.join(dir_path, "data/parquet/raw/2023_sessions.parquet")
    if not (os.path.exists(parquet_path) and os.path.exists(sessions_parquet_path)):
        return None

    endline_df = pd.read_parquet(parquet_path)
    sessions_df = pd.read_parquet(sessions_parquet_path)
    for col in ['Mcode']:
        if col in endline_df.columns:
            endline_df[col] = pd.to_numeric(endline_df[col], errors='coerce')
        if col in sessions_df.columns:
            sessions_df[col] = pd.to_numeric(sessions_df[col], errors='coerce')
    return endline_df, sessions_df


@st.cache_data
def _load_zazi_izandi_2023_from_excel():
    dir_path = _base_dir()
    endline_path = os.path.join(dir_path, "data/ZZ Children's Database 2023 (Endline) 20231130.xlsx")
    sessions_path = os.path.join(dir_path, "data/Zazi iZandi Session Tracker 20231124.xlsx")
    endline_df = pd.read_excel(endline_path, sheet_name="Database", engine='openpyxl')
    sessions_df = pd.read_excel(sessions_path, sheet_name="Zazi iZandi Sessions", engine='openpyxl')
    return endline_df, sessions_df


def load_zazi_izandi_2023():
    """
    Load 2023 data from Parquet (fast) or Excel (fallback).
    
    Returns processed DataFrame directly if available in parquet,
    otherwise loads and processes from Excel files.
    """
    if is_authenticated():
        frames = _load_zazi_izandi_2023_from_excel()
    else:
        frames = _load_zazi_izandi_2023_from_parquet() or _load_zazi_izandi_2023_from_excel()
    return _mask_frames(*frames, dataset_key="zazi_izandi_2023")


@st.cache_data
def _load_2024_session_tracker_monthly_raw():
    session_tracker_path = os.path.join(_base_dir(), "data/Zazi iZandi Session Tracker 18102024.xlsx")
    return pd.read_excel(session_tracker_path, sheet_name="Sessions")


def load_2024_session_tracker_monthly():
    return mask_dataframe(_load_2024_session_tracker_monthly_raw(), dataset_key="session_tracker_2024")


# ---- 2025 Parquet Loaders (frozen data) ----

def _get_parquet_path(filename):
    """Get absolute path to a parquet file in data/parquet/raw/"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "parquet", "raw", filename)


@st.cache_data
def _load_sessions_2025_raw():
    """Load frozen 2025 session data from parquet file.
    Returns DataFrame with school_type and mentor columns added."""
    from database_utils import get_school_type, get_mentor
    path = _get_parquet_path("2025_sessions.parquet")
    df = pd.read_parquet(path)
    df['school_type'] = df['program_name'].apply(get_school_type)
    df['mentor'] = df['program_name'].apply(get_mentor)
    df['programme_area'] = df['program_name'].apply(_get_programme_area)
    df['is_dataquest_school'] = df['program_name'].apply(_is_dataquest_school)
    return df


@st.cache_data
def _load_assessments_endline_2025_raw():
    """Load frozen 2025 endline assessment data from parquet file."""
    path = _get_parquet_path("2025_assessment_endline.parquet")
    return pd.read_parquet(path)


@st.cache_data(ttl=3600)
def _load_sessions_2026_raw():
    """Load 2026 session data from PostgreSQL (updated nightly by nightly_sync_2026).
    Returns DataFrame with school_type and mentor columns added."""
    from database_utils import get_database_engine, get_school_type, get_mentor
    engine = get_database_engine()
    df = pd.read_sql(
        "SELECT * FROM sessions_2026 ORDER BY session_started_at DESC",
        engine
    )
    df['school_type'] = df['program_name'].apply(get_school_type)
    df['mentor'] = df['program_name'].apply(get_mentor)
    return df


@st.cache_data(ttl=3600)
def _load_assessments_2026_raw():
    """Load 2026 baseline assessment data from PostgreSQL (updated nightly)."""
    from database_utils import get_database_engine
    engine = get_database_engine()
    return pd.read_sql("SELECT * FROM assessments_2026 ORDER BY response_date DESC", engine)


@st.cache_data(ttl=3600)
def _load_mentor_visits_2026_raw():
    """Load 2026 mentor visit data from PostgreSQL (updated nightly)."""
    from database_utils import get_database_engine
    engine = get_database_engine()
    df = pd.read_sql("SELECT * FROM mentor_visits_2026 ORDER BY response_start_at DESC", engine)
    for col in ['response_start_at', 'response_end_at']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    df['Response Date'] = df['response_start_at']
    return df


def load_sessions_2025():
    return mask_dataframe(_load_sessions_2025_raw(), dataset_key="sessions_2025")


def load_assessments_endline_2025():
    return mask_dataframe(_load_assessments_endline_2025_raw(), dataset_key="assessments_endline_2025")


def load_sessions_2026():
    return mask_dataframe(_load_sessions_2026_raw(), dataset_key="sessions_2026")


_SESSIONS_2026_ANALYSIS_COLUMNS = (
    "session_id",
    "session_started_at",
    "session_duration",
    "attended_percentage",
    "user_name",
    "program_name",
    "participant_id",
    "participant_name",
    "class_name",
)


@st.cache_data(ttl=3600)
def _load_sessions_2026_analysis_raw():
    """Load only columns needed by sessions analysis pages to reduce memory use."""
    from database_utils import get_database_engine, get_school_type, get_mentor
    engine = get_database_engine()
    selected_columns = ", ".join(_SESSIONS_2026_ANALYSIS_COLUMNS)
    query = f"SELECT {selected_columns} FROM sessions_2026 ORDER BY session_started_at DESC"
    analysis_dataframe = pd.read_sql(query, engine)
    analysis_dataframe["school_type"] = analysis_dataframe["program_name"].apply(get_school_type)
    analysis_dataframe["mentor"] = analysis_dataframe["program_name"].apply(get_mentor)
    return analysis_dataframe


def load_sessions_2026_analysis():
    return mask_dataframe(_load_sessions_2026_analysis_raw(), dataset_key="sessions_2026")


def load_assessments_2026():
    return mask_dataframe(_load_assessments_2026_raw(), dataset_key="assessments_2026")


def load_mentor_visits_2026():
    return mask_dataframe(_load_mentor_visits_2026_raw(), dataset_key="mentor_visits_2026")
