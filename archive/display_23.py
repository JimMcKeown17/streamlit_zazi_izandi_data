import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
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
        st.success('On average, the Grade 1 children improved their EGRA score by 96% while the Grade Rs improved theirs by 416%')
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

        st.plotly_chart(egra_fig, width='stretch')

    with st.expander('Click to view data:'):
        egra_summary = endline.groupby('Grade').agg({
            'Masi Egra Full Baseline': 'mean',
            'Masi Egra Full Endline': 'mean',
            'Egra Improvement Endline': 'mean'
        }).round(1)
        st.dataframe(egra_summary)

    st.markdown("---")
    # Masi Letters Known Baseline	Masi Letters Known Midline	Masi Letters Known Endline
    with st.container():
        st.subheader('Letters Known Improvement')
        st.success('Our Grade R children improved their letter knowledge by 254% and learned, while the Grade 1s improved by 61%.')
        letter_summary = endline.groupby('Grade').agg({
            'Masi Letters Known Baseline': 'mean',
            'Masi Letters Known Endline': 'mean',
        }).round(1).reset_index()

        # Attempt to Melt
        letter_summary_melted = letter_summary.melt(id_vars="Grade",
                                                    value_vars=['Masi Letters Known Baseline', 'Masi Letters Known Endline'],
                                                    var_name="Measurement", value_name="Letters Known")

        # Create the Plotly bar graph with grouped bars
        letter_fig = px.bar(
            letter_summary_melted,
            x='Grade',
            y='Letters Known',
            color='Measurement',
            barmode='group',
            labels={'Letters Known': 'Average Letter Known'},
            color_discrete_map={'Masi Letters Known Baseline': GREY, 'Masi Letters Known Endline': BLUE}

        )
        st.plotly_chart(letter_fig, width='stretch')

        with st.expander('Click to view data:'):
            letter_summary = endline.groupby('Grade').agg({
                'Masi Letters Known Baseline': 'mean',
                'Masi Letters Known Endline': 'mean',
            }).round(1)
            st.dataframe(letter_summary)

    st.markdown('---')
    #Masi Egra Full Baseline	Masi Egra Full Midline	Masi Egra Full Endline
    with st.container():
        st.subheader("Percentage of Grade 1's On Grade Level")
        st.success("The number of Grade 1 children 'On Grade Level' for letter knowledge increased from 22% to 74% on the 2-minute EGRA.")
        egra_time = st.selectbox("Choose EGRA Time Limit", ['2-min', '1-min'])

        if egra_time == '2-min':
            baseline_metric = 'Masi Egra Full Baseline'
            endline_metric = 'Masi Egra Full Endline'
        else:
            baseline_metric = 'Masi Egra Full Baseline'
            endline_metric = 'Masi Egra 1-min Endline'

        grade1 = endline[endline['Grade'] == 'Grade 1']
        # Calculate percentages for baseline
        baseline_40_or_more = (grade1[baseline_metric] >= 40).sum()
        baseline_less_than_40 = (grade1[baseline_metric] < 40).sum()
        total_baseline = baseline_40_or_more + baseline_less_than_40

        baseline_40_or_more_percent = (baseline_40_or_more / total_baseline).round(3) * 100
        baseline_less_than_40_percent = (baseline_less_than_40 / total_baseline).round(3) * 100

        # Calculate percentages for midline
        midline_40_or_more = (grade1[endline_metric] >= 40).sum()
        midline_less_than_40 = (grade1[endline_metric] < 40).sum()
        total_midline = midline_40_or_more + midline_less_than_40

        midline_40_or_more_percent = (midline_40_or_more / total_midline).round(3) * 100
        midline_less_than_40_percent = (midline_less_than_40 / total_midline).round(3) * 100

        # Create DataFrame
        data = {
            'Above Grade Level': [baseline_40_or_more_percent, midline_40_or_more_percent]
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

        st.plotly_chart(grade_level_fig, width='stretch')

        with st.expander('Click to view data:'):
            st.dataframe(df)

        st.markdown('---')
        # Masi Egra Full Baseline	Masi Egra Full Midline	Masi Egra Full Endline

        st.header('SCHOOL PERFORMANCE')

        with st.container():
            st.subheader('School Level EGRA Improvement')

            grade_selection = st.selectbox('Select Grade', ['All Grades', 'Grade 1', 'Grade R'], key="egra2")
            if grade_selection == 'All Grades':
                filtered_midline = endline
            else:
                filtered_midline = endline[endline['Grade'] == grade_selection]

            school_egra_improvement = filtered_midline.groupby(['School']).agg({
                'Masi Egra Full Baseline': 'mean',
                'Masi Egra Full Endline': 'mean',
                'Egra Improvement Endline': 'mean',
            }).round(1).sort_values(by='Egra Improvement Endline', ascending=False).reset_index()

            school_fig = px.bar(
                school_egra_improvement,
                x='School',
                y='Egra Improvement Endline',
                color_discrete_sequence=[YELLOW]
            )
            st.plotly_chart(school_fig, width='stretch')

            with st.expander('Click to view data:'):
                school_egra_improvement = filtered_midline.groupby(['School']).agg({
                    'Masi Egra Full Baseline': 'mean',
                    'Masi Egra Full Endline': 'mean',
                    'Egra Improvement Endline': 'mean',
                }).round(1).sort_values(by='Egra Improvement Endline', ascending=False)
                st.dataframe(school_egra_improvement)


