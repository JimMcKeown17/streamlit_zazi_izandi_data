import streamlit as st
import pandas as pd
import plotly.express as px
from zz_data_processing import process_zz_data_midline, process_zz_data_endline, grade1_df, gradeR_df
from data_loader import load_zazi_izandi_2024
import os

def word_reading_page():

    #Import Dataframes - create deep copies to avoid tab interference
    baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df = load_zazi_izandi_2024()
    
    # Create deep copies to ensure data independence between tabs
    baseline2_df = baseline2_df.copy()
    endline2_df = endline2_df.copy()
    base_dir = os.path.dirname(os.path.abspath(__file__))

    #Process Dataframes
    midline, baseline = process_zz_data_midline(baseline_df, midline_df, sessions_df)
    endline = process_zz_data_endline(endline_df)
    grade1 = grade1_df(endline)
    gradeR = gradeR_df(endline)

    st.title("Word Reading")
    st.success(
        "Zazi IZandi 2.0 (aka Word Reading) is for children that have learned all of their letter sounds. They now focus on learning to blend those letter sounds together to make, and ultimately read, words. As of Sept 17, 2024 we have 522 children on ZZ 2.0. This represents 47% of the initial Grade 1 cohort. The remaining 53% are still mastering their letter sounds on ZZ 1.0")

    st.markdown("---")
    with st.container():
        st.subheader("Average Word Reading and Non-Word Reading Scores")
        st.info(
            "The charts below compare the average scores for Word Reading and Non-Word Reading between Baseline and Endline assessments.")

        # Calculate average scores for Word Reading
        baseline_avg_word_reading = baseline2_df['B. Word reading'].mean()
        endline_avg_word_reading = endline2_df['B. Word reading'].mean()

        # Calculate average scores for Non-Word Reading
        baseline_avg_nonword_reading = baseline2_df['A.Non-word reading'].mean()
        endline_avg_nonword_reading = endline2_df['A.Non-word reading'].mean()

        # Prepare data for Word Reading bar chart
        data_word_reading = pd.DataFrame({
            'Cohort': ['Baseline', 'Endline'],
            'Average Score': [baseline_avg_word_reading, endline_avg_word_reading]
        })

        # Prepare data for Non-Word Reading bar chart
        data_nonword_reading = pd.DataFrame({
            'Cohort': ['Baseline', 'Endline'],
            'Average Score': [baseline_avg_nonword_reading, endline_avg_nonword_reading]
        })

        # Define color mapping for Cohorts
        color_discrete_map = {
            'Baseline': 'blue',
            'Endline': 'red'
        }

        # Create two columns for side-by-side display
        col1, col2 = st.columns(2)

        # Word Reading Bar Chart
        with col1:
            st.write("**Average Word Reading Scores**")
            fig_word = px.bar(
                data_word_reading,
                x='Cohort',
                y='Average Score',
                color='Cohort',
                color_discrete_map=color_discrete_map,
                text='Average Score',
                title='Word Reading'
            )
            fig_word.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig_word.update_layout(
                showlegend=False,
                xaxis_title=None,
                yaxis_title='Average Score'
            )
            st.plotly_chart(fig_word)

        # Non-Word Reading Bar Chart
        with col2:
            st.write("**Average Non-Word Reading Scores**")
            fig_nonword = px.bar(
                data_nonword_reading,
                x='Cohort',
                y='Average Score',
                color='Cohort',
                color_discrete_map=color_discrete_map,
                text='Average Score',
                title='Non-Word Reading'
            )
            fig_nonword.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig_nonword.update_layout(
                showlegend=False,
                xaxis_title=None,
                yaxis_title='Average Score'
            )
            st.plotly_chart(fig_nonword)

    st.markdown("---")
    with st.container():
        st.subheader("Word Reading Buckets Pie Charts")
        st.info("The charts below bucket children's assessment scores based on the numbers of words read.")

        # Define bins and labels
        bins = [-1, 0, 5, 10, 15, 20, float('inf')]  # float('inf') represents 21+
        labels = ['0', '1-5', '6-10', '11-15', '16-20', '21+']

        # Define color mapping for each group
        color_discrete_map = {
            '0': 'darkblue',
            '1-5': 'blue',
            '6-10': 'lightblue',
            '11-15': 'green',
            '16-20': 'orange',
            '21+': 'red'
        }

        # Create two columns for side-by-side display
        col1, col2 = st.columns(2)

        # Process and display Baseline DataFrame in the left column
        with col1:
            st.write("**Baseline Word Reading Distribution**")
            df_baseline = baseline2_df.copy()
            
            # Check if we have valid data first
            if df_baseline.empty or 'B. Word reading' not in df_baseline.columns:
                st.warning("No baseline word reading data available.")
            else:
                # Remove any rows with NaN values in the target column
                valid_data = df_baseline['B. Word reading'].dropna()
                if len(valid_data) == 0:
                    st.warning("No valid baseline word reading data available.")
                else:
                    # Create a new dataframe with only valid data
                    df_clean = df_baseline[df_baseline['B. Word reading'].notna()].copy()
                    df_clean['Word Reading Group'] = pd.cut(
                        df_clean['B. Word reading'], bins=bins, labels=labels, right=True
                    )
                    
                    # Get value counts and ensure we have data
                    bucket_counts_baseline = df_clean['Word Reading Group'].value_counts()
                    if len(bucket_counts_baseline) == 0:
                        st.warning("No data falls into the defined reading buckets.")
                    else:
                        # Create DataFrame ensuring proper data types
                        bucket_df_baseline = pd.DataFrame({
                            'Group': bucket_counts_baseline.index.astype(str),
                            'Count': bucket_counts_baseline.values
                        }).reset_index(drop=True)
                        
                        fig_baseline = px.pie(
                            bucket_df_baseline,
                            values='Count',
                            names='Group',
                            title='Baseline',
                            hole=0.4
                        )
                        fig_baseline.update_layout(legend_title_text='No. of words read')
                        st.plotly_chart(fig_baseline)

        # Process and display Endline DataFrame in the right column
        with col2:
            st.write("**Endline Word Reading Distribution**")
            df_endline = endline2_df.copy()
            
            # Check if we have valid data first
            if df_endline.empty or 'B. Word reading' not in df_endline.columns:
                st.warning("No endline word reading data available.")
            else:
                # Remove any rows with NaN values in the target column
                valid_data = df_endline['B. Word reading'].dropna()
                if len(valid_data) == 0:
                    st.warning("No valid endline word reading data available.")
                else:
                    # Create a new dataframe with only valid data
                    df_clean = df_endline[df_endline['B. Word reading'].notna()].copy()
                    df_clean['Word Reading Group'] = pd.cut(
                        df_clean['B. Word reading'], bins=bins, labels=labels, right=True
                    )
                    
                    # Get value counts and ensure we have data
                    bucket_counts_endline = df_clean['Word Reading Group'].value_counts()
                    if len(bucket_counts_endline) == 0:
                        st.warning("No data falls into the defined reading buckets.")
                    else:
                        # Create DataFrame ensuring proper data types
                        bucket_df_endline = pd.DataFrame({
                            'Group': bucket_counts_endline.index.astype(str),
                            'Count': bucket_counts_endline.values
                        }).reset_index(drop=True)
                        
                        fig_endline = px.pie(
                            bucket_df_endline,
                            values='Count',
                            names='Group',
                            title='Endline',
                            hole=0.4
                        )
                        fig_endline.update_layout(legend_title_text='No. of words read')
                        st.plotly_chart(fig_endline)

    st.markdown("---")
    with st.container():
        st.subheader("Non-Word Reading Buckets Pie Charts")
        st.info("The charts below bucket children's assessment scores based on the numbers of non-words read.")

        # Define bins and labels
        bins = [-1, 0, 5, 10, 15, 20, float('inf')]  # float('inf') represents 21+
        labels = ['0', '1-5', '6-10', '11-15', '16-20', '21+']

        # Define color mapping for each group
        color_discrete_map = {
            '0': 'darkblue',
            '1-5': 'blue',
            '6-10': 'lightblue',
            '11-15': 'green',
            '16-20': 'orange',
            '21+': 'red'
        }

        # Create two columns for side-by-side display
        col1, col2 = st.columns(2)

        # Process and display Baseline DataFrame in the left column
        with col1:
            st.write("**Baseline Non-Word Reading Distribution**")
            df_baseline = baseline2_df.copy()
            
            # Check if we have valid data first
            if df_baseline.empty or 'A.Non-word reading' not in df_baseline.columns:
                st.warning("No baseline non-word reading data available.")
            else:
                # Remove any rows with NaN values in the target column
                valid_data = df_baseline['A.Non-word reading'].dropna()
                if len(valid_data) == 0:
                    st.warning("No valid baseline non-word reading data available.")
                else:
                    # Create a new dataframe with only valid data
                    df_clean = df_baseline[df_baseline['A.Non-word reading'].notna()].copy()
                    df_clean['Non-Word Reading Group'] = pd.cut(
                        df_clean['A.Non-word reading'], bins=bins, labels=labels, right=True
                    )
                    
                    # Get value counts and ensure we have data
                    bucket_counts_baseline = df_clean['Non-Word Reading Group'].value_counts()
                    if len(bucket_counts_baseline) == 0:
                        st.warning("No data falls into the defined non-word reading buckets.")
                    else:
                        # Create DataFrame ensuring proper data types
                        bucket_df_baseline = pd.DataFrame({
                            'Group': bucket_counts_baseline.index.astype(str),
                            'Count': bucket_counts_baseline.values
                        }).reset_index(drop=True)
                        
                        fig_baseline = px.pie(
                            bucket_df_baseline,
                            values='Count',
                            names='Group',
                            title='Baseline',
                            hole=0.4
                        )
                        fig_baseline.update_layout(legend_title_text='No. of non-words read')
                        st.plotly_chart(fig_baseline)

        # Process and display Endline DataFrame in the right column
        with col2:
            st.write("**Endline Non-Word Reading Distribution**")
            df_endline = endline2_df.copy()
            
            # Check if we have valid data first
            if df_endline.empty or 'A.Non-word reading' not in df_endline.columns:
                st.warning("No endline non-word reading data available.")
            else:
                # Remove any rows with NaN values in the target column
                valid_data = df_endline['A.Non-word reading'].dropna()
                if len(valid_data) == 0:
                    st.warning("No valid endline non-word reading data available.")
                else:
                    # Create a new dataframe with only valid data
                    df_clean = df_endline[df_endline['A.Non-word reading'].notna()].copy()
                    df_clean['Non-Word Reading Group'] = pd.cut(
                        df_clean['A.Non-word reading'], bins=bins, labels=labels, right=True
                    )
                    
                    # Get value counts and ensure we have data
                    bucket_counts_endline = df_clean['Non-Word Reading Group'].value_counts()
                    if len(bucket_counts_endline) == 0:
                        st.warning("No data falls into the defined non-word reading buckets.")
                    else:
                        # Create DataFrame ensuring proper data types
                        bucket_df_endline = pd.DataFrame({
                            'Group': bucket_counts_endline.index.astype(str),
                            'Count': bucket_counts_endline.values
                        }).reset_index(drop=True)
                        
                        fig_endline = px.pie(
                            bucket_df_endline,
                            values='Count',
                            names='Group',
                            title='Endline',
                            hole=0.4
                        )
                        fig_endline.update_layout(legend_title_text='No. of non-words read')
                        st.plotly_chart(fig_endline)

    with st.container():
        st.subheader("Histogram Results for ZZ 2.0")
        st.info(
            "The Non-Word assessment included 10 2-letter sounds to begin, so it is not comparable to the 'Real Word' assessment. You'll notice many kids in the 0-10 buckets for non-words b/c they could blend those two sounds together.")
        # Dropdown selection for the df
        df_choice = st.selectbox(
            "Select a cohort:",
            ("Baseline", "Endline"), key="histogram_df1"
        )

        if df_choice == "Baseline":
            df = baseline2_df.copy()
        else:
            df = endline2_df.copy()

        word_metric = st.selectbox(
            "Select a variable for the histogram:",
            ("Real Words", "Non-Words")
        )

        if word_metric == "Non-Words":
            variable = "A.Non-word reading"
        else:
            variable = "B. Word reading"

        fig = px.histogram(df, x=variable, title=f"Histogram of {variable}")

        st.plotly_chart(fig)

    with st.container():
        st.subheader("Non-word reading vs. Word reading Scores")

        df_choice = st.selectbox(
            "Select a cohort:",
            ("Baseline", "Endline")
        )

        if df_choice == "Baseline":
            df = baseline2_df.copy()
        else:
            df = endline2_df.copy()

        fig = px.scatter(df,
                         x="A.Non-word reading",
                         y="B. Word reading",
                         title="Non-word reading vs. Word reading Scores")

        st.plotly_chart(fig)

