import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from process_teampact_data import process_teampact_data
import os
from datetime import datetime as dt
from dotenv import load_dotenv
from data_loader import load_zazi_izandi_2025_tp
import traceback

# Load environment variables
load_dotenv()

def display_2025_teampact():
    # Check authentication
    if 'user' not in st.session_state:
        st.session_state.user = None


    st.title("2025 TeamPact Assessments")
    
    # Read and process data
    try:
        xhosa_df, english_df, afrikaans_df = load_zazi_izandi_2025_tp()
        df = process_teampact_data(xhosa_df, english_df, afrikaans_df)
        
        if df.empty:
            st.warning("⚠️ No assessment data was found.")
        
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.error(traceback.format_exc())
        
    # Okay, let's create some charts!
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Assessments", len(df))
    with col2:
        st.metric("isiXhosa", len(xhosa_df))
    with col3:
        st.metric("English", len(english_df))
    with col4: 
        st.metric("Afrikaans", len(afrikaans_df))
        
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        st.metric("Teacher Assistants", df['Collected By'].nunique())
    with col6:
        st.metric("Schools", df['Program Name'].nunique())
        
    st.divider()
    with st.container():
        st.subheader("EGRA Scores by Grade")
        agg_results = df.groupby('Grade').agg({
        'First Name': 'count',
        'Total cells correct - EGRA Letters': 'mean'
            }).reset_index()
        fig = px.bar(agg_results, x='Grade', y='Total cells correct - EGRA Letters', color='Grade',
                     category_orders={'Grade': ['Grade R', 'Grade 1', 'Grade 2']})
        st.plotly_chart(fig)    
        
    st.divider()
    with st.container():
        st.subheader("EGRA Scores by Language")
        agg_results = df.groupby(['Language', 'Grade']).agg({
        'First Name': 'count',
        'Total cells correct - EGRA Letters': 'mean'
            }).reset_index()
    
        fig = px.bar(agg_results, x='Language', y='Total cells correct - EGRA Letters', color='Grade', barmode='group',
                     category_orders={'Grade': ['Grade R', 'Grade 1', 'Grade 2']})
        st.plotly_chart(fig)
        
    st.divider()
    with st.container():
        st.subheader("Average EGRA Scores by Data Collector")
        
        # Create a dropdown for grade
        grade_options = ['Grade R', 'Grade 1', 'Grade 2']
        selected_grade = st.selectbox('Select Grade', grade_options)
        
        # Filter data for the selected grade
        filtered_df = df[df['Grade'] == selected_grade]
        
        # Group by 'Collected By' and calculate mean and count
        collector_stats = filtered_df.groupby('Collected By').agg({
            'Total cells correct - EGRA Letters': 'mean',
            'First Name': 'count'
        }).reset_index()
        
        # Rename columns for clarity
        collector_stats = collector_stats.rename(columns={
            'Total cells correct - EGRA Letters': 'Mean_Score',
            'First Name': 'Count'
        })
        
        # Sort by descending mean score
        collector_stats = collector_stats.sort_values('Mean_Score', ascending=False)
        
        # Replace the go.Figure() approach with this simpler px.bar() approach
        fig = px.bar(
            collector_stats, 
            x='Collected By', 
            y='Mean_Score',
            title='Average Total Cells Correct by Data Collector',
            labels={
                'Mean_Score': 'Mean Correct Cells',
                'Collected By': 'Collected By'
            }
        )

        # Add the count labels as text
        fig.update_traces(
            text=[f'n={count}' for count in collector_stats['Count']],
            textposition='outside'
        )

        # Rotate x-axis labels and sort by descending values
        fig.update_xaxes(tickangle=45, categoryorder='total descending')
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    with st.container():
        st.subheader("Number of Children Assessed by Data Collector")
        
        # Create a dropdown for grade
        grade_options_count = ['Grade R', 'Grade 1', 'Grade 2']
        selected_grade_count = st.selectbox('Select Grade', grade_options_count, key='grade_count_selector')
        
        # Filter data for the selected grade
        filtered_df_count = df[df['Grade'] == selected_grade_count]
        
        # Group by 'Collected By' and count records
        collector_counts = filtered_df_count.groupby('Collected By').agg({
            'First Name': 'count'
        }).reset_index()
        
        # Rename columns for clarity
        collector_counts = collector_counts.rename(columns={
            'First Name': 'Count'
        })
        
        # Sort by descending count
        collector_counts = collector_counts.sort_values('Count', ascending=False)
        
        # Create bar chart showing counts
        fig_count = px.bar(
            collector_counts, 
            x='Collected By', 
            y='Count',
            title='Number of Children Assessed by Data Collector',
            labels={
                'Count': 'Number of Children',
                'Collected By': 'Collected By'
            }
        )

        # Add the count labels as text on the bars
        fig_count.update_traces(
            text=collector_counts['Count'],
            textposition='outside'
        )

        # Rotate x-axis labels and sort by descending values
        fig_count.update_xaxes(tickangle=45, categoryorder='total descending')
        
        st.plotly_chart(fig_count, use_container_width=True)

    st.divider()
    with st.container():
        st.subheader("Percentage Above Grade 1 Benchmark (40lpm)")
        
        # Calculate percentages above benchmark (40) for Grade 1 and Grade 2
        grade_data = []

        for grade in ['Grade 1', 'Grade 2']:
            above_40 = df[(df['Grade'] == grade) & (df['Total cells correct - EGRA Letters'] > 40)]
            total = df[df['Grade'] == grade]
            
            n_above_40 = len(above_40)
            n_total = len(total)
            pct_above_40 = (n_above_40 / n_total) * 100 if n_total > 0 else 0
            
            grade_data.append({
                'Grade': grade,
                'Percentage_Above_40': pct_above_40,
                'Count_Above_40': n_above_40,
                'Total_Count': n_total
            })

        benchmark_df = pd.DataFrame(grade_data)

        fig_benchmark = px.bar(
            benchmark_df, 
            x='Grade', 
            y='Percentage_Above_40',
            title='Percentage of Learners Above Grade 1 Benchmark (40lpm)',
            labels={'Percentage_Above_40': 'Percentage Above 40', 'Grade': 'Grade'},
            color='Grade'
        )

        st.plotly_chart(fig_benchmark, use_container_width=True)

    st.divider()
    with st.container():
        st.subheader("Distribution of EGRA Letter Scores")
        
        # Create a dropdown for grade selection
        grade_options_hist = ['Grade R', 'Grade 1', 'Grade 2']
        selected_grade_hist = st.selectbox('Select Grade for Score Distribution', grade_options_hist, key='grade_hist_selector')
        
        # Filter data for the selected grade
        filtered_df_hist = df[df['Grade'] == selected_grade_hist]
        
        if len(filtered_df_hist) > 0:
            # Create buckets of size 5
            scores = filtered_df_hist['Total cells correct - EGRA Letters']
            
            # Define bucket edges (0-4, 5-9, 10-14, etc.)
            max_score = int(scores.max()) + 1
            bucket_edges = list(range(0, max_score + 5, 5))
            
            # Create bucket labels
            bucket_labels = [f"{i}-{i+4}" for i in range(0, max_score, 5)]
            
            # Create histogram using plotly
            fig_hist = px.histogram(
                filtered_df_hist,
                x='Total cells correct - EGRA Letters',
                nbins=len(bucket_labels),
                title=f'Distribution of EGRA Letter Scores - {selected_grade_hist}',
                labels={
                    'Total cells correct - EGRA Letters': 'EGRA Letters Correct',
                    'count': 'Number of Children'
                }
            )
            
            # Update layout to show bucket ranges clearly
            fig_hist.update_layout(
                xaxis_title='EGRA Letters Correct (Score Ranges)',
                yaxis_title='Number of Children',
                bargap=0.1
            )
            
            # Add count labels on top of bars
            fig_hist.update_traces(texttemplate='%{y}', textposition='outside')
            
            st.plotly_chart(fig_hist, use_container_width=True)
            
            # Show summary statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Children", len(filtered_df_hist))
            with col2:
                st.metric("Mean Score", f"{scores.mean():.1f}")
            with col3:
                st.metric("Median Score", f"{scores.median():.1f}")
            with col4:
                st.metric("Max Score", f"{scores.max():.0f}")
        else:
            st.warning(f"No data available for {selected_grade_hist}")

display_2025_teampact()