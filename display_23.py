import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from zz_data_processing import process_zz_data, grade1_df, gradeR_df
from zz_data_process_23 import process_zz_data_23
from data_loader import load_zazi_izandi_2023
import os
import streamlit as st

def display_2023():
    # Import dataframes
    endline_df, sessions_df = load_zazi_izandi_2023()

    endline = process_zz_data_23(endline_df, sessions_df)


    #ZZ Website colours. Going to use Yellow for EGRA and Blue for Letters Known
    YELLOW = '#ffd641'
    BLUE = '#28a1ff'
    GREY = '#b3b3b3'
    GREEN = '#32c93c'

    # START PAGE NOW
    col1, col2 = st.columns(2)
    with col1:
        st.image('assets/Zazi iZandi logo.png', width=250)
    with col2:
        st.title('2023 Results')
    # FEATURE STATS
    st.header('SUMMARY STATS')
    c1,c2,c3 = st.columns(3)
    with c1:
        st.metric('Community\n Youth Jobs:', '52')
    with c2:
        st.metric('Children on\n Programme:', '1897')
    with c3:
        st.metric('Schools on\n Programme:', '12')

    st.markdown('---')

    st.info("It's important to remember that our 2023 pilot started mid-August and only ran for 3 months. So the baseline scores are a bit higher than in 2024, when children started in January.")

    st.markdown('---')
    st.header('HIGHLIGHTS')

    # FIRST CHART
    # Masi Egra Full Baseline	Masi Egra Full Midline	Masi Egra Full Endline	Masi Egra 1-min Endline
    # Masi Letters Known Baseline	Masi Letters Known Midline	Masi Letters Known Endline
    with st.container():
        st.subheader('Letter EGRA Improvement')
        st.success('On average, the children improved their Letter EGRA scores '
                   'by 214% (17 points).')
        egra_summary = endline.groupby('Grade').agg({
            'Masi Egra Full Baseline': 'mean',
            'Masi Egra Full Endline': 'mean',
            'Egra Improvement Endline': 'mean'
        }).round(1).reset_index()

        # Melt the DataFrame for Plotly
        egra_summary_melted = egra_summary.melt(id_vars='Grade',
                                                value_vars=['Masi Egra Full Baseline', 'Masi Egra Full Endline'],
                                                var_name='Measurement', value_name='Score')

        # Create the Plotly bar graph with grouped bars
        egra_fig = px.bar(
            egra_summary_melted,
            x='Grade',
            y='Score',
            color='Measurement',
            barmode='group',
            labels={'Score': 'Average Score'},
            color_discrete_map={'Masi Egra Full Baseline': GREY, 'Masi Egra Full Endline': YELLOW}
        )

        st.plotly_chart(egra_fig, use_container_width=True)

    with st.expander('Click to view data:'):
        egra_summary = endline.groupby('Grade').agg({
            'Masi Egra Full Baseline': 'mean',
            'Masi Egra Full Endline': 'mean',
            'Egra Improvement Endline': 'mean'
        }).round(1)
        st.dataframe(egra_summary)

    st.markdown("---")


