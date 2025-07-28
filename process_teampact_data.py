import pandas as pd

def duplicate_columns_without_language(df):
    suffixes = ["isiXhosa", "English", "Afrikaans"]  # match your actual suffixes
    new_cols = {}
    for col in df.columns:
        if any(col.endswith(f" - {lang}") for lang in suffixes):
            base_col = col.rsplit(" - ", 1)[0]
            if base_col not in df.columns:
                new_cols[base_col] = col
    for new_col, original_col in new_cols.items():
        df[new_col] = df[original_col]
    return df

def process_teampact_data(xhosa_df: pd.DataFrame, english_df: pd.DataFrame, afrikaans_df: pd.DataFrame) -> pd.DataFrame:
    """
    Process the TeamPact data
    """
    xhosa_df = duplicate_columns_without_language(xhosa_df)
    english_df = duplicate_columns_without_language(english_df)
    afrikaans_df = duplicate_columns_without_language(afrikaans_df)
    
    xhosa_df['Language'] = 'isiXhosa'
    english_df['Language'] = 'English'
    afrikaans_df['Language'] = 'Afrikaans'
    
    common_cols = [
    'User ID',
    'First Name',
    'Last Name',
    'Email',
    'Class Name',
    'Class ID',
    'Program Name',
    'Language',
    'Gender',
    'Survey Name',
    'Survey ID',
    'Response ID',
    'Collected By',
    'Response Date',
    'Grade ',
    'Class',
    'Learner First Name',
    'Learner Surname ',
    'Learner Gender',
    'Learner EMIS',
    'Total cells correct - EGRA Letters',
    'Total cells incorrect - EGRA Letters',
    'Total cells attempted - EGRA Letters',
    'Total cells not attempted - EGRA Letters',
    'Assessment Complete? - EGRA Letters',
    'Stop rule reached? - EGRA Letters',
    'Timer elapsed? - EGRA Letters',
    'Time elapsed at completion - EGRA Letters']
    
    df_all = pd.concat([
    xhosa_df[common_cols],
    english_df[common_cols],
    afrikaans_df[common_cols]], ignore_index=True)

    df_all.columns = df_all.columns.str.strip()
    
    
    return df_all  