import pandas as pd
from grouping_logic import assign_groups_by_cohort
from create_letter_tracker import create_letter_tracker
from datetime import datetime as dt

children_df = pd.read_csv("EGRA form-assessment_repeat - Jan 29.csv", parse_dates=['date'])
ta_df = pd.read_csv("EGRA form - Jan 29.csv")

letters_dict = {
    1: 'l',  2: 'a',  3: 'm',  4: 'E',  5: 'p',  6: 'n',  7: 'L',  8: 's',  9: 'o', 10: 'e',
    11: 'Y', 12: 'i', 13: 'K', 14: 'N', 15: 'd', 16: 'H', 17: 'f', 18: 'U', 19: 'h', 20: 'v',
    21: 'F', 22: 'y', 23: 'C', 24: 'I', 25: 'T', 26: 'k', 27: 'D', 28: 'Z', 29: 'f', 30: 'd',
    31: 't', 32: 'z', 33: 'O', 34: 'J', 35: 'P', 36: 'r', 37: 'c', 38: 'W', 39: 'p', 40: 'o',
    41: 'w', 42: 'A', 43: 'E', 44: 'x', 45: 'Q', 46: 'I', 47: 'g', 48: 'O', 49: 'U', 50: 'z',
    51: 'X', 52: 'r', 53: 'V', 54: 'B', 55: 'j', 56: 'b', 57: 'q', 58: 'u', 59: 'R', 60: 'G'
}
nonwords_dict = {
    1: 'ba',  2: 'om',  3: 'pe',  4: 'lu',  5: 'ma',  6: 'wu',  7: 'yi',  8: 'ko',  9: 'ta', 10: 'ze',
    11: 'uzi', 12: 'ida', 13: 'bom', 14: 'ebe', 15: 'uya', 16: 'ndu', 17: 'lim', 18: 'nti', 19: 'kwe', 20: 'utu',
    21: 'sido', 22: 'husi', 23: 'ikho', 24: 'bule', 25: 'sani', 26: 'pelu', 27: 'tuma', 28: 'cuse', 29: 'dipo', 30: 'wavo',
    31: 'umido', 32: 'evatu', 33: 'lipadi', 34: 'nosan', 35: 'ujala', 36: 'uweba', 37: 'iloke', 38: 'ngotu', 39: 'ezimu', 40: 'ndile',
    41: 'isobu', 42: 'ulani', 43: 'epoba', 44: 'izonu', 45: 'elati', 46: 'mbonu', 47: 'kwina', 48: 'ngabi', 49: 'ufano', 50: 'emoni'
}
words_dict = {
    1: 'ewe',   2: 'iti',   3: 'lala',   4: 'bona',   5: 'vuka',   6: 'funa',   7: 'wona',   8: 'yena',   9: 'cela',  10: 'waya',
    11: 'kuba', 12: 'suka', 13: 'hayi',  14: 'luma',  15: 'sela',  16: 'jika',  17: 'waza',  18: 'cula',  19: 'zisa',  20: 'wema',
    21: 'umama',22: 'utata',23: 'usisi', 24: 'usana', 25: 'ifama', 26: 'imoto', 27: 'icawa', 28: 'ubisi', 29: 'usuku', 30: 'udade',
    31: 'ikati',32: 'ukuba',33: 'ibali', 34: 'imali', 35: 'ihagu', 36: 'ubusi', 37: 'sikolo',38: 'lilela',39: 'wabona',40: 'nomama',
    41: 'kudala',42: 'wafika',43: 'umfo', 44: 'emva',  45: 'zathi', 46: 'njani', 47: 'ibhola',48: 'kakhulu',49: 'intombi',50: 'phambili'
}

# Filter children_df by date
cutoff_date = pd.Timestamp('2025-01-22')
children_df = children_df[children_df['date'] >= cutoff_date]

# Merge
df = children_df.merge(ta_df, left_on='PARENT_KEY', right_on='KEY', how='left')

