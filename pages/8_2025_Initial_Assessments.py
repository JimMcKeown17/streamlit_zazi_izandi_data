import streamlit as st
import pandas as pd

# Streamlit page header
st.set_page_config(page_title="TA Assessments", layout="wide")
st.title("2025 Initial Assessments")
st.subheader("Utilizing SurveyCTO's EGRA Plugin")

# Read and process data
children_df = pd.read_csv("data/EGRA form-assessment_repeat (1).csv", parse_dates=['date'])
ta_df = pd.read_csv("data/EGRA form.csv")

# Define dictionaries (letters_dict, nonwords_dict, words_dict remain the same)
letters_dict = {
    # ... (keep existing dictionary)
}

# Filter by cutoff date
cutoff_date = pd.Timestamp('2025-01-22')
children_df = children_df[children_df['date'] >= cutoff_date]

# Merge dataframes
df = children_df.merge(ta_df, left_on='PARENT_KEY', right_on='KEY', how='left')

# Clean data columns
df['name_ta_rep'] = df['name_ta_rep'].str.strip().str.title()
df['name_ta_rep'] = df['name_ta_rep'].str.replace(r'[^\x00-\x7F]+', '', regex=True)
df['name_ta_rep'] = df['name_ta_rep'].str.replace(r'\s+', ' ', regex=True).str.strip()

df['school_rep'] = df['school_rep'].str.strip().str.title()
df['school_rep'] = df['school_rep'].str.replace(r'[^\x00-\x7F]+', '', regex=True)

# TA Assessments Summary
st.header("TA Assessments Summary")
ta_assessments = df.groupby(['school_rep', 'name_ta_rep', 'grade_label'])['name_first_learner'].count().reset_index()
ta_assessments.columns = ['School', 'TA', 'Grade', 'Count']
st.dataframe(ta_assessments, use_container_width=True)

# Grade Summary
st.header("Grade Summary")
grade_summary = df.groupby(['grade_label']).agg(
    Number_Assessed=('name_first_learner', 'count'),
    Average_Letters_Correct=('letters_correct_a1', 'mean'),
    Letter_Score=('letters_score_a1', 'mean'),
    Count_Above_40=('letters_correct_a1', lambda x: (x >= 40).sum())
).reset_index()
grade_summary['Average_Letters_Correct'] = grade_summary['Average_Letters_Correct'].round(1)
grade_summary['Letter_Score'] = grade_summary['Letter_Score'].round(1)
st.dataframe(grade_summary, use_container_width=True)

# School Summary
st.header("School Summary")
school_summary = df.groupby(['school_rep', 'grade_label']).agg(
    Number_Assessed=('name_first_learner', 'count'),
    Average_Letters_Correct=('letters_correct_a1', 'mean'),
    Letter_Score=('letters_score_a1', 'mean'),
    Count_Above_40=('letters_correct_a1', lambda x: (x >= 40).sum())
).reset_index()
school_summary['Average_Letters_Correct'] = school_summary['Average_Letters_Correct'].round(1)
school_summary['Letter_Score'] = school_summary['Letter_Score'].round(1)
school_summary = school_summary.sort_values(by='Average_Letters_Correct', ascending=False)
st.dataframe(school_summary, use_container_width=True)

# Grade 1 Non-Words Summary
st.header("Grade 1 Non-Words Summary")
g1 = df[df['grade_label'] == 'Grade 1']
school_non_words_summary = g1.groupby(['school_rep', 'class']).agg(
    Number_Assessed=('name_first_learner', 'count'),
    Average_NonWords_Correct=('nonwords_correct_a1', 'mean')
).reset_index()
school_non_words_summary['Average_NonWords_Correct'] = school_non_words_summary['Average_NonWords_Correct'].round(1)
school_non_words_summary = school_non_words_summary.sort_values(by='Average_NonWords_Correct', ascending=False)
st.dataframe(school_non_words_summary, use_container_width=True)

# Grade 1 Words Summary
st.header("Grade 1 Words Summary")
school_words_summary = g1.groupby(['school_rep', 'class']).agg(
    Number_Assessed=('name_first_learner', 'count'),
    Average_Words_Correct=('words_correct_a1', 'mean')
).reset_index()
school_words_summary['Average_Words_Correct'] = school_words_summary['Average_Words_Correct'].round(1)
school_words_summary = school_words_summary.sort_values(by='Average_Words_Correct', ascending=False)
st.dataframe(school_words_summary, use_container_width=True)