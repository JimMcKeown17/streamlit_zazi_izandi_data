import streamlit as st
import pandas as pd
import plotly.express as px

# Streamlit page header
st.set_page_config(page_title="TA Assessments", layout="wide")
st.title("2025 Initial Assessments")
st.info("Utilizing SurveyCTO's EGRA Plugin. As of Jan 25, 2025, we have 41 TAs starting with assessments. The next 40 will begin once their TLT contracts are signed.")

# Read and process data
children_df = pd.read_csv("data/EGRA form-assessment_repeat (1).csv", parse_dates=['date'])
ta_df = pd.read_csv("data/EGRA form.csv")

def clean_school_name(name):
    # Remove common suffixes
    suffixes = [" Primary School", " Primary", " P.S.", " PS"]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name.replace(suffix, "")
    # Remove extra spaces and standardize
    return name.strip()

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

df = df[df['school_rep'] != 'Masinyusane']
df['school_rep_orig'] = df['school_rep']
df['school_rep'] = df['school_rep'].apply(clean_school_name)
# START OF PAGE

col1, col2, col3 = st.columns(3)

with col1:# Total Assessed
    st.metric("Total Number of Children Assessed", len(df))

with col2:
    # Number of TAs that assessed > 20 kids
    ta_counts = df['name_ta_rep'].value_counts()
    ta_more_than_20 = ta_counts[ta_counts >= 20]
    st.metric("TAs That Assessed More Than 20 Children", f'{len(ta_more_than_20)}/41')

with col3:
    # Number of TAs that submitted anything
    ta_counts = df['name_ta_rep'].value_counts()
    st.metric("TAs That Submitted Results (1 or more children)", f'{len(ta_counts)}/41')

# Assessments Per TA
with st.container():
    ta_counts = df['name_ta_rep'].value_counts().reset_index()
    ta_counts.columns = ['name_ta_rep', 'count']

    fig = px.bar(
        ta_counts,
        x='name_ta_rep',
        y='count',
        title='Counts of TAs',
        labels={'name_ta_rep': 'TA Name', 'count': 'Number of Kids Assessed'},
        color='count',
        text='count'
    )

    fig.update_layout(
        xaxis_title="TA Name",
        yaxis_title="Number of Kids Assessed",
        showlegend=False
    )


    st.plotly_chart(fig, use_container_width=True)

# TA Assessments Summary
with st.container():
    st.header("Assessments Completed Per School & TA")
    ta_assessments = df.groupby(['school_rep', 'name_ta_rep', 'grade_label'])['name_first_learner'].count().reset_index()
    ta_assessments.columns = ['School', 'TA', 'Grade', 'Count']
    st.dataframe(ta_assessments, use_container_width=True)

# Grade Summary
with st.container():
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
with st.container():
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

    fig = px.bar(
        school_summary,
        x="school_rep",
        y="Average_Letters_Correct",
        color="grade_label",
        barmode="group",
        title="Average Letters Correct by School and Grade",
        labels={"school_rep": "School", "Average_Letters_Correct": "Average Letters Correct"},
        color_discrete_sequence=px.colors.qualitative.Set2  # Optional: Use a qualitative color scheme
    )

    fig.update_layout(
        xaxis_title="School",
        yaxis_title="Average Letters Correct",
        legend_title="Grade",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(school_summary, use_container_width=True)

# Grade 1 Non-Words Summary
with st.container():
    st.header("Grade 1 Non-Words Summary")
    g1 = df[df['grade_label'] == 'Grade 1']
    school_non_words_summary = g1.groupby(['school_rep', 'class']).agg(
        Number_Assessed=('name_first_learner', 'count'),
        Average_NonWords_Correct=('nonwords_correct_a1', 'mean')
    ).reset_index()
    school_non_words_summary['Average_NonWords_Correct'] = school_non_words_summary['Average_NonWords_Correct'].round(1)
    school_non_words_summary = school_non_words_summary.sort_values(by='Average_NonWords_Correct', ascending=False)

    fig = px.bar(
        school_non_words_summary,
        x="school_rep",
        y="Average_NonWords_Correct",
        color="class",
        barmode="group",
        title="Average Non-Words Correct by School and Class",
        labels={
            "school_rep": "School",
            "Average_NonWords_Correct": "Average Non-Words Correct",
            "class": "Class"
        },
        color_discrete_sequence=px.colors.qualitative.Set2  # Optional: Use a qualitative color scheme
    )

    # Customize chart layout
    fig.update_layout(
        xaxis_title="School",
        yaxis_title="Average Non-Words Correct",
        legend_title="Class",
    )

    # Display the chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(school_non_words_summary, use_container_width=True)

# Grade 1 Words Summary
with st.container():
    st.header("Grade 1 Words Summary")
    school_words_summary = g1.groupby(['school_rep', 'class']).agg(
        Number_Assessed=('name_first_learner', 'count'),
        Average_Words_Correct=('words_correct_a1', 'mean')
    ).reset_index()
    school_words_summary['Average_Words_Correct'] = school_words_summary['Average_Words_Correct'].round(1)
    school_words_summary = school_words_summary.sort_values(by='Average_Words_Correct', ascending=False)

    fig = px.bar(
        school_words_summary,
        x="school_rep",  # Schools on the x-axis
        y="Average_Words_Correct",  # Values for the y-axis
        color="class",  # Differentiate bars by class
        barmode="group",  # Grouped bars for classes
        title="Average Words Correct by School and Class",
        labels={
            "school_rep": "School",
            "Average_Words_Correct": "Average Words Correct",
            "class": "Class"
        },
        color_discrete_sequence=px.colors.qualitative.Set2  # Optional: Use a qualitative color scheme
    )

    # Customize chart layout
    fig.update_layout(
        xaxis_title="School",
        yaxis_title="Average Words Correct",
        legend_title="Class",
    )

    # Display the chart in Streamlit
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(school_words_summary, use_container_width=True)