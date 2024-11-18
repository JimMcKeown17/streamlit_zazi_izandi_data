import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from zz_data_processing import process_zz_data_midline, process_zz_data_endline, grade1_df, gradeR_df
from data_loader import load_zazi_izandi_2024
import os
import streamlit as st

# Import dataframes
baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df = load_zazi_izandi_2024()
base_dir = os.path.dirname(os.path.abspath(__file__))

# ZZ Website colours. Going to use Yellow for EGRA and Blue for Letters Known
YELLOW = '#ffd641'
BLUE = '#28a1ff'
GREY = '#b3b3b3'
GREEN = '#32c93c'

midline, baseline = process_zz_data_midline(baseline_df, midline_df, sessions_df)
endline = process_zz_data_endline(endline_df)
grade1 = grade1_df(endline)
gradeR = gradeR_df(endline)

# START PAGE NOW

def display_home():
    st.image('assets/Zazi iZandi logo.png', width=250)
    # FEATURE STATS
    st.header('SUMMARY STATS')
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric('Community\n Youth Jobs:', '82')
    with c2:
        st.metric('Children on\n Programme:', '3490')
    with c3:
        st.metric('Schools on\n Programme:', '16')
    st.divider()

    with st.container():
        st.subheader("Percentage of Grade 1's On Grade Level")
        st.success(
            "We double the number of children at Grade Level by the end of Grade 1. This critical benchmark is the leading indicator for success in school. It is highly correlated with becoming a reader by age 10.")

        # Calculate percentages for baseline
        baseline_40_or_more = (grade1['EGRA Baseline'] >= 40).sum()
        baseline_less_than_40 = (grade1['EGRA Baseline'] < 40).sum()
        total_baseline = baseline_40_or_more + baseline_less_than_40

        baseline_40_or_more_percent = (baseline_40_or_more / total_baseline).round(3) * 100
        baseline_less_than_40_percent = (baseline_less_than_40 / total_baseline).round(3) * 100

        # Calculate percentages for midline
        endline_40_or_more = (grade1['EGRA Endline'] >= 40).sum()
        endline_less_than_40 = (grade1['EGRA Endline'] < 40).sum()
        total_endline = endline_40_or_more + endline_less_than_40

        endline_40_or_more_percent = (endline_40_or_more / total_endline).round(3) * 100
        endline_less_than_40_percent = (endline_less_than_40 / total_endline).round(3) * 100

        # Create DataFrame
        data = {
            'Above Grade Level': [baseline_40_or_more_percent, endline_40_or_more_percent]
        }

        df = pd.DataFrame(data, index=['Baseline', 'Endline'])

        # Melt the DataFrame for Plotly
        df_melted = df.reset_index().melt(id_vars='index', value_vars=['Above Grade Level'],
                                          var_name='Score Category', value_name='Percentage')

        # Create the Plotly bar graph
        grade_level_fig = px.bar(
            df_melted,
            x='index',
            y='Percentage',
            color='Score Category',
            barmode='group',
            labels={'index': 'Assessment', 'Percentage': 'Percentage (%)'},
            color_discrete_map={'Above Grade Level': GREEN}

        )
        # Add horizontal line at y=27 with label 'South Africa Average'
        grade_level_fig.add_hline(y=27, line_dash='dash', line_color='red', annotation_text='South Africa Average',
                                  annotation_position='top left')

        st.plotly_chart(grade_level_fig, use_container_width=True)

        with st.expander('Click to view data:'):
            st.dataframe(df)
        st.divider()
