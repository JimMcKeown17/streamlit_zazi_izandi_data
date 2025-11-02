import streamlit as st
import plotly.express as px
import pandas as pd
from zz_data_processing import process_zz_data_midline, process_zz_data_endline, grade1_df
from zz_data_process_23 import process_zz_data_23
from data_loader import load_zazi_izandi_2024, load_zazi_izandi_2023, load_zazi_izandi_new_schools_2024
from process_survey_cto_updated import process_egra_data
import os


# ZZ Website colours
YELLOW = '#ffd641'
BLUE = '#28a1ff' 
GREY = '#b3b3b3'
GREEN = '#32c93c'
RED = '#ff6b6b'

def display_year_comparisons():

    st.title("Year Comparisons")
    st.subheader("Comparative Analysis Across Years and Assessment Periods")

    # Filter for assessment period - default to Midline
    assessment_filter = st.selectbox(
        "Filter by Assessment Period:",
        ["Baseline", "Midline", "Endline"],
        index=1  # Default to Midline
    )

    st.markdown("---")

    # Load all datasets
    @st.cache_data
    def load_all_data():
        # 2023 data
        endline_2023, sessions_2023 = load_zazi_izandi_2023()
        data_2023 = process_zz_data_23(endline_2023, sessions_2023)
        
        # 2024 data
        baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df = load_zazi_izandi_2024()
        midline_2024, baseline_2024 = process_zz_data_midline(baseline_df, midline_df, sessions_df)
        endline_2024 = process_zz_data_endline(endline_df)
        
        # 2024 New Schools data
        new_schools_df = load_zazi_izandi_new_schools_2024()
        
        # 2025 data (from CSV files)
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        children_path = os.path.join(root_dir, "data", "EGRA form [Eastern Cape]-assessment_repeat - June 4.csv")
        ta_path = os.path.join(root_dir, "data", "EGRA form [Eastern Cape] - June 4.csv")
        
        try:
            data_2025, _ = process_egra_data(children_file=children_path, ta_file=ta_path)
            data_2025['submission_date'] = pd.to_datetime(data_2025['date'])
        except:
            data_2025 = pd.DataFrame()  # Empty if files don't exist
        
        return data_2023, baseline_2024, midline_2024, endline_2024, new_schools_df, data_2025

    data_2023, baseline_2024, midline_2024, endline_2024, new_schools_df, data_2025 = load_all_data()

    # Standardize all grade names upfront to avoid issues
    baseline_2024['Grade'] = baseline_2024['Grade'].replace({'1': 'Grade 1', 'R': 'Grade R'})
    midline_2024['Grade'] = midline_2024['Grade'].replace({'1': 'Grade 1', 'R': 'Grade R'})
    endline_2024['Grade'] = endline_2024['Grade'].replace({'1': 'Grade 1', 'R': 'Grade R'})
    new_schools_df['Grade'] = new_schools_df['Grade'].replace({'1': 'Grade 1', 'R': 'Grade R'})

    def get_egra_scores_by_period(assessment_period):
        """Get EGRA scores for all years based on assessment period"""
        
        if assessment_period == "Baseline":
            # 2023 Baseline
            egra_2023 = data_2023.groupby('Grade')['Masi Egra Full Baseline'].mean().round(1)
            
            # 2024 Baseline  
            egra_2024 = baseline_2024.groupby('Grade')['EGRA Baseline'].mean().round(1)
            
            # 2025 Baseline (early submissions)
            if not data_2025.empty:
                early_2025 = data_2025[data_2025['submission_date'] < pd.Timestamp('2025-04-15')]
                egra_2025 = early_2025.groupby('grade_label')['letters_correct'].mean().round(1)
            else:
                egra_2025 = pd.Series()
                
        elif assessment_period == "Midline":
            # 2023 Midline (using available data)
            egra_2023 = data_2023.groupby('Grade')['Masi Egra Full Midline'].mean().round(1) if 'Masi Egra Full Midline' in data_2023.columns else pd.Series()
            
            # 2024 Midline
            egra_2024 = midline_2024.groupby('Grade')['EGRA Midline'].mean().round(1)
            
            # 2025 Midline (recent submissions)
            if not data_2025.empty:
                recent_2025 = data_2025[data_2025['submission_date'] >= pd.Timestamp('2025-04-15')]
                egra_2025 = recent_2025.groupby('grade_label')['letters_correct'].mean().round(1)
            else:
                egra_2025 = pd.Series()
                
        else:  # Endline
            # 2023 Endline
            egra_2023 = data_2023.groupby('Grade')['Masi Egra Full Endline'].mean().round(1)
            
            # 2024 Endline
            egra_2024 = endline_2024.groupby('Grade')['EGRA Endline'].mean().round(1)
            
            # 2025 Endline (not available yet)
            egra_2025 = pd.Series()
        
        return egra_2023, egra_2024, egra_2025

    def get_benchmark_percentages_by_period(assessment_period):
        """Get percentage of Grade 1s over benchmark (40) by assessment period"""
        
        if assessment_period == "Baseline":
            # 2023
            grade1_2023 = data_2023[data_2023['Grade'] == 'Grade 1']
            pct_2023 = ((grade1_2023['Masi Egra Full Baseline'] >= 40).sum() / len(grade1_2023) * 100).round(1) if len(grade1_2023) > 0 else 0
            
            # 2024
            grade1_2024 = baseline_2024[baseline_2024['Grade'] == 'Grade 1']
            pct_2024 = ((grade1_2024['EGRA Baseline'] >= 40).sum() / len(grade1_2024) * 100).round(1) if len(grade1_2024) > 0 else 0
            
            # 2024 New Schools
            grade1_new = new_schools_df[new_schools_df['Grade'] == 'Grade 1']
            pct_2024_new = ((grade1_new['Baseline Assessment Score'] >= 40).sum() / len(grade1_new) * 100).round(1) if len(grade1_new) > 0 else 0
            
            # 2025
            if not data_2025.empty:
                early_2025 = data_2025[data_2025['submission_date'] < pd.Timestamp('2025-04-15')]
                grade1_2025 = early_2025[early_2025['grade_label'] == 'Grade 1']
                pct_2025 = ((grade1_2025['letters_correct'] >= 40).sum() / len(grade1_2025) * 100).round(1) if len(grade1_2025) > 0 else 0
            else:
                pct_2025 = 0
                
        elif assessment_period == "Midline":
            # 2023 (using available data)
            if 'Masi Egra Full Midline' in data_2023.columns:
                grade1_2023 = data_2023[data_2023['Grade'] == 'Grade 1']
                pct_2023 = ((grade1_2023['Masi Egra Full Midline'] >= 40).sum() / len(grade1_2023) * 100).round(1) if len(grade1_2023) > 0 else 0
            else:
                pct_2023 = 0
            
            # 2024
            grade1_2024 = midline_2024[midline_2024['Grade'] == 'Grade 1']
            pct_2024 = ((grade1_2024['EGRA Midline'] >= 40).sum() / len(grade1_2024) * 100).round(1) if len(grade1_2024) > 0 else 0
            
            # 2024 New Schools (no midline data available)
            pct_2024_new = 0
            
            # 2025
            if not data_2025.empty:
                recent_2025 = data_2025[data_2025['submission_date'] >= pd.Timestamp('2025-04-15')]
                grade1_2025 = recent_2025[recent_2025['grade_label'] == 'Grade 1']
                pct_2025 = ((grade1_2025['letters_correct'] >= 40).sum() / len(grade1_2025) * 100).round(1) if len(grade1_2025) > 0 else 0
            else:
                pct_2025 = 0
                
        else:  # Endline
            # 2023
            grade1_2023 = data_2023[data_2023['Grade'] == 'Grade 1']
            pct_2023 = ((grade1_2023['Masi Egra Full Endline'] >= 40).sum() / len(grade1_2023) * 100).round(1) if len(grade1_2023) > 0 else 0
            
            # 2024
            grade1_2024 = endline_2024[endline_2024['Grade'] == 'Grade 1']
            pct_2024 = ((grade1_2024['EGRA Endline'] >= 40).sum() / len(grade1_2024) * 100).round(1) if len(grade1_2024) > 0 else 0
            
            # 2024 New Schools
            grade1_new = new_schools_df[new_schools_df['Grade'] == 'Grade 1']
            pct_2024_new = ((grade1_new['Endline Assessment Score'] >= 40).sum() / len(grade1_new) * 100).round(1) if len(grade1_new) > 0 else 0
            
            # 2025 (not available yet)
            pct_2025 = 0
        
        return pct_2023, pct_2024, pct_2024_new, pct_2025

    # Chart 1: EGRA Score Comparison
    st.subheader(f"1. EGRA Score Comparison ({assessment_filter})")

    egra_2023, egra_2024, egra_2025 = get_egra_scores_by_period(assessment_filter)

    # Create comparison dataframe for EGRA scores
    egra_comparison_data = []

    # Add 2023 data
    for grade in egra_2023.index:
        egra_comparison_data.append({
            'Year': '2023',
            'Grade': grade,
            'EGRA Score': egra_2023[grade]
        })

    # Add 2024 data  
    for grade in egra_2024.index:
        egra_comparison_data.append({
            'Year': '2024', 
            'Grade': grade,
            'EGRA Score': egra_2024[grade]
        })

    # Add 2025 data if available
    for grade in egra_2025.index:
        egra_comparison_data.append({
            'Year': '2025',
            'Grade': grade, 
            'EGRA Score': egra_2025[grade]
        })

    if egra_comparison_data:
        egra_df = pd.DataFrame(egra_comparison_data)
        
        egra_fig = px.bar(
            egra_df,
            x='Grade',
            y='EGRA Score', 
            color='Year',
            barmode='group',
            title=f'EGRA Scores by Grade - {assessment_filter}',
            color_discrete_map={'2023': GREY, '2024': BLUE, '2025': YELLOW}
        )
        
        st.plotly_chart(egra_fig, width='stretch')
        
        with st.expander('View EGRA Score Data'):
            st.dataframe(egra_df)
    else:
        st.warning(f"No EGRA score data available for {assessment_filter} period")

    st.markdown("---")

    # Chart 2: Percentage Over Benchmark
    st.subheader(f"2. Percentage of Grade 1's Over Benchmark (40 letters/min) - {assessment_filter}")

    pct_2023, pct_2024, pct_2024_new, pct_2025 = get_benchmark_percentages_by_period(assessment_filter)

    # Create comparison dataframe for benchmark percentages
    benchmark_data = [
        {'Year': '2023', 'Percentage Over Benchmark': pct_2023},
        {'Year': '2024', 'Percentage Over Benchmark': pct_2024},
        {'Year': '2024_New_Schools', 'Percentage Over Benchmark': pct_2024_new},
        {'Year': '2025', 'Percentage Over Benchmark': pct_2025}
    ]

    # Filter out years with 0% if they represent missing data
    if assessment_filter == "Endline" and pct_2025 == 0:
        benchmark_data = benchmark_data[:-1]  # Remove 2025 for endline as it's not available yet
        
    if assessment_filter == "Midline" and pct_2024_new == 0:
        benchmark_data = [d for d in benchmark_data if d['Year'] != '2024_New_Schools']  # Remove new schools midline

    benchmark_df = pd.DataFrame(benchmark_data)

    benchmark_fig = px.bar(
        benchmark_df,
        x='Year',
        y='Percentage Over Benchmark',
        title=f'Percentage of Grade 1s Over Benchmark (40 letters/min) - {assessment_filter}',
        color='Year',
        color_discrete_map={
            '2023': GREY, 
            '2024': BLUE, 
            '2024_New_Schools': GREEN,
            '2025': YELLOW
        }
    )

    # Add horizontal line at national average
    benchmark_fig.add_hline(
        y=27,
        line_dash='dash',
        line_color='red',
        annotation_text='South Africa Average (27%)',
        annotation_position='top left'
    )

    st.plotly_chart(benchmark_fig, width='stretch')

    with st.expander('View Benchmark Data'):
        st.dataframe(benchmark_df)

    # Additional info
    st.markdown("---")
    st.info("""
    **Notes:**
    - The benchmark for Grade 1 letter knowledge is 40 letters per minute in isiXhosa
    - South Africa average is approximately 27% of Grade 1 students meeting this benchmark
    - 2024_New_Schools represents schools that joined the program in 2024
    - Data availability varies by assessment period and year
    """) 
    
display_year_comparisons()