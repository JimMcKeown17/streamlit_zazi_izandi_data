import streamlit as st
import pandas as pd
import plotly.express as px
from process_survey_cto_updated import process_egra_data
from create_letter_tracker import create_letter_tracker
from letter_tracker_htmls import main as create_html_reports
import os
from datetime import datetime as dt
from data_loader import load_zazi_izandi_2025

def display_baseline():
    # Check authentication
    if 'user' not in st.session_state:
        st.session_state.user = None
    

    st.title("2025 Initial Assessments")

    # Read and process data
    try:

        df_full, df_ecd = load_zazi_izandi_2025()
        df_full['submission_date'] = pd.to_datetime(df_full['date'])
        
        # Create initial dataset for initial assessments (before midline cutoff)
        initial_df = df_full[df_full['submission_date'] < pd.Timestamp('2025-04-15')]

        # START OF PAGE

        col1, col2, col3 = st.columns(3)

        with col1:# Total Assessed
            st.metric("Total Number of Children Assessed", len(initial_df))

        with col2:
            # Number of TAs that assessed >= 20 kids
            ta_counts = initial_df['name_ta_rep'].value_counts()
            ta_more_than_20 = ta_counts[ta_counts >= 20]
            st.metric("TAs That Assessed > 20 Children", f'{len(ta_more_than_20)}')

        with col3:
            # Number of TAs that submitted anything
            ta_counts = initial_df['name_ta_rep'].value_counts()
            st.metric("TAs That Submitted Results (1+ Children)", f'{len(ta_counts)}')

        st.divider()

        # Grade Summary
        with st.container():
            st.subheader("EGRA Letters per Grade")
            grade_summary = initial_df.groupby(['grade_label']).agg(
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

        # School Summary
        with st.container():
            st.header("School Summary")
            school_summary = initial_df.groupby(['school_rep', 'grade_label']).agg(
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

        st.divider()
        
        # Add this section after your existing Grade 1 analyses
        with st.container():
            st.header("Grade 1 Learners Hitting Benchmark")
            st.info("This is a measure of how many Grade 1 learners are hitting the benchmark of 40 letters correct.")

            # Filter for Grade 1 only
            g1_letter_scores = initial_df[initial_df['grade_label'] == 'Grade 1']

            # Calculate overall statistics
            total_g1_students = len(g1_letter_scores)
            students_above_40 = len(g1_letter_scores[g1_letter_scores['letters_score_a1'] >= 40])
            percentage_above_40 = (students_above_40 / total_g1_students * 100) if total_g1_students > 0 else 0

            # Create a simple bar chart showing percentage
            fig = px.bar(
                x=['Grade 1'],
                y=[percentage_above_40],
                title='Percentage of Grade 1 Learners with Letter Score >= 40',
                labels={'x': 'Grade', 'y': 'Percentage (%)'},
                text=[f'{percentage_above_40:.1f}%'],
                color=[percentage_above_40],
                color_continuous_scale='RdYlGn'
            )

            # Customize layout
            fig.update_layout(
                xaxis_title="",
                yaxis_title="Percentage (%)",
                showlegend=False,
                yaxis_range=[0, 100],  # Set y-axis from 0 to 100%
                height=400
            )

            # Display chart
            st.plotly_chart(fig, use_container_width=True)

            # Show summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Grade 1 Students", total_g1_students)
            with col2:
                st.metric("Students with Score >= 40", students_above_40)
            with col3:
                st.metric("Percentage Above 40", f"{percentage_above_40:.1f}%")

        st.divider()
        
        # Grade 1 Benchmark by School
        with st.container():
            st.header("Grade 1 Benchmark by School")

            # Filter for Grade 1 only
            g1_letter_scores = initial_df[initial_df['grade_label'] == 'Grade 1']

            # Calculate percentage by school
            school_letter_score_summary = g1_letter_scores.groupby('school_rep').agg(
                Total_Assessed=('name_first_learner', 'count'),
                Above_40_Count=('letters_score_a1', lambda x: (x >= 40).sum())
            ).reset_index()

            # Calculate percentage
            school_letter_score_summary['Percentage_Above_40'] = (
                    school_letter_score_summary['Above_40_Count'] /
                    school_letter_score_summary['Total_Assessed'] * 100
            ).round(1)

            # Sort by percentage descending
            school_letter_score_summary = school_letter_score_summary.sort_values(
                by='Percentage_Above_40', ascending=False
            )

            # Create bar chart
            fig = px.bar(
                school_letter_score_summary,
                x='school_rep',
                y='Percentage_Above_40',
                title='Percentage of Grade 1 Learners with Letter Score >= 40 by School',
                labels={'school_rep': 'School', 'Percentage_Above_40': 'Percentage (%)'},
                color='Percentage_Above_40',
                text='Percentage_Above_40',
                color_continuous_scale='RdYlGn'
            )

            # Customize layout
            fig.update_layout(
                xaxis_title="School",
                yaxis_title="Percentage (%)",
                showlegend=False,
                yaxis_range=[0, 100]  # Set y-axis from 0 to 100%
            )

            # Display chart
            st.plotly_chart(fig, use_container_width=True)

            # Show detailed table
            st.dataframe(school_letter_score_summary, use_container_width=True)

        # Data Export Tools section (truncated for brevity, but includes PDF generation)
        with st.container():
            st.subheader("Data Export Tools")
            st.info("Export tools for generating letter trackers and datasets.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Generate Letter Tracker CSV"):
                    try:
                        letter_tracker_df = create_letter_tracker(initial_df, export_csv=False)
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
                        csv = initial_df.to_csv(index=False)
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
        
display_baseline()