import streamlit as st
import pandas as pd
import plotly.express as px
from process_survey_cto_updated import process_egra_data
from create_letter_tracker import create_letter_tracker
import os
from datetime import datetime as dt

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Streamlit page header
st.set_page_config(page_title="TA Assessments", layout="wide")
st.title("2025 Initial Assessments")
st.info("Utilizing SurveyCTO's EGRA Plugin. As of Jan 25, 2025, we have 41 TAs starting with assessments. The next 40 will begin once their TLT contracts are signed.")

# Read and process data
try:
    df = process_egra_data(
        children_file=os.path.join(ROOT_DIR, "data/EGRA form-assessment_repeat - Jan 30.csv"),
        ta_file=os.path.join(ROOT_DIR, "data/EGRA form - Jan 30.csv")
    )

    # START OF PAGE

    col1, col2, col3 = st.columns(3)

    with col1:# Total Assessed
        st.metric("Total Number of Children Assessed", len(df))

    with col2:
        # Number of TAs that assessed >= 20 kids
        ta_counts = df['name_ta_rep'].value_counts()
        ta_more_than_20 = ta_counts[ta_counts >= 20]
        st.metric("TAs That Assessed > 20 Children", f'{len(ta_more_than_20)}/41')

    with col3:
        # Number of TAs that submitted anything
        ta_counts = df['name_ta_rep'].value_counts()
        st.metric("TAs That Submitted Results (1+ Children)", f'{len(ta_counts)}/41')


    st.divider()

    # Grade Summary
    with st.container():
        st.subheader("EGRA Letters per Grade")
        grade_summary = df.groupby(['grade_label']).agg(
            Number_Assessed=('name_first_learner', 'count'),
            Average_Letters_Correct=('letters_correct_a1', 'mean'),
            Letter_Score=('letters_score_a1', 'mean'),
            Count_Above_40=('letters_correct_a1', lambda x: (x >= 40).sum())
        ).reset_index()
        grade_summary['Average_Letters_Correct'] = grade_summary['Average_Letters_Correct'].round(1)
        grade_summary['Letter_Score'] = grade_summary['Letter_Score'].round(1)

        # Setting a filter for which results end up displayed on the chart.
        grade_summary = grade_summary[grade_summary['Number_Assessed'] > 10]

        fig = px.bar(
            grade_summary,
            x="grade_label",
            y="Average_Letters_Correct",
            title="Avg Score",
            labels={'grade_label': 'Grade', 'Average_Letters_Correct': 'EGRA Score'},
            color="Average_Letters_Correct",
            text="Average_Letters_Correct",
            color_continuous_scale="Blues"  # Optional: Use color to indicate values
        )

        # Adjust layout
        fig.update_layout(
            xaxis_title="Grade",
            yaxis_title="EGRA Scores",
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Show results"):
            st.dataframe(grade_summary, use_container_width=True)

    st.divider()

    # Assessments Per TA
    with st.container():
        st.subheader("Assessments Per TA")

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

    with st.container():
        st.subheader("Assessments Per School & Grade")

        # Group by school and grade, counting the number of assessments
        school_grade_counts = (
            df.groupby(['school_rep', 'grade'])
            .size()
            .reset_index(name='count')
        )

        # Create a combined x-axis label for better readability
        school_grade_counts['school_grade'] = (
            school_grade_counts['school_rep'] + "_" + school_grade_counts['grade'].astype(str)
        )

        # Sort by count (descending)
        school_grade_counts = school_grade_counts.sort_values(by='count', ascending=False)

        # Plot using Plotly
        fig = px.bar(
            school_grade_counts,
            x='school_grade',
            y='count',
            title="Assessments Per School & Grade",
            labels={'school_grade': 'School - Grade', 'count': 'Number of Assessments'},
            color='count',
            text='count',
            color_continuous_scale='Blues'  # Optional: Color gradient for visibility
        )

        # Improve layout
        fig.update_layout(
            height=700,
            xaxis_title="School & Grade",
            yaxis_title="Number of Assessments",
            showlegend=False,
            # xaxis_tickangle=-45  # Tilt x-axis labels for readability
        )

        # Display in Streamlit
        st.plotly_chart(fig, use_container_width=True)

    with st.container():
        st.subheader("Assessments Per School & Grade")

        # Group by school and grade, counting the number of assessments
        school_class_counts = (
            df.groupby(['school_rep','class'])
            .size()
            .reset_index(name='count')
        )

        # Create a combined x-axis label for better readability
        school_class_counts['school_class'] = (
            school_class_counts['school_rep'] + "_" + school_class_counts['class'].astype(str)
        )

        # Sort by count (descending)
        school_class_counts = school_class_counts.sort_values(by='count', ascending=False)

        # Plot using Plotly
        fig = px.bar(
            school_class_counts,
            x='school_class',
            y='count',
            title="Assessments Per School & Class",
            labels={'school_class': 'School - Class', 'count': 'Number of Assessments'},
            color='count',
            text='count',
            color_continuous_scale='Blues'  # Optional: Color gradient for visibility
        )

        # Improve layout
        fig.update_layout(
            height=700,
            xaxis_title="School & Class",
            yaxis_title="Number of Assessments",
            showlegend=False,
            # xaxis_tickangle=-45  # Tilt x-axis labels for readability
        )

        # Display in Streamlit
        st.plotly_chart(fig, use_container_width=True)

    # TA Assessments Summary
    with st.container():
        st.header("Assessments Completed Per School & TA")
        ta_assessments = df.groupby(['school_rep', 'name_ta_rep', 'grade_label'])['name_first_learner'].count().reset_index()
        ta_assessments.columns = ['School', 'TA', 'Grade', 'Count']
        st.dataframe(ta_assessments, use_container_width=True)

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

        # Setting a filter for which results end up displayed on the chart.
        school_summary = school_summary[school_summary['Number_Assessed'] > 10]

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

        # Setting a filter for which results end up displayed on the chart.
        school_non_words_summary = school_non_words_summary[school_non_words_summary['Number_Assessed'] > 10]

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

        # Setting a filter for which results end up displayed on the chart.
        school_words_summary = school_words_summary[school_words_summary['Number_Assessed'] > 10]


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

    st.divider()
    with st.container():
        st.subheader("Data Export Tools")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Generate Letter Tracker"):
                try:
                    letter_tracker_df = create_letter_tracker(df, export_csv=False)
                    csv = letter_tracker_df.to_csv(index=False)
                    st.download_button(
                        label="Download Letter Tracker",
                        data=csv,
                        file_name="Letter_Tracker.csv",
                        mime="text/csv",
                    )
                    st.success("Letter Tracker generated successfully!")
                except Exception as e:
                    st.error(f"Error generating Letter Tracker: {str(e)}")

        with col2:
            if st.button("Generate Full Dataset"):
                try:
                    # Get current date for filename
                    date = dt.today().strftime('%Y-%m-%d')
                    # Convert full DataFrame to CSV
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download Full Dataset",
                        data=csv,
                        file_name=f"merged_data_{date}.csv",
                        mime="text/csv",
                    )
                    st.success("Full dataset ready for download!")
                except Exception as e:
                    st.error(f"Error generating full dataset: {str(e)}")

except Exception as e:
    st.error(f"Error processing data: {str(e)}")
    st.stop()