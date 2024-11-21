import streamlit as st
import pandas as pd
import statsmodels.api as sm

def process_zz_data_midline(baseline, midline, sessions):

    # Rename a couple columns
    baseline.rename(columns={'Baseline\nAssessment Score': 'EGRA Baseline'}, inplace=True)
    midline.rename(columns={'Midline Assessment Score': 'EGRA Midline'}, inplace=True)

    # Create letter columns

    letter_cols = ['a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p', 's', 'h', 'z', 'n', 'd', 'y', 'f', 'w', 'v', 'x',
                   'g', 't', 'q', 'r', 'c', 'j']

    # Calculate Columns for Letters Learned
    mask = baseline['Captured'] == True
    baseline.loc[mask, 'Letters Known'] = baseline.loc[mask, letter_cols].notna().sum(axis=1)

    mask = midline['Captured'] == True
    midline.loc[mask, 'Letters Known'] = midline.loc[mask, letter_cols].notna().sum(axis=1)

    # Create cohorts for Baseline & Midline

    baseline['List of Letters Known'] = baseline[letter_cols].apply(
        lambda row: [letter for letter, value in row.items() if pd.notna(value)], axis=1)
    midline['List of Letters Known'] = midline[letter_cols].apply(
        lambda row: [letter for letter, value in row.items() if pd.notna(value)], axis=1)

    cohort_mask = baseline['Letters Known'].notna()

    for index, row in baseline[cohort_mask].iterrows():
        if row['Letters Known'] < 6:
            baseline.at[index, 'Letter Cohort'] = '0-5'
        elif row['Letters Known'] < 13:
            baseline.at[index, 'Letter Cohort'] = '6-12'
        elif row['Letters Known'] < 19:
            baseline.at[index, 'Letter Cohort'] = '13-18'
        else:
            baseline.at[index, 'Letter Cohort'] = '19+'

    cohort_mask = midline['Letters Known'].notna()

    for index, row in midline[cohort_mask].iterrows():
        if row['Letters Known'] < 6:
            midline.at[index, 'Letter Cohort'] = '0-5'
        elif row['Letters Known'] < 13:
            midline.at[index, 'Letter Cohort'] = '6-12'
        elif row['Letters Known'] < 19:
            midline.at[index, 'Letter Cohort'] = '13-18'
        else:
            midline.at[index, 'Letter Cohort'] = '19+'

    # Merge Dataframes (baseline, midline, & sessions)

    midline = pd.merge(midline, baseline[['Mcode', 'Baseline Letters Known', 'EGRA Baseline', 'Letter Cohort']],
                       on="Mcode", suffixes=('', '_baseline'))

    midline = pd.merge(midline, sessions[['Mcode', 'Total Sessions']],
                       on="Mcode", suffixes=('', '_sessions'))

    # Calculate 'Letters Learned'
    mask = midline['Captured'] == True
    midline.loc[mask, 'Letters Learned'] = midline.loc[mask, 'Midline Letters Known'] - midline.loc[
        mask, 'Baseline Letters Known']

    # Calculate 'Egra Improvement Agg'
    mask_egra = midline['EGRA Midline'].notna()
    midline.loc[mask_egra, 'Egra Improvement Agg'] = midline.loc[mask_egra, 'EGRA Midline'] - midline.loc[
        mask_egra, 'EGRA Baseline']

    # Calculate 'Egra Improvement' as a percentage. Note I'm setting initial zeroes to 1 to avoid dividing by zero, even though this makes the results a bit worse.
    midline['Adjusted EGRA Baseline'] = midline['EGRA Baseline'].replace(0, 1)
    midline.loc[mask_egra, 'Egra Improvement Pct'] = ((midline.loc[mask_egra, 'EGRA Midline'] - midline.loc[
        mask_egra, 'Adjusted EGRA Baseline']) / midline.loc[mask_egra, 'Adjusted EGRA Baseline']) * 100

    midline['Grade'] = midline['Grade'].astype(str).str.strip()

    midline['Midline Letters Known'] = midline['Letters Known']

    return midline, baseline

