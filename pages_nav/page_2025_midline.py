import streamlit as st
import pandas as pd
import plotly.express as px
from process_survey_cto_updated import process_egra_data
import os

def show():
    # Check authentication
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Execute the content from the original 2025 results page - Midline tab only
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    @st.cache_data
    def load_egra_data(children_filename: str, ta_filename: str):
        """
        Caches the DataFrame loading and processing so it doesn't
        re-run on every Streamlit re-execution or widget change.
        """
        children_path = os.path.join(ROOT_DIR, "data", children_filename)
        ta_path       = os.path.join(ROOT_DIR, "data", ta_filename)

        df, df_ecd = process_egra_data(
            children_file=children_path,
            ta_file=ta_path
        )
        return df, df_ecd

    st.title("2025 Midline Assessments")
    
    # Read and process data
    try:
            df_full, df_ecd = load_egra_data(
                children_filename="EGRA form [Eastern Cape]-assessment_repeat - June 4.csv",
                ta_filename="EGRA form [Eastern Cape] - June 4.csv"
            )
            df_full['submission_date'] = pd.to_datetime(df_full['date'])
            
            # Create initial and midline datasets for comparison charts
            initial_df = df_full[df_full['submission_date'] < pd.Timestamp('2025-04-15')]
            midline_df = df_full[df_full['submission_date'] >= pd.Timestamp('2025-04-15')]
            
            # START OF PAGE

            col1, col2, col3 = st.columns(3)

            with col1:# Total Assessed
                st.metric("Total Number of Children Assessed", len(midline_df))

            with col2:
                # Number of TAs that assessed >= 20 kids
                ta_counts = midline_df['name_ta_rep'].value_counts()
                ta_more_than_20 = ta_counts[ta_counts >= 20]
                st.metric("TAs That Assessed > 20 Children", f'{len(ta_more_than_20)}')

            with col3:
                # Number of TAs that submitted anything
                ta_counts = midline_df['name_ta_rep'].value_counts()
                st.metric("TAs That Submitted Results (1+ Children)", f'{len(ta_counts)}')

            st.divider()

            # Add the three charts from 1_Letter Knowledge.py
            with st.container():
                st.subheader('Letter EGRA Improvement')

                # Calculate summary for initial assessments
                initial_summary = initial_df.groupby('grade_label').agg({
                    'letters_correct': 'mean'
                }).round(1).reset_index()
                initial_summary.columns = ['Grade', 'Initial Score']

                # Calculate summary for midline assessments
                midline_summary = midline_df.groupby('grade_label').agg({
                    'letters_correct': 'mean'
                }).round(1).reset_index()
                midline_summary.columns = ['Grade', 'Midline Score']

                # Merge the summaries
                egra_summary = pd.merge(initial_summary, midline_summary, on='Grade', how='outer')

                # Melt the DataFrame for Plotly
                egra_summary_melted = egra_summary.melt(
                    id_vars='Grade',
                    value_vars=['Initial Score', 'Midline Score'],
                    var_name='Measurement',
                    value_name='Score'
                )

                # Create the Plotly bar graph with grouped bars
                egra_fig = px.bar(
                    egra_summary_melted,
                    x='Grade',
                    y='Score',
                    color='Measurement',
                    barmode='group',
                    labels={'Score': 'Average Score'},
                    color_discrete_map={'Initial Score': '#b3b3b3', 'Midline Score': '#ffd641'}
                )

                st.plotly_chart(egra_fig, use_container_width=True)

                with st.expander('Click to view data:'):
                    st.dataframe(egra_summary)

            st.divider()

            with st.container():
                st.subheader("Percentage of Grade 1's On Grade Level")
                st.success("The number of Grade 1 children 'On Grade Level' for letter knowledge more than quadrupled, increasing from 13% to 53%!")

                # Filter for Grade 1 only
                g1_initial = initial_df[initial_df['grade_label'] == 'Grade 1']
                g1_midline = midline_df[midline_df['grade_label'] == 'Grade 1']

                # Calculate percentages for initial
                initial_40_or_more = (g1_initial['letters_correct'] >= 40).sum()
                initial_less_than_40 = (g1_initial['letters_correct'] < 40).sum()
                total_initial = initial_40_or_more + initial_less_than_40

                initial_40_or_more_percent = (initial_40_or_more / total_initial).round(3) * 100 if total_initial > 0 else 0
                initial_less_than_40_percent = (initial_less_than_40 / total_initial).round(3) * 100 if total_initial > 0 else 0

                # Calculate percentages for midline
                midline_40_or_more = (g1_midline['letters_correct'] >= 40).sum()
                midline_less_than_40 = (g1_midline['letters_correct'] < 40).sum()
                total_midline = midline_40_or_more + midline_less_than_40

                midline_40_or_more_percent = (midline_40_or_more / total_midline).round(3) * 100 if total_midline > 0 else 0
                midline_less_than_40_percent = (midline_less_than_40 / total_midline).round(3) * 100 if total_midline > 0 else 0

                # Create DataFrame
                data = {
                    'Above Grade Level': [initial_40_or_more_percent, midline_40_or_more_percent]
                }

                df_grade_level = pd.DataFrame(data, index=['Initial', 'Midline'])

                # Melt the DataFrame for Plotly
                df_melted = df_grade_level.reset_index().melt(
                    id_vars='index',
                    value_vars=['Above Grade Level'],
                    var_name='Score Category',
                    value_name='Percentage'
                )

                # Create the Plotly bar graph
                grade_level_fig = px.bar(
                    df_melted,
                    x='index',
                    y='Percentage',
                    color='Score Category',
                    barmode='group',
                    labels={'index': 'Assessment', 'Percentage': 'Percentage (%)'},
                    color_discrete_map={'Above Grade Level': '#32c93c'}
                )

                # Add horizontal line at y=27 with label 'South Africa Average'
                grade_level_fig.add_hline(
                    y=27,
                    line_dash='dash',
                    line_color='red',
                    annotation_text='South Africa Average',
                    annotation_position='top left'
                )

                st.plotly_chart(grade_level_fig, use_container_width=True)

                with st.expander('Click to view data:'):
                    st.dataframe(df_grade_level)

    except Exception as e:
        st.error(f"Error loading data: {e}") 