# Clean name_ta_rep, school_rep
df['name_ta_rep'] = (
    df['name_ta_rep']
    .astype(str)
    .str.strip()
    .str.title()
    .str.replace(r'[^\x00-\x7F]+', '', regex=True)
    .str.replace(r'\s+', ' ', regex=True)
    .str.strip()
)
df.loc[df['name_ta_rep'] == 'Ntombizanele Jim Kwanoxolo Primary School', 'name_ta_rep'] = 'Ntombizanele Jim'
df.loc[df['name_ta_rep'] == 'Khanyisa Kapela', 'name_ta_rep'] = 'Kanyisa Kapela'


df['school_rep'] = (
    df['school_rep']
    .astype(str)
    .str.strip()
    .str.title()
    .str.replace(r'[^\x00-\x7F]+', '', regex=True)
)

df = df[~df['school_rep'].isin(['Masinyusane', 'Masi', 'Atest', 'Sume Center', 'Rc', 'Tckvp', 'Ilitha Lethu Day Care', "Isaac Booi"])]

def clean_school_name(name):
    # Remove common suffixes
    suffixes = [" Primary School", " Primary", " P.S.", " PS", "Public School"]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name.replace(suffix, "")
    # Remove extra spaces and standardize
    return name.strip()

df['school_rep_orig'] = df['school_rep']
df['school_rep'] = df['school_rep'].apply(clean_school_name)
df.loc[df['school_rep'] == 'K. K Ncwana', 'school_rep'] = 'Kk Ncwana'

# REMOVE DUPLICATE ASSESSMENTS FOR SAME CHILD
def remove_duplicates(df):
    df_sorted = df.sort_values(["school_rep", "name_learner_full", "date"], ascending=[True, True, False]).reset_index(drop=True)
    df_no_dupes = df_sorted.drop_duplicates(subset=["school_rep", "name_learner_full"], keep="first")
    removed_dupes_df = df_sorted[df_sorted.duplicated(subset=["school_rep", "name_learner_full"], keep="first")]
    return df_no_dupes, removed_dupes_df

df, removed_dupes_df = remove_duplicates(df)

# Strip away 1 and R from class since the same TA enters C on one day and 1C on another
df["class_orig"] = df["class"]
df["class"] = df["class"].str.replace("[1R]", "", regex=True).str.strip()
df["class"] = df["grade_label"] + df["class"]
# USING CORRECT REASSESSMENT VALUE
# pick either a1 or a2 based on whether score_a2 is blank

