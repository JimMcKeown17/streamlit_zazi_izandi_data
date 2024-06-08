import streamlit as st
import pandas as pd
import statsmodels.api as sm

def process_data():
    # Import Data: Baseline, Midline, Sessions
    baseline_path = "Zazi iZandi Children's database (Baseline)7052024.xlsx"
    sheet_name_baseline = "ZZ Childrens Database"
    midline_path = "Zazi iZandi Midline Assessments database (1).xlsx"
    sheet_name_midline = "Childrens database"
    baseline = pd.read_excel(baseline_path, sheet_name=sheet_name_baseline)
    midline = pd.read_excel(midline_path, sheet_name=sheet_name_midline)
    sessions_path = "Zazi iZandi Children's Session Tracker-08052024.xlsx"
    sheet_name_sessions = "ZZ sessions"
    sessions = pd.read_excel(sessions_path, sheet_name=sheet_name_sessions)

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

    # Calculate 'Egra Improvement' as a percentage. Not I'm setting initial zeroes to 1 to avoid dividing by zero, even though this makes the results a bit worse.
    midline['Adjusted EGRA Baseline'] = midline['EGRA Baseline'].replace(0, 1)
    midline.loc[mask_egra, 'Egra Improvement Pct'] = ((midline.loc[mask_egra, 'EGRA Midline'] - midline.loc[
        mask_egra, 'Adjusted EGRA Baseline']) / midline.loc[mask_egra, 'Adjusted EGRA Baseline']) * 100

    midline['Grade'] = midline['Grade'].astype(str).str.strip()

    midline['Midline Letters Known'] = midline['Letters Known']

    return midline, baseline

def grade1(df):
    grade1 = df[df['Grade'] == 'Grade 1']
    return grade1


def gradeR(df):
    gradeR = df[df['Grade'] == 'Grade R']
    return gradeR