def process_zz_data_endline(endline):
    # Rename a couple columns

    endline.rename(columns={'Endline Assessment Score': 'EGRA Endline'}, inplace=True)
    endline.rename(columns={'Midline Assessment Score': 'EGRA Midline'}, inplace=True)
    endline.rename(columns={'Midline Assessment Score - Sept': 'EGRA Midline Sept'}, inplace=True)
    endline.rename(columns={'Baseline Assessment Score': 'EGRA Baseline'}, inplace=True)

    columns_to_convert = ['EGRA Baseline', 'EGRA Midline', 'EGRA Midline Sept', 'EGRA Endline']

    for col in columns_to_convert:
        endline[col] = pd.to_numeric(endline[col], errors='coerce')

    # Create letter columns

    letter_cols = ['a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p', 's', 'h', 'z', 'n', 'd', 'y', 'f', 'w', 'v', 'x',
                   'g', 't', 'q', 'r', 'c', 'j']

    # Calculate Columns for Letters Learned
    mask = endline['Captured'] == True
    endline.loc[mask, 'Letters Known'] = endline.loc[mask, letter_cols].notna().sum(axis=1)

    # Calculate 'Egra Improvement Agg'

    endline_mask_egra = endline['EGRA Endline'].notna()
    endline.loc[endline_mask_egra, 'Egra Improvement Agg'] = endline.loc[endline_mask_egra, 'EGRA Endline'] - endline.loc[
        endline_mask_egra, 'EGRA Baseline']

    endline['Adjusted EGRA Baseline'] = endline['EGRA Baseline'].replace(0, 1)
    endline.loc[endline_mask_egra, 'Egra Improvement Pct'] = ((endline.loc[endline_mask_egra, 'EGRA Endline'] - endline.loc[
        endline_mask_egra, 'Adjusted EGRA Baseline']) / endline.loc[endline_mask_egra, 'Adjusted EGRA Baseline']) * 100

    endline['Grade'] = endline['Grade'].astype(str).str.strip()

    endline['Midline Letters Known'] = endline['Letters Known']

    return endline

def process_zz_data_endline_new_schools(endline):
    # Rename a couple columns

    endline.rename(columns={'Endline Assessment Score': 'EGRA Endline'}, inplace=True)
    endline.rename(columns={'Baseline Assessment Score': 'EGRA Baseline'}, inplace=True)

    columns_to_convert = ['EGRA Baseline', 'EGRA Endline']

    for col in columns_to_convert:
        endline[col] = pd.to_numeric(endline[col], errors='coerce')

    # Create letter columns

    letter_cols = ['a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p', 's', 'h', 'z', 'n', 'd', 'y', 'f', 'w', 'v', 'x',
                   'g', 't', 'q', 'r', 'c', 'j']

    # Calculate Columns for Letters Learned
    mask = endline['Captured'] == True
    endline.loc[mask, 'Letters Known'] = endline.loc[mask, letter_cols].notna().sum(axis=1)

    # Calculate 'Egra Improvement Agg'

    endline_mask_egra = endline['EGRA Endline'].notna()
    endline.loc[endline_mask_egra, 'Egra Improvement Agg'] = endline.loc[endline_mask_egra, 'EGRA Endline'] - endline.loc[
        endline_mask_egra, 'EGRA Baseline']

    endline['Adjusted EGRA Baseline'] = endline['EGRA Baseline'].replace(0, 1)
    endline.loc[endline_mask_egra, 'Egra Improvement Pct'] = ((endline.loc[endline_mask_egra, 'EGRA Endline'] - endline.loc[
        endline_mask_egra, 'Adjusted EGRA Baseline']) / endline.loc[endline_mask_egra, 'Adjusted EGRA Baseline']) * 100

    endline['Grade'] = endline['Grade'].astype(str).str.strip()

    endline['Endline Letters Known'] = endline['Letters Known']

    return endline
def grade1_df(df):
    grade1 = df[df['Grade'] == 'Grade 1']
    return grade1


def gradeR_df(df):
    gradeR = df[df['Grade'] == 'Grade R']
    return gradeR