def process_either_a1_a2_letters(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each row, if 'letters_score_a2' is blank => use columns from letters_a1 + letter_attempted_a1,
    else use letters_a2 + letter_attempted_a2.

    Then create new columns named 'letters_{letter}_{i}' with:
       - i > last_attempted => NaN
       - 0 => 'X'
       - 1 => '0'
       - NaN => NaN
    """
    for idx, row in df.iterrows():
        # Decide if we use a1 or a2:
        if pd.isna(row.get('letters_score_a2', None)):
            prefix = 'letters_a1'
            attempted_col = 'letter_attempted_a1'
        else:
            prefix = 'letters_a2'
            attempted_col = 'letter_attempted_a2'

        last_idx = row.get(attempted_col, 0)
        if pd.isna(last_idx):
            last_idx = 0
        else:
            last_idx = int(last_idx)

        # For each letter index
        for i, letter in letters_dict.items():
            old_col = f"{prefix}_{i}"  # e.g. letters_a1_1 or letters_a2_1
            new_col = f"letters_{letter}_{i}"

            # If that old column is missing entirely, just set new col to NaN
            if old_col not in df.columns:
                df.at[idx, new_col] = pd.NA
                continue

            # Convert to numeric
            val = pd.to_numeric(row[old_col], errors='coerce')

            # If i > last_idx => NaN
            if i > last_idx:
                df.at[idx, new_col] = pd.NA
            else:
                # 0->'X', 1->'0', else NaN
                if pd.isna(val):
                    df.at[idx, new_col] = pd.NA
                elif val == 0:
                    df.at[idx, new_col] = 'X'
                elif val == 1:
                    df.at[idx, new_col] = '0'
                else:
                    df.at[idx, new_col] = pd.NA
    return df

def process_either_a1_a2_nonwords(df: pd.DataFrame) -> pd.DataFrame:
    """
    Similar logic for nonwords:
    If 'nonwords_score_a2' is blank => use nonwords_a1 + nonwords_attempted_a1,
    else use nonwords_a2 + nonwords_attempted_a2.
    """
    for idx, row in df.iterrows():
        # Decide
        if pd.isna(row.get('nonwords_score_a2', None)):
            prefix = 'nonwords_a1'
            attempted_col = 'nonwords_attempted_a1'
        else:
            prefix = 'nonwords_a2'
            attempted_col = 'nonwords_attempted_a2'

        last_idx = row.get(attempted_col, 0)
        if pd.isna(last_idx):
            last_idx = 0
        else:
            last_idx = int(last_idx)

        for i, syllable in nonwords_dict.items():
            old_col = f"{prefix}_{i}"
            new_col = f"nonwords_{syllable}_{i}"

            if old_col not in df.columns:
                df.at[idx, new_col] = pd.NA
                continue

            val = pd.to_numeric(row[old_col], errors='coerce')

            if i > last_idx:
                df.at[idx, new_col] = pd.NA
            else:
                if pd.isna(val):
                    df.at[idx, new_col] = pd.NA
                elif val == 0:
                    df.at[idx, new_col] = 'X'
                elif val == 1:
                    df.at[idx, new_col] = '0'
                else:
                    df.at[idx, new_col] = pd.NA
    return df

def process_either_a1_a2_words(df: pd.DataFrame) -> pd.DataFrame:
    """
    Same approach for words:
    If 'words_score_a2' is blank => words_a1 + words_attempted_a1,
    else words_a2 + words_attempted_a2
    """
    for idx, row in df.iterrows():
        if pd.isna(row.get('words_score_a2', None)):
            prefix = 'words_a1'
            attempted_col = 'words_attempted_a1'
        else:
            prefix = 'words_a2'
            attempted_col = 'words_attempted_a2'

        last_idx = row.get(attempted_col, 0)
        if pd.isna(last_idx):
            last_idx = 0
        else:
            last_idx = int(last_idx)

        for i, w_syllable in words_dict.items():
            old_col = f"{prefix}_{i}"
            new_col = f"words_{w_syllable}_{i}"

            if old_col not in df.columns:
                df.at[idx, new_col] = pd.NA
                continue

            val = pd.to_numeric(row[old_col], errors='coerce')

            if i > last_idx:
                df.at[idx, new_col] = pd.NA
            else:
                if pd.isna(val):
                    df.at[idx, new_col] = pd.NA
                elif val == 0:
                    df.at[idx, new_col] = 'X'
                elif val == 1:
                    df.at[idx, new_col] = '0'
                else:
                    df.at[idx, new_col] = pd.NA
    return df

# 3) APPLY ROW-BY-ROW LOGIC
df = process_either_a1_a2_letters(df)
df = process_either_a1_a2_nonwords(df)
df = process_either_a1_a2_words(df)

# GROUP LOGIC
df = assign_groups_by_cohort(df, group_size=7)

date = dt.today().strftime('%Y-%m-%d')

df.to_csv(f'merged_data_{date}.csv', index=False)

df_simple = df[['date', 'name_ta_rep', 'school_rep', 'grade', 'class', 'name_first_learner',
                'name_second_learner', 'letters_correct', 'learner_list_concat',
                'learner_list', 'grouping_remainder', 'stage2_join_list', 'group']]
df_simple.to_csv("simple_merged_data.csv", index=False)

# CREATE LETTER TRACKER
letter_tracker_df = create_letter_tracker(df)

# CREATE LETTER TRACKER PDFs
# export_html_per_ta(df)

print("Success")
