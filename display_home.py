import os
import pandas as pd
import plotly.express as px
import streamlit as st
from zz_data_processing import process_zz_data_midline, process_zz_data_endline, grade1_df, gradeR_df
from data_loader import load_zazi_izandi_2024

def display_home():
    # Load assets and data
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = os.path.join(base_dir, 'assets/Zazi iZandi logo.png')
    baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df = load_zazi_izandi_2024()

    # Process data
    midline, baseline = process_zz_data_midline(baseline_df, midline_df, sessions_df)
    endline = process_zz_data_endline(endline_df)
    grade1 = grade1_df(endline)
    gradeR = gradeR_df(endline)

    # Display logo
    st.image(logo_path, width=250)

    # Summary Stats
    st.header('2024 SUMMARY STATS')
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric('Community\n Youth Jobs:', '82')
    with c2:
        st.metric('Children on\n Programme:', '3490')
    with c3:
        st.metric('Schools on\n Programme:', '16')
    st.divider()

    # Percentage of Grade 1s On Grade Level
    st.subheader("Percentage of Grade 1's On Grade Level")
    st.success(
        "We double the number of children at Grade Level by the end of Grade 1. "
        "This critical benchmark is the leading indicator for success in school."
    )

    # Calculate percentages
    baseline_40_or_more = (grade1['EGRA Baseline'] >= 40).sum()
    total_baseline = len(grade1)
    baseline_40_or_more_percent = round((baseline_40_or_more / total_baseline) * 100, 1)

    endline_40_or_more = (grade1['EGRA Endline'] >= 40).sum()
    total_endline = len(grade1)
    endline_40_or_more_percent = round((endline_40_or_more / total_endline) * 100, 1)

    # Create DataFrame for visualization
    df = pd.DataFrame({
        'Assessment': ['Baseline', 'Endline'],
        'Above Grade Level': [baseline_40_or_more_percent, endline_40_or_more_percent]
    })

    # Bar Chart
    grade_level_fig = px.bar(
        df,
        x='Assessment',
        y='Above Grade Level',
        labels={'Above Grade Level': 'Percentage (%)'},
        title="Percentage of Grade 1's Above Grade Level",
        color_discrete_sequence=['#32c93c']
    )
    grade_level_fig.add_hline(y=27, line_dash="dash", line_color="red", annotation_text="South Africa Average")

    st.plotly_chart(grade_level_fig, width='stretch')
    st.divider()

    # Show data table
    with st.expander('Click to view data:'):
        st.dataframe(df)
