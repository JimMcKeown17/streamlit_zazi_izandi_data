# data_processor.py

import pandas as pd
from datetime import datetime as dt
from typing import Tuple, Dict
from grouping_logic import assign_groups_by_cohort


class EGRADataProcessor:
    def __init__(self):
        # Define dictionaries as class attributes
        self.letters_dict = {
    1: 'l',  2: 'a',  3: 'm',  4: 'E',  5: 'p',  6: 'n',  7: 'L',  8: 's',  9: 'o', 10: 'e',
    11: 'Y', 12: 'i', 13: 'K', 14: 'N', 15: 'd', 16: 'H', 17: 'f', 18: 'U', 19: 'h', 20: 'v',
    21: 'F', 22: 'y', 23: 'C', 24: 'I', 25: 'T', 26: 'k', 27: 'D', 28: 'Z', 29: 'f', 30: 'd',
    31: 't', 32: 'z', 33: 'O', 34: 'J', 35: 'P', 36: 'r', 37: 'c', 38: 'W', 39: 'p', 40: 'o',
    41: 'w', 42: 'A', 43: 'E', 44: 'x', 45: 'Q', 46: 'I', 47: 'g', 48: 'O', 49: 'U', 50: 'z',
    51: 'X', 52: 'r', 53: 'V', 54: 'B', 55: 'j', 56: 'b', 57: 'q', 58: 'u', 59: 'R', 60: 'G'
}
        self.nonwords_dict = {
    1: 'ba',  2: 'om',  3: 'pe',  4: 'lu',  5: 'ma',  6: 'wu',  7: 'yi',  8: 'ko',  9: 'ta', 10: 'ze',
    11: 'uzi', 12: 'ida', 13: 'bom', 14: 'ebe', 15: 'uya', 16: 'ndu', 17: 'lim', 18: 'nti', 19: 'kwe', 20: 'utu',
    21: 'sido', 22: 'husi', 23: 'ikho', 24: 'bule', 25: 'sani', 26: 'pelu', 27: 'tuma', 28: 'cuse', 29: 'dipo', 30: 'wavo',
    31: 'umido', 32: 'evatu', 33: 'lipadi', 34: 'nosan', 35: 'ujala', 36: 'uweba', 37: 'iloke', 38: 'ngotu', 39: 'ezimu', 40: 'ndile',
    41: 'isobu', 42: 'ulani', 43: 'epoba', 44: 'izonu', 45: 'elati', 46: 'mbonu', 47: 'kwina', 48: 'ngabi', 49: 'ufano', 50: 'emoni'
}
        self.words_dict = {
    1: 'ewe',   2: 'iti',   3: 'lala',   4: 'bona',   5: 'vuka',   6: 'funa',   7: 'wona',   8: 'yena',   9: 'cela',  10: 'waya',
    11: 'kuba', 12: 'suka', 13: 'hayi',  14: 'luma',  15: 'sela',  16: 'jika',  17: 'waza',  18: 'cula',  19: 'zisa',  20: 'wema',
    21: 'umama',22: 'utata',23: 'usisi', 24: 'usana', 25: 'ifama', 26: 'imoto', 27: 'icawa', 28: 'ubisi', 29: 'usuku', 30: 'udade',
    31: 'ikati',32: 'ukuba',33: 'ibali', 34: 'imali', 35: 'ihagu', 36: 'ubusi', 37: 'sikolo',38: 'lilela',39: 'wabona',40: 'nomama',
    41: 'kudala',42: 'wafika',43: 'umfo', 44: 'emva',  45: 'zathi', 46: 'njani', 47: 'ibhola',48: 'kakhulu',49: 'intombi',50: 'phambili'
}

    def load_data(self, children_file: str, ta_file: str, cutoff_date: str = '2025-01-22') -> pd.DataFrame:
        """Load and merge EGRA data from children and TA files."""
        children_df = pd.read_csv(children_file, parse_dates=['date'], dtype={
        "column_name_337": str,
        "column_name_392": int,
    }, low_memory=False)
        ta_df = pd.read_csv(ta_file)

        # Filter by date
        cutoff = pd.Timestamp(cutoff_date)
        children_df = children_df[children_df['date'] >= cutoff]

        # Merge dataframes
        return children_df.merge(ta_df, left_on='PARENT_KEY', right_on='KEY', how='left')

    def clean_special_cases(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fix special cases."""
        df = df.copy()

        # Fix class for 'Aphelele Nkomo'
        df.loc[df['username'] == 'Aphelele Nkomo', 'class'] = '1A'

        return df

    def clean_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean TA and school names."""
        df = df.copy()

        # Clean name_ta_rep
        df['name_ta_rep'] = (
            df['name_ta_rep']
            .astype(str)
            .str.strip()
            .str.title()
            .str.replace(r'[^\x00-\x7F]+', '', regex=True)
            .str.replace(r'\s+', ' ', regex=True)
            .str.strip()
        )

        # Special cases for name_ta_rep
        name_mappings = {
            'Ntombizanele Jim Kwanoxolo Primary School': 'Ntombizanele Jim',
            'Khanyisa Kapela': 'Kanyisa Kapela'
        }
        for old_name, new_name in name_mappings.items():
            df.loc[df['name_ta_rep'] == old_name, 'name_ta_rep'] = new_name

        # Clean school_rep
        df['school_rep'] = (
            df['school_rep']
            .astype(str)
            .str.strip()
            .str.title()
            .str.replace(r'[^\x00-\x7F]+', '', regex=True)
        )

        # Filter out specific schools
        excluded_schools = ['Masinyusane', 'Masi', 'Atest', 'Rc', 'RC'
                            'Tckvp', "Isaac Booi", "Ee", "Ppp", "Agap", "Ghnn"]
        df = df[~df['school_rep'].isin(excluded_schools)]

        mask = df['school_rep'].isin([
            'Sume Center',
            'Ilitha Lethu Day Care',
            'Njongozabantu Day Care',
            'Greenapple'
        ])
        df.loc[mask, 'username'] = 'ecd_assessments'

        return df

    def clean_school_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean school names by removing common suffixes."""
        df = df.copy()
        df['school_rep_orig'] = df['school_rep']
        df['school_rep'] = df['school_rep'].str.lower().str.title()

        def clean_name(name: str) -> str:
            suffixes = [" Primary School","primary school","Primary school", " Primary", " P.S.", "Public", " PS", "Public School", "pre school", "preschool", "pre-school", "Day care", "Daycare"]
            for suffix in suffixes:
                if name.endswith(suffix):
                    name = name.replace(suffix, "")
            return name.strip()

        df['school_rep'] = df['school_rep'].apply(clean_name)
        df.loc[df['school_rep'] == 'K. K Ncwana', 'school_rep'] = 'Kk Ncwana'
        df.loc[df['school_rep'] == 'K.K Ncwana', 'school_rep'] = 'Kk Ncwana'
        df.loc[df['school_rep'] == 'K.K. Ncwana', 'school_rep'] = 'Kk Ncwana'
        df.loc[df['school_rep'] == 'Kk Ncwane', 'school_rep'] = 'Kk Ncwana'
        df.loc[df['school_rep'] == 'Green-Apple', 'school_rep'] = 'Green Apple'
        df.loc[df['school_rep'] == 'GreenApple', 'school_rep'] = 'Green Apple'
        df.loc[df['school_rep'] == 'Kwa-Noxolo', 'school_rep'] = 'KwaNoxolo'
        df.loc[df['school_rep'] == 'Keyser Ngxwana', 'school_rep'] = 'Kayser Ngxwana'
        df.loc[df['school_rep'] == 'Keyser Ngxwane', 'school_rep'] = 'Kayser Ngxwana'
        df.loc[df['school_rep'] == 'Bj Mnyanda Ps', 'school_rep'] = 'Bj Mnyanda'
        df.loc[df['school_rep'] == 'Bj Mnyandaw', 'school_rep'] = 'Bj Mnyanda'
        df.loc[df['school_rep'] == 'Bj Mnyandq', 'school_rep'] = 'Bj Mnyanda'
        df.loc[df['school_rep'] == 'Emfundweni Primary School.', 'school_rep'] = 'Emfundweni'
        df.loc[df['school_rep'] == 'Emzoncane', 'school_rep'] = 'Emzomncane'
        df.loc[df['school_rep'] == 'Gertrude', 'school_rep'] = 'Gertrude Shope'
        df.loc[df['school_rep'] == 'Melisizwe P School', 'school_rep'] = 'Melisizwe'
        df.loc[df['school_rep'] == 'Ben Nyati', 'school_rep'] = 'Ben Nyathi'
        df.loc[df['school_rep'] == 'Enkwekwezini', 'school_rep'] = 'Enkwenkwezini'
        df.loc[df['school_rep'] == 'Siyaphambhili', 'school_rep'] = 'Siyaphambili'
        df.loc[df['school_rep'] == 'Spencer', 'school_rep'] = 'Spencer Mabija'
        df.loc[df['school_rep'] == 'Steven Mazungula', 'school_rep'] = 'Stephen Mazungula'

        df.loc[df['school_rep'] == 'St Mary magaldene edu day care', 'school_rep'] = 'St Mary magaldene day care'

        return df

    def remove_duplicates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Remove duplicate assessments for the same child."""
        df_sorted = df.sort_values(
            ["school_rep", "name_learner_full", "date"],
            ascending=[True, True, False]
        ).reset_index(drop=True)

        df_no_dupes = df_sorted.drop_duplicates(
            subset=["school_rep", "name_learner_full"],
            keep="first"
        )
        removed_dupes = df_sorted[
            df_sorted.duplicated(subset=["school_rep", "name_learner_full"], keep="first")
        ]
        return df_no_dupes, removed_dupes

    def clean_class_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean class labels."""
        df = df.copy()
        df["class_orig"] = df["class"]
        df["class"] = df["class"].str.replace("[1R]", "", regex=True).str.strip()
        df["class"] = df["grade_label"] + df["class"]
        return df

    def process_assessment_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process letters, nonwords, and words data."""
        df = self.process_either_a1_a2_letters(df)
        df = self.process_either_a1_a2_nonwords(df)
        df = self.process_either_a1_a2_words(df)
        return df

    def process_either_a1_a2_letters(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process letter assessment data."""
        df = df.copy()  # Create a copy to avoid modifying the original
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
            for i, letter in self.letters_dict.items():  # Changed to self.letters_dict
                old_col = f"{prefix}_{i}"
                new_col = f"letters_{letter}_{i}"

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

    def process_either_a1_a2_nonwords(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process nonwords assessment data."""
        df = df.copy()
        for idx, row in df.iterrows():
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

            for i, syllable in self.nonwords_dict.items():  # Changed to self.nonwords_dict
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

    def process_either_a1_a2_words(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process words assessment data."""
        df = df.copy()
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

            for i, w_syllable in self.words_dict.items():  # Changed to self.words_dict
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

    def process_usernames(self, df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        # Filter 'df_primary' for all usernames containing 'zz'
        df_primary = df[df['username'].str.contains('zz', na=False)]

        # Filter 'df_ecd' for the exact match 'ecd_assessments'
        df_ecd = df[df['username'] == 'ecd_assessments']

        return df_primary, df_ecd

    def exclude(self, df: pd.DataFrame) -> pd.DataFrame:
        # Filter separately for each username
        # df = df[df['name_ta_rep'] != 'Sivenathi Ntshontsho']
        df = df[df['name_ta_rep'] != 'Bongiwe Mbusi']

        df.loc[
            (df['name_ta_rep'] == 'Sivenathi Ntshontsho'),
            ['words_correct_a1', 'nonwords_correct_a1']
        ] = 0

        return df

def process_egra_data(
        children_file: str,
        ta_file: str,
        output_dir: str = '.',
        cutoff_date: str = '2025-01-22'
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Main function to process EGRA data."""
    processor = EGRADataProcessor()

    # Load and process data
    df = processor.load_data(children_file, ta_file, cutoff_date)
    df = processor.clean_special_cases(df)
    df = processor.clean_names(df)
    df = processor.clean_school_names(df)
    df, _ = processor.remove_duplicates(df)
    df = processor.clean_class_labels(df)
    df = processor.process_assessment_data(df)
    df = processor.exclude(df)
    # df_ecd = pd.DataFrame()
    df, df_ecd = processor.process_usernames(df)

    df = assign_groups_by_cohort(df, group_size=7)

    return df, df_ecd


if __name__ == "__main__":
    # Example usage
    df = process_egra_data(
        children_file="data/EGRA form-assessment_repeat - June 4.csv",
        ta_file="data/EGRA form - June 4.csv"
    )