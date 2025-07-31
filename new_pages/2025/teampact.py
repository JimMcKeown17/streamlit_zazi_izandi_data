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
    with col7:
        ta_counts = df.groupby('Collected By')['First Name'].count()
        active_tas = (ta_counts > 10).sum()
        st.metric("Active TAs (>10 assessments)", active_tas)
        
    st.divider()
    with st.container():
        # Add toggle for median/mean (default to median)
        col_title, col_toggle = st.columns([3, 1])
        with col_title:
            st.subheader("EGRA Scores by Grade")
        with col_toggle:
            use_mean = st.toggle("📊 Show Mean", value=False, key="grade_mean_toggle")
        
        # Choose aggregation method based on toggle (default to median)
        stat_method = 'mean' if use_mean else 'median'
        stat_label = 'Mean' if use_mean else 'Median'
        
        agg_results = df.groupby('Grade').agg({
        'First Name': 'count',
        'Total cells correct - EGRA Letters': stat_method
            }).reset_index()
        
        fig = px.bar(agg_results, x='Grade', y='Total cells correct - EGRA Letters', color='Grade',
                     category_orders={'Grade': ['Grade R', 'Grade 1', 'Grade 2']},
                     title=f'{stat_label} EGRA Letter Scores by Grade')
        
        # Update y-axis label to reflect the statistic being shown
        fig.update_yaxes(title=f'{stat_label} Correct Letters')
        
        st.plotly_chart(fig)    
        
    st.divider()
    with st.container():
        # Add toggle for median/mean (default to median)
        col_title2, col_toggle2 = st.columns([3, 1])
        with col_title2:
            st.subheader("EGRA Scores by Language")
        with col_toggle2:
            use_mean = st.toggle("📊 Show Mean", value=False, key="language_mean_toggle")
        
        # Choose aggregation method based on toggle (default to median)
        stat_method = 'mean' if use_mean else 'median'
        stat_label = 'Mean' if use_mean else 'Median'
        
        agg_results = df.groupby(['Language', 'Grade']).agg({
        'First Name': 'count',
        'Total cells correct - EGRA Letters': stat_method
            }).reset_index()
    
        fig = px.bar(agg_results, x='Language', y='Total cells correct - EGRA Letters', color='Grade', barmode='group',
                     category_orders={'Grade': ['Grade R', 'Grade 1', 'Grade 2']},
                     title=f'{stat_label} EGRA Letter Scores by Language')
        
        # Update y-axis label to reflect the statistic being shown
        fig.update_yaxes(title=f'{stat_label} Correct Letters')
        
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
        # Add title and slider for dynamic threshold
        col_title3, col_slider = st.columns([3, 1])
        with col_title3:
            st.subheader("Percentage Above Benchmark")
        with col_slider:
            # Dynamic slider for lpm threshold
            lpm_threshold = st.slider("Set LPM Threshold", min_value=10, max_value=50, value=40, step=5, key="lpm_threshold_slider")
        
        # Create two columns for side-by-side pie charts
        col1, col2 = st.columns(2)
        
        for i, grade in enumerate(['Grade 1', 'Grade 2']):
            # Calculate data for this grade using dynamic threshold
            above_threshold = df[(df['Grade'] == grade) & (df['Total cells correct - EGRA Letters'] > lpm_threshold)]
            at_or_below_threshold = df[(df['Grade'] == grade) & (df['Total cells correct - EGRA Letters'] <= lpm_threshold)]
            total = df[df['Grade'] == grade]
            
            n_above_threshold = len(above_threshold)
            n_at_or_below_threshold = len(at_or_below_threshold)
            n_total = len(total)
            
            if n_total > 0:
                # Create pie chart data with dynamic labels
                labels = [f'Above {lpm_threshold}lpm', f'At or Below {lpm_threshold}lpm']
                values = [n_above_threshold, n_at_or_below_threshold]
                colors = ['#00cc44', '#ff4444']  # Green for above, red for below
                
                # Create pie chart
                fig_pie = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    marker_colors=colors,
                    textinfo='label+percent',
                    textposition='auto'
                )])
                
                fig_pie.update_layout(
                    title=f'{grade}<br>Total: {n_total} children',
                    showlegend=False,
                    height=500,
                    margin=dict(t=80, b=20, l=20, r=20)
                )
                
                # Display in appropriate column
                if i == 0:
                    with col1:
                        st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    with col2:
                        st.plotly_chart(fig_pie, use_container_width=True)
            else:
                # Handle case where no data exists for this grade
                if i == 0:
                    with col1:
                        st.warning(f"No data available for {grade}")
                else:
                    with col2:
                        st.warning(f"No data available for {grade}")
        
        # Add expander with school-level breakdown
        with st.expander("📊 School-Level Breakdown"):
            # Filter for Grade 1 and Grade 2 only since that's what we're analyzing above
            grade_1_2_df = df[df['Grade'].isin(['Grade 1', 'Grade 2'])]
            
            if len(grade_1_2_df) > 0:
                # Create summary by Program Name and Grade
                school_summary = []
                
                for school in grade_1_2_df['Program Name'].unique():
                    for grade in ['Grade 1', 'Grade 2']:
                        school_grade_data = grade_1_2_df[
                            (grade_1_2_df['Program Name'] == school) & 
                            (grade_1_2_df['Grade'] == grade)
                        ]
                        
                        if len(school_grade_data) > 0:
                            above_count = len(school_grade_data[school_grade_data['Total cells correct - EGRA Letters'] > lpm_threshold])
                            total_count = len(school_grade_data)
                            below_count = total_count - above_count
                            percentage_above = (above_count / total_count * 100) if total_count > 0 else 0
                            
                            school_summary.append({
                                'School': school,
                                'Grade': grade,
                                'Total Children': total_count,
                                f'Above {lpm_threshold}lpm': above_count,
                                f'At/Below {lpm_threshold}lpm': below_count,
                                '% Above Threshold': f"{percentage_above:.1f}%"
                            })
                
                if school_summary:
                    summary_df = pd.DataFrame(school_summary)
                    
                    # Sort by school name and then by grade
                    summary_df = summary_df.sort_values(['School', 'Grade'])
                    
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)
                    
                    # Add summary statistics
                    st.write("**Summary:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        total_schools = summary_df['School'].nunique()
                        st.metric("Schools Analyzed", total_schools)
                    with col2:
                        total_children = summary_df['Total Children'].sum()
                        st.metric("Total Children", total_children)
                    with col3:
                        total_above = summary_df[f'Above {lpm_threshold}lpm'].sum()
                        overall_percentage = (total_above / total_children * 100) if total_children > 0 else 0
                        st.metric("Overall % Above Threshold", f"{overall_percentage:.1f}%")
                else:
                    st.warning("No data available for analysis")
            else:
                st.warning("No Grade 1 or Grade 2 data available")

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

    st.divider()
    st.subheader("Extra Data Checks")
    
    with st.expander("Teacher Assistants with Low Assessment Counts"):
        assessments_per_TA = df.groupby('Collected By').agg({
            'First Name': 'count',
        }).reset_index()
        assessments_per_TA = assessments_per_TA.sort_values(by='First Name', ascending=False)
        low_count_TAs = assessments_per_TA[assessments_per_TA['First Name'] < 15]
        
        if len(low_count_TAs) > 0:
            st.write(f"**{len(low_count_TAs)} Teacher Assistants** have completed fewer than 15 assessments:")
            st.dataframe(low_count_TAs.rename(columns={'First Name': 'Assessment Count'}), use_container_width=True)
        else:
            st.success("All Teacher Assistants have completed 15 or more assessments!")

display_2025_teampact()