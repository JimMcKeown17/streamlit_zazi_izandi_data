import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
from dotenv import load_dotenv
import sys
import os

# Ensure the project root is on the import path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from database_utils import get_database_engine, check_table_exists
from data_loader import load_zazi_izandi_2025_tp
from process_teampact_data import process_teampact_data

# Load environment variables
load_dotenv()

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_baseline_data():
    """
    Load baseline assessment data from CSV files
    
    Returns:
        pandas.DataFrame: Baseline assessment data
    """
    try:
        # Load baseline data from CSV files
        baseline_xhosa_df, baseline_english_df, baseline_afrikaans_df = load_zazi_izandi_2025_tp()
        
        # Process baseline data
        if baseline_xhosa_df is not None:
            baseline_df = process_teampact_data(baseline_xhosa_df, baseline_english_df, baseline_afrikaans_df)
            
            if baseline_df.empty:
                return pd.DataFrame()
            
            return baseline_df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Error loading baseline data: {e}")
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame()

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_assessment_data_from_db():
    """
    Load endline assessment data from Django database
    Includes cohort assignments, quality flags, and session counts
    
    Returns:
        pandas.DataFrame: Assessment data with all calculated fields
    """
    try:
        # Check if table exists
        if not check_table_exists("teampact_assessment_endline_2025"):
            st.error("Assessment table not found in database. Please ensure sync has been run.")
            return pd.DataFrame()
        
        engine = get_database_engine()
        
        # Load all assessment data with cohort and flag information
        query = """
        SELECT 
            response_id,
            user_id,
            survey_id,
            survey_name,
            program_name as "Program Name",
            class_name as "Class Name",
            collected_by as "Collected By",
            response_date as "Response Date",
            first_name as "First Name",
            last_name as "Last Name",
            email,
            gender as "Gender",
            grade as "Grade",
            language as "Language",
            total_correct as "Total cells correct - EGRA Letters",
            total_incorrect,
            total_attempted,
            total_not_attempted,
            assessment_complete,
            stop_rule_reached,
            timer_elapsed,
            time_elapsed_completion,
            assessment_type,
            -- Cohort & session fields
            session_count_total,
            session_count_30_days,
            session_count_90_days,
            cohort_session_range,
            -- Quality flags
            flag_moving_too_fast,
            flag_same_letter_groups,
            cohort_calculated_at,
            -- Timestamps
            created_at,
            updated_at,
            data_refresh_timestamp
        FROM teampact_assessment_endline_2025
        WHERE assessment_type = 'endline'
        ORDER BY response_date DESC
        """
        
        df = pd.read_sql(query, engine)
        
        if df.empty:
            st.warning("No endline assessment data found in database.")
            return df
        
        # Convert date columns to datetime
        date_columns = ['Response Date', 'cohort_calculated_at', 'created_at', 'updated_at', 'data_refresh_timestamp']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Create a combined participant name
        df['Participant Name'] = df['First Name'] + ' ' + df['Last Name']
        
        # Create flag indicators for analysis
        df['Has Quality Flags'] = df['flag_moving_too_fast'] | df['flag_same_letter_groups']
        df['Both Flags'] = df['flag_moving_too_fast'] & df['flag_same_letter_groups']
        
        return df
        
    except Exception as e:
        st.error(f"Error loading assessment data from database: {e}")
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame()

def get_cohort_order():
    """Return the logical order of session cohorts"""
    return ['0-10', '11-20', '21-30', '31-40', '41+', '']

def display_nmb_endline_cohort_analysis():
    """Main function to display the cohort and quality analysis page"""
    
    st.title("📊 NMB 2025 Endline Analysis")
    st.warning("Internal notes: We need to make decisions around which data to exclude, as many of these schools never really ran the programme. We also have to be aware of Grade 1 graduates showing up in the low session buckets and skewing the data. They didn't receive sessions b/c they already knew 40+, but it's hard to exclude currently b/c of Teampact's setup. There is, potentially, a lot of noise in this data until Teampact can help us determine which kids were a) originally assessed b) on the programme and c) also assessed at endline.")    
    # Load data
    with st.spinner("Loading assessment data from database..."):
        df = load_assessment_data_from_db()
    
    if df.empty:
        st.error("No data available for analysis")
        return
    
    # Show data refresh info
    if 'data_refresh_timestamp' in df.columns and not df['data_refresh_timestamp'].isna().all():
        last_refresh = df['data_refresh_timestamp'].max()
        st.info(f"📅 Data last refreshed: {last_refresh.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Global session filter toggle
    st.divider()
    col_toggle, col_info = st.columns([1, 3])
    with col_toggle:
        filter_sessions = st.toggle("📌 Show only 11+ sessions", value=False, key="global_session_filter")
    
    # Apply global filter if enabled
    if filter_sessions:
        df_filtered = df[df['session_count_total'] >= 11].copy()
        with col_info:
            st.info(f"🔍 Filtered to {len(df_filtered):,} assessments with 11+ sessions (from {len(df):,} total)")
        df = df_filtered
    
    st.divider()
    
    # Create tabs
    tabs = st.tabs([
        "📊 Overview",
        "🎯 Cohort Performance", 
        "🚩 Quality Flag Impact",
        "🔬 Cross-Analysis",
        "🏫 School & EA Insights",
        "📈 Data Explorer"
    ])
    
    # Tab 1: Overview
    with tabs[0]:
        render_overview_tab(df)
    
    # Tab 2: Cohort Performance
    with tabs[1]:
        render_cohort_performance_tab(df)
    
    # Tab 3: Quality Flag Impact
    with tabs[2]:
        render_flag_impact_tab(df)
    
    # Tab 4: Cross-Analysis
    with tabs[3]:
        render_cross_analysis_tab(df)
    
    # Tab 5: School & EA Insights
    with tabs[4]:
        render_school_ea_insights_tab(df)
    
    # Tab 6: Data Explorer
    with tabs[5]:
        render_data_explorer_tab(df)

def render_overview_tab(df):
    """Render the overview and distribution tab"""
    st.header("📊 Overview & Distribution")
    
    # Grade filter at the top
    col_filter, col_space = st.columns([1, 3])
    with col_filter:
        grade_filter = st.selectbox(
            "Filter by Grade",
            options=['All Grades', 'Grade R', 'Grade 1', 'Grade 2'],
            key='overview_grade_filter'
        )
    
    # Apply grade filter
    if grade_filter != 'All Grades':
        df_filtered = df[df['Grade'] == grade_filter].copy()
        st.info(f"Showing {len(df_filtered):,} assessments for {grade_filter}")
    else:
        df_filtered = df.copy()
    
    # Filter to only expected grades
    expected_grades = ['Grade R', 'Grade 1', 'Grade 2']
    df_filtered = df_filtered[df_filtered['Grade'].isin(expected_grades)]
    
    # Overall metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Assessments", f"{len(df_filtered):,}")
    with col2:
        with_sessions = df_filtered[df_filtered['session_count_total'] > 0].shape[0]
        st.metric("With Session Data", f"{with_sessions:,}")
    with col3:
        flagged = df_filtered['Has Quality Flags'].sum()
        pct = (flagged/len(df_filtered)*100) if len(df_filtered) > 0 else 0
        st.metric("With Quality Flags", f"{flagged:,} ({pct:.1f}%)")
    with col4:
        with_cohort = df_filtered[df_filtered['cohort_session_range'].notna() & (df_filtered['cohort_session_range'] != '')].shape[0]
        st.metric("With Cohort Assignment", f"{with_cohort:,}")
    
    st.divider()
    
    # Baseline vs Endline Comparison - MOVED TO TOP
    st.subheader("📊 Baseline vs Endline Comparison")
    st.info("The baseline data is from August 2025, while the endline data is from October 2025. The programme itself was run for approximately 8 weeks, with a 2 week school holiday in the middle.")
    
    col_toggle_comparison = st.columns([3, 1])
    with col_toggle_comparison[1]:
        use_mean_comparison = st.toggle("📊 Show Mean", value=False, key="comparison_mean_toggle")
    
    stat_method_comparison = 'mean' if use_mean_comparison else 'median'
    stat_label_comparison = 'Mean' if use_mean_comparison else 'Median'
    
    # Load baseline data
    baseline_df = load_baseline_data()
    
    # Calculate baseline scores dynamically
    baseline_scores = {}
    if not baseline_df.empty:
        # Filter to only expected grades in baseline data
        baseline_df_filtered = baseline_df[baseline_df['Grade'].isin(['Grade R', 'Grade 1', 'Grade 2'])]
        
        baseline_by_grade = baseline_df_filtered.groupby('Grade').agg({
            'Total cells correct - EGRA Letters': stat_method_comparison
        }).reset_index()
        
        for _, row in baseline_by_grade.iterrows():
            baseline_scores[row['Grade']] = row['Total cells correct - EGRA Letters']
    
    # If baseline data failed to load, use fallback values with a warning
    if not baseline_scores:
        st.warning("⚠️ Could not load baseline data. Using fallback median values.")
        baseline_scores = {
            'Grade R': 2,
            'Grade 1': 15,
            'Grade 2': 37
        }
    
    # Get endline scores for comparison
    endline_scores_comparison = df_filtered.groupby('Grade').agg({
        'Total cells correct - EGRA Letters': stat_method_comparison
    }).reset_index()
    
    # Create comparison dataframe
    comparison_data = []
    for grade in ['Grade R', 'Grade 1', 'Grade 2']:
        baseline_score = baseline_scores.get(grade, 0)
        endline_row = endline_scores_comparison[endline_scores_comparison['Grade'] == grade]
        endline_score = endline_row['Total cells correct - EGRA Letters'].values[0] if len(endline_row) > 0 else 0
        
        comparison_data.append({
            'Grade': grade,
            'Period': 'Baseline (August)',
            'Score': baseline_score
        })
        comparison_data.append({
            'Grade': grade,
            'Period': 'Endline (Oct)',
            'Score': endline_score
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Create grouped bar chart
    fig_comparison = px.bar(
        comparison_df, 
        x='Grade', 
        y='Score',
        color='Period',
        barmode='group',
        category_orders={'Grade': ['Grade R', 'Grade 1', 'Grade 2']},
        title=f'{stat_label_comparison} EGRA Scores: Baseline vs Endline',
        color_discrete_map={'Baseline (August)': '#94a3b8', 'Endline (Oct)': '#3b82f6'}
    )
    
    # Add value labels on bars
    fig_comparison.update_traces(texttemplate='%{y:.1f}', textposition='outside')
    fig_comparison.update_yaxes(title=f'{stat_label_comparison} Correct Letters')
    
    st.plotly_chart(fig_comparison, use_container_width=True)
    
    # Calculate and display improvements
    col1, col2, col3 = st.columns(3)
    for i, grade in enumerate(['Grade R', 'Grade 1', 'Grade 2']):
        baseline = baseline_scores[grade]
        endline_row = endline_scores_comparison[endline_scores_comparison['Grade'] == grade]
        endline = endline_row['Total cells correct - EGRA Letters'].values[0] if len(endline_row) > 0 else 0
        improvement = endline - baseline
        pct_improvement = (improvement / baseline * 100) if baseline > 0 else 0
        
        with [col1, col2, col3][i]:
            st.metric(
                grade,
                f"{endline:.1f}",
                delta=f"+{improvement:.1f} ({pct_improvement:+.1f}%)",
                delta_color="normal"
            )
    
    st.divider()
    
    # Grade 1 Benchmark Comparison
    st.subheader("🎯 Grade 1: Baseline vs Endline Benchmark Achievement")
    
    col_slider_g1 = st.columns([3, 1])
    with col_slider_g1[1]:
        grade1_threshold = st.slider("Grade 1 Benchmark (LPM)", min_value=20, max_value=40, value=40, step=5, key="grade1_benchmark_slider")
    
    # Get Grade 1 data for baseline and endline
    baseline_g1 = baseline_df[baseline_df['Grade'] == 'Grade 1'] if not baseline_df.empty else pd.DataFrame()
    endline_g1 = df_filtered[df_filtered['Grade'] == 'Grade 1']
    
    col1_g1, col2_g1 = st.columns(2)
    
    # Baseline Grade 1 pie chart
    with col1_g1:
        if len(baseline_g1) > 0:
            above_baseline = len(baseline_g1[baseline_g1['Total cells correct - EGRA Letters'] > grade1_threshold])
            below_baseline = len(baseline_g1) - above_baseline
            
            labels = [f'Above {grade1_threshold}lpm', f'At or Below {grade1_threshold}lpm']
            values = [above_baseline, below_baseline]
            colors = ['#00cc44', '#ff4444']
            
            fig_pie_baseline = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                textinfo='label+percent',
                textposition='auto'
            )])
            
            fig_pie_baseline.update_layout(
                title=f'Grade 1 Baseline (August)<br>Total: {len(baseline_g1):,} children',
                showlegend=False,
                height=400,
                margin=dict(t=80, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig_pie_baseline, use_container_width=True)
        else:
            st.warning("No Grade 1 baseline data available")
    
    # Endline Grade 1 pie chart
    with col2_g1:
        if len(endline_g1) > 0:
            above_endline = len(endline_g1[endline_g1['Total cells correct - EGRA Letters'] > grade1_threshold])
            below_endline = len(endline_g1) - above_endline
            
            labels = [f'Above {grade1_threshold}lpm', f'At or Below {grade1_threshold}lpm']
            values = [above_endline, below_endline]
            colors = ['#00cc44', '#ff4444']
            
            fig_pie_endline = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                textinfo='label+percent',
                textposition='auto'
            )])
            
            fig_pie_endline.update_layout(
                title=f'Grade 1 Endline (Oct)<br>Total: {len(endline_g1):,} children',
                showlegend=False,
                height=400,
                margin=dict(t=80, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig_pie_endline, use_container_width=True)
        else:
            st.warning("No Grade 1 endline data available")
    
    st.divider()
    
    # Grade R Benchmark Comparison
    st.subheader("🎯 Grade R: Baseline vs Endline Benchmark Achievement")
    
    col_slider_gr = st.columns([3, 1])
    with col_slider_gr[1]:
        gradeR_threshold = st.slider("Grade R Benchmark (LPM)", min_value=0, max_value=40, value=10, step=10, key="gradeR_benchmark_slider")
    
    # Get Grade R data for baseline and endline
    baseline_gr = baseline_df[baseline_df['Grade'] == 'Grade R'] if not baseline_df.empty else pd.DataFrame()
    endline_gr = df_filtered[df_filtered['Grade'] == 'Grade R']
    
    col1_gr, col2_gr = st.columns(2)
    
    # Baseline Grade R pie chart
    with col1_gr:
        if len(baseline_gr) > 0:
            above_baseline = len(baseline_gr[baseline_gr['Total cells correct - EGRA Letters'] > gradeR_threshold])
            below_baseline = len(baseline_gr) - above_baseline
            
            labels = [f'Above {gradeR_threshold}lpm', f'At or Below {gradeR_threshold}lpm']
            values = [above_baseline, below_baseline]
            colors = ['#22c55e', '#f87171']  # Lighter shades for Grade R
            
            fig_pie_baseline = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                textinfo='label+percent',
                textposition='auto'
            )])
            
            fig_pie_baseline.update_layout(
                title=f'Grade R Baseline (August)<br>Total: {len(baseline_gr):,} children',
                showlegend=False,
                height=400,
                margin=dict(t=80, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig_pie_baseline, use_container_width=True)
        else:
            st.warning("No Grade R baseline data available")
    
    # Endline Grade R pie chart
    with col2_gr:
        if len(endline_gr) > 0:
            above_endline = len(endline_gr[endline_gr['Total cells correct - EGRA Letters'] > gradeR_threshold])
            below_endline = len(endline_gr) - above_endline
            
            labels = [f'Above {gradeR_threshold}lpm', f'At or Below {gradeR_threshold}lpm']
            values = [above_endline, below_endline]
            colors = ['#22c55e', '#f87171']  # Lighter shades for Grade R
            
            fig_pie_endline = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                textinfo='label+percent',
                textposition='auto'
            )])
            
            fig_pie_endline.update_layout(
                title=f'Grade R Endline (Oct)<br>Total: {len(endline_gr):,} children',
                showlegend=False,
                height=400,
                margin=dict(t=80, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig_pie_endline, use_container_width=True)
        else:
            st.warning("No Grade R endline data available")
    
    st.divider()
    
    # Grade R Zero Letter Learners
    st.subheader("📊 Grade R: Zero Letter Learners (Baseline vs Endline)")
    
    col1_gr_zero, col2_gr_zero = st.columns(2)
    
    # Baseline Grade R zero learners
    with col1_gr_zero:
        if len(baseline_gr) > 0:
            zero_learners = len(baseline_gr[baseline_gr['Total cells correct - EGRA Letters'] == 0])
            non_zero_learners = len(baseline_gr) - zero_learners
            
            labels = ['Zero Letter Learners', '1+ Letters']
            values = [zero_learners, non_zero_learners]
            colors = ['#ef4444', '#10b981']  # Red for zero, green for 1+
            
            fig_pie_zero_baseline = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                textinfo='label+percent',
                textposition='auto'
            )])
            
            fig_pie_zero_baseline.update_layout(
                title=f'Grade R Baseline (August)<br>Total: {len(baseline_gr):,} children',
                showlegend=False,
                height=400,
                margin=dict(t=80, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig_pie_zero_baseline, use_container_width=True)
        else:
            st.warning("No Grade R baseline data available")
    
    # Endline Grade R zero learners
    with col2_gr_zero:
        if len(endline_gr) > 0:
            zero_learners = len(endline_gr[endline_gr['Total cells correct - EGRA Letters'] == 0])
            non_zero_learners = len(endline_gr) - zero_learners
            
            labels = ['Zero Letter Learners', '1+ Letters']
            values = [zero_learners, non_zero_learners]
            colors = ['#ef4444', '#10b981']  # Red for zero, green for 1+
            
            fig_pie_zero_endline = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                textinfo='label+percent',
                textposition='auto'
            )])
            
            fig_pie_zero_endline.update_layout(
                title=f'Grade R Endline (Oct)<br>Total: {len(endline_gr):,} children',
                showlegend=False,
                height=400,
                margin=dict(t=80, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig_pie_zero_endline, use_container_width=True)
        else:
            st.warning("No Grade R endline data available")
    
    st.divider()
    
    # Grade 1 Zero Letter Learners
    st.subheader("📊 Grade 1: Zero Letter Learners (Baseline vs Endline)")
    
    col1_g1_zero, col2_g1_zero = st.columns(2)
    
    # Baseline Grade 1 zero learners
    with col1_g1_zero:
        if len(baseline_g1) > 0:
            zero_learners = len(baseline_g1[baseline_g1['Total cells correct - EGRA Letters'] == 0])
            non_zero_learners = len(baseline_g1) - zero_learners
            
            labels = ['Zero Letter Learners', '1+ Letters']
            values = [zero_learners, non_zero_learners]
            colors = ['#ef4444', '#10b981']  # Red for zero, green for 1+
            
            fig_pie_zero_baseline = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                textinfo='label+percent',
                textposition='auto'
            )])
            
            fig_pie_zero_baseline.update_layout(
                title=f'Grade 1 Baseline (August)<br>Total: {len(baseline_g1):,} children',
                showlegend=False,
                height=400,
                margin=dict(t=80, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig_pie_zero_baseline, use_container_width=True)
        else:
            st.warning("No Grade 1 baseline data available")
    
    # Endline Grade 1 zero learners
    with col2_g1_zero:
        if len(endline_g1) > 0:
            zero_learners = len(endline_g1[endline_g1['Total cells correct - EGRA Letters'] == 0])
            non_zero_learners = len(endline_g1) - zero_learners
            
            labels = ['Zero Letter Learners', '1+ Letters']
            values = [zero_learners, non_zero_learners]
            colors = ['#ef4444', '#10b981']  # Red for zero, green for 1+
            
            fig_pie_zero_endline = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                textinfo='label+percent',
                textposition='auto'
            )])
            
            fig_pie_zero_endline.update_layout(
                title=f'Grade 1 Endline (Oct)<br>Total: {len(endline_g1):,} children',
                showlegend=False,
                height=400,
                margin=dict(t=80, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig_pie_zero_endline, use_container_width=True)
        else:
            st.warning("No Grade 1 endline data available")
    
    st.divider()
    
    # Session cohort distribution
    st.subheader("📈 Session Cohort Distribution")
    
    cohort_counts = df_filtered[df_filtered['cohort_session_range'] != ''].groupby('cohort_session_range').size().reset_index(name='count')
    cohort_counts = cohort_counts[cohort_counts['cohort_session_range'].notna()]
    
    if not cohort_counts.empty:
        # Sort by cohort order
        cohort_order = get_cohort_order()
        cohort_counts['cohort_session_range'] = pd.Categorical(
            cohort_counts['cohort_session_range'], 
            categories=cohort_order, 
            ordered=True
        )
        cohort_counts = cohort_counts.sort_values('cohort_session_range')
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Bar chart
            fig = px.bar(cohort_counts, x='cohort_session_range', y='count',
                        title='Distribution of Assessments by Session Cohort',
                        labels={'cohort_session_range': 'Session Cohort', 'count': 'Number of Assessments'},
                        color='count', color_continuous_scale='Blues')
            fig.update_traces(text=cohort_counts['count'], textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Pie chart
            fig_pie = px.pie(cohort_counts, values='count', names='cohort_session_range',
                           title='Cohort Percentage Distribution')
            st.plotly_chart(fig_pie, use_container_width=True)
    
    st.divider()
    
    # Grade and Language breakdown (only show if All Grades selected)
    if grade_filter == 'All Grades':
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👶 By Grade")
            grade_counts = df_filtered.groupby('Grade').size().reset_index(name='count')
            grade_order = ['Grade R', 'Grade 1', 'Grade 2']
            grade_counts['Grade'] = pd.Categorical(grade_counts['Grade'], categories=grade_order, ordered=True)
            grade_counts = grade_counts.sort_values('Grade')
            
            fig = px.bar(grade_counts, x='Grade', y='count', 
                        color='Grade',
                        title='Assessments by Grade',
                        text='count')
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🗣️ By Language")
            language_counts = df_filtered.groupby('Language').size().reset_index(name='count')
            
            fig = px.bar(language_counts, x='Language', y='count',
                        color='Language',
                        title='Assessments by Language',
                        text='count')
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # EGRA Scores by Grade
    st.subheader("📈 EGRA Scores by Grade")
    
    col_title, col_toggle = st.columns([3, 1])
    with col_toggle:
        use_mean_grade = st.toggle("📊 Show Mean", value=False, key="overview_grade_mean_toggle")
    
    stat_method = 'mean' if use_mean_grade else 'median'
    stat_label = 'Mean' if use_mean_grade else 'Median'
    
    agg_results = df_filtered.groupby('Grade').agg({
        'First Name': 'count',
        'Total cells correct - EGRA Letters': stat_method
    }).reset_index()
    
    fig = px.bar(agg_results, x='Grade', y='Total cells correct - EGRA Letters', color='Grade',
                 category_orders={'Grade': ['Grade R', 'Grade 1', 'Grade 2']},
                 title=f'{stat_label} EGRA Letter Scores by Grade')
    fig.update_yaxes(title=f'{stat_label} Correct Letters')
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # EGRA Scores by Language (only show if All Grades selected)
    if grade_filter == 'All Grades':
        st.subheader("🗣️ EGRA Scores by Language")
        
        col_title2, col_toggle2 = st.columns([3, 1])
        with col_toggle2:
            use_mean_language = st.toggle("📊 Show Mean", value=False, key="overview_language_mean_toggle")
        
        stat_method = 'mean' if use_mean_language else 'median'
        stat_label = 'Mean' if use_mean_language else 'Median'
        
        agg_results = df_filtered.groupby(['Language', 'Grade']).agg({
            'First Name': 'count',
            'Total cells correct - EGRA Letters': stat_method
        }).reset_index()
        
        fig = px.bar(agg_results, x='Language', y='Total cells correct - EGRA Letters', color='Grade', barmode='group',
                     category_orders={'Grade': ['Grade R', 'Grade 1', 'Grade 2']},
                     title=f'{stat_label} EGRA Letter Scores by Language')
        fig.update_yaxes(title=f'{stat_label} Correct Letters')
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
    
    # Average EGRA Scores by Data Collector
    st.subheader("📋 Average EGRA Scores by Data Collector")
    
    # Grade selector for data collector chart
    if grade_filter == 'All Grades':
        grade_options = ['Grade R', 'Grade 1', 'Grade 2']
        selected_grade_dc = st.selectbox('Select Grade', grade_options, key='overview_grade_selector_dc')
        filtered_df_dc = df[df['Grade'] == selected_grade_dc]
    else:
        filtered_df_dc = df_filtered
    
    # Group by 'Collected By' and calculate mean and count
    collector_stats = filtered_df_dc.groupby('Collected By').agg({
        'Total cells correct - EGRA Letters': 'mean',
        'First Name': 'count'
    }).reset_index()
    
    collector_stats = collector_stats.rename(columns={
        'Total cells correct - EGRA Letters': 'Mean_Score',
        'First Name': 'Count'
    })
    
    collector_stats = collector_stats.sort_values('Mean_Score', ascending=False)
    
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
    
    fig.update_traces(
        text=[f'n={count}' for count in collector_stats['Count']],
        textposition='outside'
    )
    
    fig.update_xaxes(tickangle=45, categoryorder='total descending')
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Number of Children Assessed by Data Collector
    st.subheader("📊 Number of Children Assessed by Data Collector")
    
    # Grade selector for assessment count chart
    if grade_filter == 'All Grades':
        grade_options_count = ['Grade R', 'Grade 1', 'Grade 2']
        selected_grade_count = st.selectbox('Select Grade', grade_options_count, key='overview_grade_count_selector')
        filtered_df_count = df[df['Grade'] == selected_grade_count]
    else:
        filtered_df_count = df_filtered
    
    # Group by 'Collected By' and count records
    collector_counts = filtered_df_count.groupby('Collected By').agg({
        'First Name': 'count'
    }).reset_index()
    
    collector_counts = collector_counts.rename(columns={
        'First Name': 'Count'
    })
    
    collector_counts = collector_counts.sort_values('Count', ascending=False)
    
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
    
    fig_count.update_traces(
        text=collector_counts['Count'],
        textposition='outside'
    )
    
    fig_count.update_xaxes(tickangle=45, categoryorder='total descending')
    st.plotly_chart(fig_count, use_container_width=True)
    
    st.divider()
    
    # Grade 2 Benchmark Comparison
    st.subheader("🎯 Grade 2: Baseline vs Endline Benchmark Achievement")
    
    col_slider_g2 = st.columns([3, 1])
    with col_slider_g2[1]:
        grade2_threshold = st.slider("Grade 2 Benchmark (LPM)", min_value=20, max_value=50, value=40, step=5, key="grade2_benchmark_slider")
    
    # Get Grade 2 data for baseline and endline
    baseline_g2 = baseline_df[baseline_df['Grade'] == 'Grade 2'] if not baseline_df.empty else pd.DataFrame()
    endline_g2 = df_filtered[df_filtered['Grade'] == 'Grade 2']
    
    col1_g2, col2_g2 = st.columns(2)
    
    # Baseline Grade 2 pie chart
    with col1_g2:
        if len(baseline_g2) > 0:
            above_baseline = len(baseline_g2[baseline_g2['Total cells correct - EGRA Letters'] > grade2_threshold])
            below_baseline = len(baseline_g2) - above_baseline
            
            labels = [f'Above {grade2_threshold}lpm', f'At or Below {grade2_threshold}lpm']
            values = [above_baseline, below_baseline]
            colors = ['#00cc44', '#ff4444']
            
            fig_pie_baseline = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                textinfo='label+percent',
                textposition='auto'
            )])
            
            fig_pie_baseline.update_layout(
                title=f'Grade 2 Baseline (August)<br>Total: {len(baseline_g2):,} children',
                showlegend=False,
                height=400,
                margin=dict(t=80, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig_pie_baseline, use_container_width=True)
        else:
            st.warning("No Grade 2 baseline data available")
    
    # Endline Grade 2 pie chart
    with col2_g2:
        if len(endline_g2) > 0:
            above_endline = len(endline_g2[endline_g2['Total cells correct - EGRA Letters'] > grade2_threshold])
            below_endline = len(endline_g2) - above_endline
            
            labels = [f'Above {grade2_threshold}lpm', f'At or Below {grade2_threshold}lpm']
            values = [above_endline, below_endline]
            colors = ['#00cc44', '#ff4444']
            
            fig_pie_endline = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                marker_colors=colors,
                textinfo='label+percent',
                textposition='auto'
            )])
            
            fig_pie_endline.update_layout(
                title=f'Grade 2 Endline (Oct)<br>Total: {len(endline_g2):,} children',
                showlegend=False,
                height=400,
                margin=dict(t=80, b=20, l=20, r=20)
            )
            
            st.plotly_chart(fig_pie_endline, use_container_width=True)
        else:
            st.warning("No Grade 2 endline data available")
    
    # LPM threshold slider for school breakdowns
    st.divider()
    col_title_breakdown, col_slider_breakdown = st.columns([3, 1])
    with col_title_breakdown:
        st.markdown("**School-Level Breakdown Threshold**")
    with col_slider_breakdown:
        lpm_threshold = st.slider("LPM", min_value=10, max_value=50, value=40, step=5, 
                                  key="school_breakdown_threshold")
    
    # School-Level Breakdown
    with st.expander("📊 School-Level Breakdown by Grade"):
        # Filter for Grade 1 and Grade 2 only (or selected grade)
        if grade_filter == 'All Grades':
            grade_1_2_df = df_filtered[df_filtered['Grade'].isin(['Grade 1', 'Grade 2'])]
        else:
            grade_1_2_df = df_filtered.copy()
        
        if len(grade_1_2_df) > 0:
            school_summary = []
            
            # Determine which grades to analyze
            if grade_filter == 'All Grades':
                grades_to_analyze = ['Grade 1', 'Grade 2']
            else:
                grades_to_analyze = [grade_filter]
            
            for school in grade_1_2_df['Program Name'].unique():
                for grade in grades_to_analyze:
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
                
                # Convert percentage to numeric for sorting
                summary_df['% Above Threshold Numeric'] = summary_df['% Above Threshold'].str.rstrip('%').astype(float)
                summary_df = summary_df.sort_values('% Above Threshold Numeric', ascending=False)
                summary_df = summary_df.drop('% Above Threshold Numeric', axis=1)
                
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                # Summary statistics
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
            st.warning("No data available for selected grade(s)")
    
    # Grade 1 Only Breakdown (only show if All Grades or Grade 1 selected)
    if grade_filter in ['All Grades', 'Grade 1']:
        with st.expander("📊 Grade 1 Only - School Breakdown"):
            grade_1_df = df[df['Grade'] == 'Grade 1']
            
            if len(grade_1_df) > 0:
                grade_1_summary = []
                
                for school in grade_1_df['Program Name'].unique():
                    school_data = grade_1_df[grade_1_df['Program Name'] == school]
                    
                    if len(school_data) > 0:
                        above_count = len(school_data[school_data['Total cells correct - EGRA Letters'] > lpm_threshold])
                        total_count = len(school_data)
                        below_count = total_count - above_count
                        percentage_above = (above_count / total_count * 100) if total_count > 0 else 0
                        
                        grade_1_summary.append({
                            'School': school,
                            'Total Children': total_count,
                            f'Above {lpm_threshold}lpm': above_count,
                            f'At/Below {lpm_threshold}lpm': below_count,
                            '% Above Threshold': percentage_above
                        })
                
                if grade_1_summary:
                    grade_1_df_summary = pd.DataFrame(grade_1_summary)
                    grade_1_df_summary = grade_1_df_summary.sort_values('% Above Threshold', ascending=False)
                    grade_1_df_summary['% Above Threshold'] = grade_1_df_summary['% Above Threshold'].apply(lambda x: f"{x:.1f}%")
                    
                    st.dataframe(grade_1_df_summary, use_container_width=True, hide_index=True)
                    
                    # Grade 1 Summary statistics
                    st.write("**Grade 1 Summary:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Grade 1 Schools", len(grade_1_summary))
                    with col2:
                        total_children_g1 = sum([s['Total Children'] for s in grade_1_summary])
                        st.metric("Total Grade 1 Children", total_children_g1)
                    with col3:
                        total_above_g1 = sum([s[f'Above {lpm_threshold}lpm'] for s in grade_1_summary])
                        overall_pct_g1 = (total_above_g1 / total_children_g1 * 100) if total_children_g1 > 0 else 0
                        st.metric("Grade 1 % Above Threshold", f"{overall_pct_g1:.1f}%")
                else:
                    st.warning("No Grade 1 data available")
            else:
                st.warning("No Grade 1 data available")
    
    st.divider()
    
    # Flag breakdown - MOVED TO BOTTOM
    st.subheader("🚩 Quality Flag Breakdown")
    col1, col2, col3 = st.columns(3)
    
    moving_fast = df_filtered['flag_moving_too_fast'].sum()
    same_letter = df_filtered['flag_same_letter_groups'].sum()
    both_flags = df_filtered['Both Flags'].sum()
    
    with col1:
        pct = (moving_fast/len(df_filtered)*100) if len(df_filtered) > 0 else 0
        st.metric("Moving Too Fast", f"{moving_fast:,}", 
                 delta=f"{pct:.1f}%", delta_color="off")
    with col2:
        pct = (same_letter/len(df_filtered)*100) if len(df_filtered) > 0 else 0
        st.metric("Same Letter Groups", f"{same_letter:,}", 
                 delta=f"{pct:.1f}%", delta_color="off")
    with col3:
        pct = (both_flags/len(df_filtered)*100) if len(df_filtered) > 0 else 0
        st.metric("Both Flags", f"{both_flags:,}", 
                 delta=f"{pct:.1f}%", delta_color="off")

def render_cohort_performance_tab(df):
    """Render cohort performance analysis"""
    st.header("🎯 Cohort Performance Analysis")
    st.markdown("**Key Question:** Do more sessions lead to better EGRA performance?")
    
    # Grade filter at the top
    col_filter, col_toggle = st.columns([1, 3])
    with col_filter:
        grade_filter = st.selectbox(
            "Filter by Grade",
            options=['All Grades', 'Grade R', 'Grade 1', 'Grade 2'],
            key='cohort_grade_filter'
        )
    
    # Apply grade filter
    if grade_filter != 'All Grades':
        df_filtered = df[df['Grade'] == grade_filter].copy()
        st.info(f"Analyzing {len(df_filtered):,} assessments for {grade_filter}")
    else:
        df_filtered = df.copy()
    
    # Filter to only assessments with cohort data
    df_cohorts = df_filtered[df_filtered['cohort_session_range'].notna() & (df_filtered['cohort_session_range'] != '')].copy()
    
    if df_cohorts.empty:
        st.warning(f"No cohort data available for {grade_filter if grade_filter != 'All Grades' else 'analysis'}")
        return
    
    # Statistical method toggle
    with col_toggle:
        use_mean = st.toggle("📊 Show Mean (instead of Median)", value=False, key="cohort_mean_toggle")
    stat_method = 'mean' if use_mean else 'median'
    stat_label = 'Mean' if use_mean else 'Median'
    
    st.divider()
    
    # Overall performance by cohort
    st.subheader(f"{stat_label} EGRA Scores by Session Cohort")
    
    cohort_order = get_cohort_order()
    df_cohorts['cohort_session_range'] = pd.Categorical(
        df_cohorts['cohort_session_range'], 
        categories=cohort_order, 
        ordered=True
    )
    
    cohort_stats = df_cohorts.groupby('cohort_session_range').agg({
        'Total cells correct - EGRA Letters': [stat_method, 'count']
    }).reset_index()
    cohort_stats.columns = ['Cohort', 'Score', 'Count']
    cohort_stats = cohort_stats.sort_values('Cohort')
    
    fig = px.bar(cohort_stats, x='Cohort', y='Score',
                title=f'{stat_label} EGRA Letter Scores by Session Cohort',
                labels={'Score': f'{stat_label} Correct Letters', 'Cohort': 'Session Cohort'},
                color='Score', color_continuous_scale='Viridis')
    fig.update_traces(text=[f"{score:.1f}<br>n={count}" for score, count in 
                           zip(cohort_stats['Score'], cohort_stats['Count'])],
                     textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
    
    # Key insight
    if len(cohort_stats) > 1:
        lowest_cohort = cohort_stats.iloc[0]
        highest_cohort = cohort_stats.iloc[-1]
        diff = highest_cohort['Score'] - lowest_cohort['Score']
        pct_change = (diff / lowest_cohort['Score'] * 100) if lowest_cohort['Score'] > 0 else 0
        
        st.warning(f"💡 **Warning:** We need to make sure Grade 1's excluded from the programme because they knew more than 30 letter sounds on baseline are not included in the zero session bucket thus skewing results upwards for that group. Awaiting on data from Teampact in order to isolate these kids.")
    
    st.divider()
    
    # Performance by cohort AND grade (only show if All Grades selected)
    if grade_filter == 'All Grades':
        st.subheader(f"{stat_label} EGRA Scores by Cohort & Grade")
        
        grade_cohort_stats = df_cohorts.groupby(['cohort_session_range', 'Grade']).agg({
            'Total cells correct - EGRA Letters': stat_method
        }).reset_index()
        grade_cohort_stats.columns = ['Cohort', 'Grade', 'Score']
        
        # Order grades
        grade_order = ['Grade R', 'Grade 1', 'Grade 2']
        grade_cohort_stats['Grade'] = pd.Categorical(grade_cohort_stats['Grade'], 
                                                      categories=grade_order, ordered=True)
        grade_cohort_stats = grade_cohort_stats.sort_values(['Cohort', 'Grade'])
        
        fig = px.bar(grade_cohort_stats, x='Cohort', y='Score', color='Grade', barmode='group',
                    category_orders={'Grade': grade_order},
                    title=f'{stat_label} EGRA Scores by Session Cohort and Grade',
                    labels={'Score': f'{stat_label} Correct Letters'})
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
    
    # Distribution boxplots
    st.subheader("Score Distribution by Cohort (Boxplot)")
    st.markdown("*Shows the spread and variability of scores within each cohort*")
    
    fig = px.box(df_cohorts, x='cohort_session_range', y='Total cells correct - EGRA Letters',
                category_orders={'cohort_session_range': cohort_order},
                title='EGRA Score Distribution by Session Cohort',
                labels={'cohort_session_range': 'Session Cohort', 
                       'Total cells correct - EGRA Letters': 'EGRA Letters Correct'})
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Benchmark analysis
    st.subheader("📊 Percentage Above Benchmark by Cohort")
    
    benchmark = st.slider("Set LPM Benchmark", min_value=20, max_value=50, value=40, step=5, 
                         key="cohort_benchmark_slider")
    
    # Calculate percentage above benchmark for each cohort
    benchmark_stats = []
    for cohort in cohort_order:
        if cohort == '':
            continue
        cohort_data = df_cohorts[df_cohorts['cohort_session_range'] == cohort]
        if len(cohort_data) > 0:
            above = (cohort_data['Total cells correct - EGRA Letters'] > benchmark).sum()
            total = len(cohort_data)
            pct_above = (above / total * 100) if total > 0 else 0
            benchmark_stats.append({
                'Cohort': cohort,
                'Above Benchmark': above,
                'Total': total,
                'Percentage': pct_above
            })
    
    if benchmark_stats:
        benchmark_df = pd.DataFrame(benchmark_stats)
        
        fig = px.bar(benchmark_df, x='Cohort', y='Percentage',
                    title=f'Percentage of Students Above {benchmark} LPM by Cohort',
                    labels={'Percentage': f'% Above {benchmark} LPM'},
                    color='Percentage', color_continuous_scale='RdYlGn')
        fig.update_traces(text=[f"{pct:.1f}%<br>({above}/{total})" 
                               for pct, above, total in 
                               zip(benchmark_df['Percentage'], benchmark_df['Above Benchmark'], 
                                   benchmark_df['Total'])],
                         textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

def render_flag_impact_tab(df):
    """Render quality flag impact analysis"""
    st.header("🚩 Quality Flag Impact Analysis")
    st.markdown("**Key Question:** How do flagged groups perform vs non-flagged?")
    
    # Grade filter and toggle
    col_filter, col_toggle = st.columns([1, 3])
    with col_filter:
        grade_filter = st.selectbox(
            "Filter by Grade",
            options=['All Grades', 'Grade R', 'Grade 1', 'Grade 2'],
            key='flag_grade_filter'
        )
    
    # Apply grade filter
    if grade_filter != 'All Grades':
        df_filtered = df[df['Grade'] == grade_filter].copy()
        st.info(f"Analyzing {len(df_filtered):,} assessments for {grade_filter}")
    else:
        df_filtered = df.copy()
    
    # Statistical method toggle
    with col_toggle:
        use_mean = st.toggle("📊 Show Mean (instead of Median)", value=False, key="flag_mean_toggle")
    stat_method = 'mean' if use_mean else 'median'
    stat_label = 'Mean' if use_mean else 'Median'
    
    st.divider()
    
    # Flag 1: Moving Too Fast
    st.subheader("⚡ Moving Too Fast Flag Impact")
    
    col1, col2 = st.columns(2)
    
    with col1:
        flagged = df_filtered[df_filtered['flag_moving_too_fast'] == True]['Total cells correct - EGRA Letters']
        not_flagged = df_filtered[df_filtered['flag_moving_too_fast'] == False]['Total cells correct - EGRA Letters']
        
        flagged_stat = flagged.mean() if use_mean else flagged.median()
        not_flagged_stat = not_flagged.mean() if use_mean else not_flagged.median()
        
        st.metric("Flagged Groups", f"{flagged_stat:.1f} letters", 
                 delta=f"{len(flagged):,} assessments")
        st.metric("Non-Flagged Groups", f"{not_flagged_stat:.1f} letters",
                 delta=f"{len(not_flagged):,} assessments")
        
        diff = not_flagged_stat - flagged_stat
        if diff > 0:
            st.success(f"✅ Non-flagged groups score {diff:.1f} letters higher")
        else:
            st.warning(f"⚠️ Flagged groups score {abs(diff):.1f} letters higher (unexpected)")
    
    with col2:
        # Comparison bar chart
        comparison_data = pd.DataFrame({
            'Group': ['Flagged (Moving Fast)', 'Not Flagged'],
            'Score': [flagged_stat, not_flagged_stat],
            'Count': [len(flagged), len(not_flagged)]
        })
        
        fig = px.bar(comparison_data, x='Group', y='Score',
                    title=f'{stat_label} EGRA Scores: Flagged vs Not Flagged (Moving Too Fast)',
                    color='Group',
                    color_discrete_map={'Flagged (Moving Fast)': '#ff4444', 
                                       'Not Flagged': '#00cc44'})
        fig.update_traces(text=[f"{score:.1f}<br>n={count:,}" 
                               for score, count in zip(comparison_data['Score'], comparison_data['Count'])],
                         textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    # Distribution comparison
    fig = px.histogram(df_filtered, x='Total cells correct - EGRA Letters', 
                      color='flag_moving_too_fast',
                      barmode='overlay',
                      title='Score Distribution: Moving Too Fast Flag',
                      labels={'flag_moving_too_fast': 'Flagged?',
                             'Total cells correct - EGRA Letters': 'EGRA Letters Correct'},
                      color_discrete_map={True: '#ff4444', False: '#00cc44'},
                      opacity=0.7)
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Flag 2: Same Letter Groups
    st.subheader("🔄 Same Letter Groups Flag Impact")
    
    col1, col2 = st.columns(2)
    
    with col1:
        flagged = df_filtered[df_filtered['flag_same_letter_groups'] == True]['Total cells correct - EGRA Letters']
        not_flagged = df_filtered[df_filtered['flag_same_letter_groups'] == False]['Total cells correct - EGRA Letters']
        
        flagged_stat = flagged.mean() if use_mean else flagged.median()
        not_flagged_stat = not_flagged.mean() if use_mean else not_flagged.median()
        
        st.metric("Flagged Groups", f"{flagged_stat:.1f} letters",
                 delta=f"{len(flagged):,} assessments")
        st.metric("Non-Flagged Groups", f"{not_flagged_stat:.1f} letters",
                 delta=f"{len(not_flagged):,} assessments")
        
        diff = not_flagged_stat - flagged_stat
        if diff > 0:
            st.success(f"✅ Non-flagged groups score {diff:.1f} letters higher")
        else:
            st.warning(f"⚠️ Flagged groups score {abs(diff):.1f} letters higher (unexpected)")
    
    with col2:
        # Comparison bar chart
        comparison_data = pd.DataFrame({
            'Group': ['Flagged (Same Letter)', 'Not Flagged'],
            'Score': [flagged_stat, not_flagged_stat],
            'Count': [len(flagged), len(not_flagged)]
        })
        
        fig = px.bar(comparison_data, x='Group', y='Score',
                    title=f'{stat_label} EGRA Scores: Flagged vs Not Flagged (Same Letter Groups)',
                    color='Group',
                    color_discrete_map={'Flagged (Same Letter)': '#ff4444', 
                                       'Not Flagged': '#00cc44'})
        fig.update_traces(text=[f"{score:.1f}<br>n={count:,}" 
                               for score, count in zip(comparison_data['Score'], comparison_data['Count'])],
                         textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    
    # Distribution comparison
    fig = px.histogram(df_filtered, x='Total cells correct - EGRA Letters', 
                      color='flag_same_letter_groups',
                      barmode='overlay',
                      title='Score Distribution: Same Letter Groups Flag',
                      labels={'flag_same_letter_groups': 'Flagged?',
                             'Total cells correct - EGRA Letters': 'EGRA Letters Correct'},
                      color_discrete_map={True: '#ff4444', False: '#00cc44'},
                      opacity=0.7)
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Combined flags analysis
    st.subheader("🚩🚩 Both Flags Combined")
    
    both_flags = df_filtered[df_filtered['Both Flags'] == True]['Total cells correct - EGRA Letters']
    one_flag = df_filtered[(df_filtered['Has Quality Flags'] == True) & (df_filtered['Both Flags'] == False)]['Total cells correct - EGRA Letters']
    no_flags = df_filtered[df_filtered['Has Quality Flags'] == False]['Total cells correct - EGRA Letters']
    
    both_stat = both_flags.mean() if use_mean else both_flags.median()
    one_stat = one_flag.mean() if use_mean else one_flag.median()
    no_stat = no_flags.mean() if use_mean else no_flags.median()
    
    comparison_data = pd.DataFrame({
        'Group': ['Both Flags', 'One Flag', 'No Flags'],
        'Score': [both_stat, one_stat, no_stat],
        'Count': [len(both_flags), len(one_flag), len(no_flags)]
    })
    
    fig = px.bar(comparison_data, x='Group', y='Score',
                title=f'{stat_label} EGRA Scores by Flag Status',
                color='Group',
                color_discrete_sequence=['#cc0000', '#ff9900', '#00cc44'])
    fig.update_traces(text=[f"{score:.1f}<br>n={count:,}" 
                           for score, count in zip(comparison_data['Score'], comparison_data['Count'])],
                     textposition='outside')
    st.plotly_chart(fig, use_container_width=True)

def render_cross_analysis_tab(df):
    """Render cross-analysis of cohorts and flags"""
    st.header("🔬 Cross-Analysis & Correlations")
    st.markdown("**Key Question:** How do cohorts and flags interact?")
    
    # Grade filter and toggle
    col_filter, col_toggle = st.columns([1, 3])
    with col_filter:
        grade_filter = st.selectbox(
            "Filter by Grade",
            options=['All Grades', 'Grade R', 'Grade 1', 'Grade 2'],
            key='cross_grade_filter'
        )
    
    # Apply grade filter
    if grade_filter != 'All Grades':
        df_filtered = df[df['Grade'] == grade_filter].copy()
        st.info(f"Analyzing {len(df_filtered):,} assessments for {grade_filter}")
    else:
        df_filtered = df.copy()
    
    # Filter to assessments with cohort data
    df_cohorts = df_filtered[df_filtered['cohort_session_range'].notna() & (df_filtered['cohort_session_range'] != '')].copy()
    
    if df_cohorts.empty:
        st.warning(f"No cohort data available for {grade_filter if grade_filter != 'All Grades' else 'cross-analysis'}")
        return
    
    # Statistical method toggle
    with col_toggle:
        use_mean = st.toggle("📊 Show Mean (instead of Median)", value=False, key="cross_mean_toggle")
    stat_method = 'mean' if use_mean else 'median'
    stat_label = 'Mean' if use_mean else 'Median'
    
    st.divider()
    
    # Heatmap: Cohort × Flag Status
    st.subheader(f"{stat_label} Scores by Cohort & Flag Status")
    
    # Create flag status categories
    df_cohorts['Flag Status'] = 'No Flags'
    df_cohorts.loc[df_cohorts['Both Flags'], 'Flag Status'] = 'Both Flags'
    df_cohorts.loc[(df_cohorts['Has Quality Flags']) & (~df_cohorts['Both Flags']), 'Flag Status'] = 'One Flag'
    
    cohort_flag_stats = df_cohorts.groupby(['cohort_session_range', 'Flag Status']).agg({
        'Total cells correct - EGRA Letters': [stat_method, 'count']
    }).reset_index()
    cohort_flag_stats.columns = ['Cohort', 'Flag Status', 'Score', 'Count']
    
    # Pivot for heatmap
    heatmap_data = cohort_flag_stats.pivot(index='Flag Status', columns='Cohort', values='Score')
    
    # Order columns
    cohort_order = get_cohort_order()
    heatmap_data = heatmap_data[[col for col in cohort_order if col in heatmap_data.columns]]
    
    fig = px.imshow(heatmap_data, 
                    text_auto='.1f',
                    aspect='auto',
                    color_continuous_scale='RdYlGn',
                    title=f'{stat_label} EGRA Scores: Cohort × Flag Status',
                    labels={'x': 'Session Cohort', 'y': 'Flag Status', 'color': f'{stat_label} Score'})
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Scatter plot: Sessions vs Performance with flags
    st.subheader("Session Count vs EGRA Performance")
    st.markdown("*Each point represents one assessment, colored by flag status*")
    
    fig = px.scatter(df_cohorts, 
                    x='session_count_total', 
                    y='Total cells correct - EGRA Letters',
                    color='Flag Status',
                    color_discrete_map={'No Flags': '#00cc44', 'One Flag': '#ff9900', 'Both Flags': '#cc0000'},
                    title='Session Count vs EGRA Score (with Flag Status)',
                    labels={'session_count_total': 'Total Sessions',
                           'Total cells correct - EGRA Letters': 'EGRA Letters Correct'},
                    opacity=0.6,
                    trendline='ols')  # Add trendline
    st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Session recency analysis
    st.subheader("Session Recency: Does Recent Activity Matter?")
    
    col1, col2, col3 = st.columns(3)
    
    # Filter to those with session data
    df_sessions = df_cohorts[df_cohorts['session_count_total'] > 0].copy()
    
    with col1:
        st.markdown("**30-Day Sessions**")
        corr_30 = df_sessions['session_count_30_days'].corr(df_sessions['Total cells correct - EGRA Letters'])
        st.metric("Correlation with Score", f"{corr_30:.3f}")
        
    with col2:
        st.markdown("**90-Day Sessions**")
        corr_90 = df_sessions['session_count_90_days'].corr(df_sessions['Total cells correct - EGRA Letters'])
        st.metric("Correlation with Score", f"{corr_90:.3f}")
        
    with col3:
        st.markdown("**Total Sessions**")
        corr_total = df_sessions['session_count_total'].corr(df_sessions['Total cells correct - EGRA Letters'])
        st.metric("Correlation with Score", f"{corr_total:.3f}")
    
    st.info("💡 Correlation values closer to 1.0 indicate stronger positive relationship between sessions and performance")
    
    st.divider()
    
    # Correlation matrix
    st.subheader("📊 Correlation Matrix")
    
    # Select numeric columns for correlation
    numeric_cols = ['Total cells correct - EGRA Letters', 'session_count_total', 
                   'session_count_30_days', 'session_count_90_days']
    
    # Add flag columns as numeric (0/1)
    df_corr = df_sessions[numeric_cols].copy()
    df_corr['Moving Too Fast (flag)'] = df_sessions['flag_moving_too_fast'].astype(int)
    df_corr['Same Letter Groups (flag)'] = df_sessions['flag_same_letter_groups'].astype(int)
    
    # Calculate correlation matrix
    corr_matrix = df_corr.corr()
    
    # Rename for display
    corr_matrix.index = ['EGRA Score', 'Total Sessions', '30-Day Sessions', 
                        '90-Day Sessions', 'Moving Fast Flag', 'Same Letter Flag']
    corr_matrix.columns = corr_matrix.index
    
    fig = px.imshow(corr_matrix, 
                    text_auto='.2f',
                    aspect='auto',
                    color_continuous_scale='RdBu_r',
                    title='Correlation Matrix: Sessions, Flags, and Performance',
                    zmin=-1, zmax=1)
    st.plotly_chart(fig, use_container_width=True)

def render_school_ea_insights_tab(df):
    """Render school and EA level insights"""
    st.header("🏫 School & EA Level Insights")
    
    # Grade filter at the top
    col_filter, col_space = st.columns([1, 3])
    with col_filter:
        grade_filter = st.selectbox(
            "Filter by Grade",
            options=['All Grades', 'Grade R', 'Grade 1', 'Grade 2'],
            key='school_grade_filter'
        )
    
    # Apply grade filter
    if grade_filter != 'All Grades':
        df_filtered = df[df['Grade'] == grade_filter].copy()
        st.info(f"Analyzing {len(df_filtered):,} assessments for {grade_filter}")
    else:
        df_filtered = df.copy()
    
    st.divider()
    
    # Schools with most flags
    st.subheader("🚩 Schools with Most Quality Flags")
    
    school_flags = df_filtered.groupby('Program Name').agg({
        'flag_moving_too_fast': 'sum',
        'flag_same_letter_groups': 'sum',
        'Has Quality Flags': 'sum',
        'response_id': 'count',
        'Total cells correct - EGRA Letters': 'mean'
    }).reset_index()
    
    school_flags.columns = ['School', 'Moving Fast Count', 'Same Letter Count', 
                           'Total Flagged', 'Total Assessments', 'Mean Score']
    school_flags['Flag Rate %'] = (school_flags['Total Flagged'] / school_flags['Total Assessments'] * 100)
    school_flags = school_flags.sort_values('Flag Rate %', ascending=False)
    
    # Show top 15
    top_flagged = school_flags.head(15)
    
    fig = px.bar(top_flagged, x='School', y='Flag Rate %',
                title='Top 15 Schools by Quality Flag Rate',
                color='Mean Score',
                color_continuous_scale='RdYlGn',
                hover_data=['Total Assessments', 'Moving Fast Count', 'Same Letter Count'])
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Full table
    with st.expander("📋 View Full School Flag Data"):
        st.dataframe(school_flags, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # EA performance by cohort
    st.subheader("👨‍🏫 EA Performance Analysis")
    
    # Filter for EAs with sufficient data
    min_assessments = st.slider("Minimum assessments per EA", min_value=5, max_value=50, value=15, 
                                key="ea_min_assessments")
    
    ea_stats = df_filtered.groupby('Collected By').agg({
        'Total cells correct - EGRA Letters': ['mean', 'median', 'count'],
        'flag_moving_too_fast': 'sum',
        'flag_same_letter_groups': 'sum',
        'session_count_total': 'mean'
    }).reset_index()
    
    ea_stats.columns = ['EA', 'Mean Score', 'Median Score', 'Assessment Count',
                       'Moving Fast Flags', 'Same Letter Flags', 'Avg Sessions']
    
    # Filter by minimum assessments
    ea_stats = ea_stats[ea_stats['Assessment Count'] >= min_assessments]
    ea_stats = ea_stats.sort_values('Mean Score', ascending=False)
    
    # Top and bottom performers
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🌟 Top 10 Performing EAs**")
        top_eas = ea_stats.head(10)
        fig = px.bar(top_eas, x='EA', y='Mean Score',
                    color='Avg Sessions',
                    title='Top 10 EAs by Mean EGRA Score',
                    hover_data=['Assessment Count', 'Moving Fast Flags', 'Same Letter Flags'])
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("**⚠️ Bottom 10 Performing EAs**")
        bottom_eas = ea_stats.tail(10)
        fig = px.bar(bottom_eas, x='EA', y='Mean Score',
                    color='Avg Sessions',
                    title='Bottom 10 EAs by Mean EGRA Score',
                    hover_data=['Assessment Count', 'Moving Fast Flags', 'Same Letter Flags'])
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Full EA table
    with st.expander("📋 View Full EA Performance Data"):
        st.dataframe(ea_stats, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # Flag distribution by school
    st.subheader("🎯 Flag Distribution by School")
    
    # Create grouped bar chart
    school_flag_detail = df.groupby('Program Name').agg({
        'flag_moving_too_fast': ['sum', lambda x: (x.sum() / len(x) * 100)],
        'flag_same_letter_groups': ['sum', lambda x: (x.sum() / len(x) * 100)],
        'response_id': 'count'
    }).reset_index()
    
    school_flag_detail.columns = ['School', 'Moving Fast Count', 'Moving Fast %', 
                                  'Same Letter Count', 'Same Letter %', 'Total']
    
    # Filter for schools with minimum assessments
    school_flag_detail = school_flag_detail[school_flag_detail['Total'] >= 10]
    school_flag_detail = school_flag_detail.sort_values('Moving Fast %', ascending=False).head(15)
    
    # Reshape for grouped bar chart
    school_flag_melted = school_flag_detail.melt(
        id_vars=['School'], 
        value_vars=['Moving Fast %', 'Same Letter %'],
        var_name='Flag Type',
        value_name='Percentage'
    )
    
    fig = px.bar(school_flag_melted, x='School', y='Percentage', color='Flag Type',
                barmode='group',
                title='Flag Rates by School (Top 15 Schools)',
                labels={'Percentage': 'Flag Rate (%)'})
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

def render_data_explorer_tab(df):
    """Render interactive data explorer"""
    st.header("📈 Detailed Data Explorer")
    st.markdown("*Filter, search, and export assessment data*")
    
    st.divider()
    
    # Filter controls
    st.subheader("🔍 Filters")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        grade_filter = st.multiselect("Grade", 
                                     options=df['Grade'].dropna().unique().tolist(),
                                     default=None,
                                     key="explorer_grade")
    
    with col2:
        language_filter = st.multiselect("Language",
                                        options=df['Language'].dropna().unique().tolist(),
                                        default=None,
                                        key="explorer_language")
    
    with col3:
        cohort_filter = st.multiselect("Session Cohort",
                                      options=[c for c in get_cohort_order() if c != ''],
                                      default=None,
                                      key="explorer_cohort")
    
    with col4:
        flag_filter = st.multiselect("Quality Flags",
                                    options=['Moving Too Fast', 'Same Letter Groups', 'Both', 'None'],
                                    default=None,
                                    key="explorer_flags")
    
    # School and EA filters
    col5, col6 = st.columns(2)
    
    with col5:
        school_filter = st.multiselect("School",
                                      options=sorted(df['Program Name'].dropna().unique().tolist()),
                                      default=None,
                                      key="explorer_school")
    
    with col6:
        ea_filter = st.multiselect("EA/Collector",
                                  options=sorted(df['Collected By'].dropna().unique().tolist()),
                                  default=None,
                                  key="explorer_ea")
    
    # Apply filters
    filtered_df = df.copy()
    
    if grade_filter:
        filtered_df = filtered_df[filtered_df['Grade'].isin(grade_filter)]
    
    if language_filter:
        filtered_df = filtered_df[filtered_df['Language'].isin(language_filter)]
    
    if cohort_filter:
        filtered_df = filtered_df[filtered_df['cohort_session_range'].isin(cohort_filter)]
    
    if flag_filter:
        flag_conditions = []
        if 'Moving Too Fast' in flag_filter:
            flag_conditions.append(filtered_df['flag_moving_too_fast'] == True)
        if 'Same Letter Groups' in flag_filter:
            flag_conditions.append(filtered_df['flag_same_letter_groups'] == True)
        if 'Both' in flag_filter:
            flag_conditions.append(filtered_df['Both Flags'] == True)
        if 'None' in flag_filter:
            flag_conditions.append(filtered_df['Has Quality Flags'] == False)
        
        if flag_conditions:
            # Combine with OR
            combined_condition = flag_conditions[0]
            for condition in flag_conditions[1:]:
                combined_condition = combined_condition | condition
            filtered_df = filtered_df[combined_condition]
    
    if school_filter:
        filtered_df = filtered_df[filtered_df['Program Name'].isin(school_filter)]
    
    if ea_filter:
        filtered_df = filtered_df[filtered_df['Collected By'].isin(ea_filter)]
    
    st.divider()
    
    # Summary of filtered data
    st.subheader(f"📊 Filtered Results: {len(filtered_df):,} assessments")
    
    if len(filtered_df) > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            mean_score = filtered_df['Total cells correct - EGRA Letters'].mean()
            st.metric("Mean EGRA Score", f"{mean_score:.1f}")
        
        with col2:
            median_score = filtered_df['Total cells correct - EGRA Letters'].median()
            st.metric("Median EGRA Score", f"{median_score:.1f}")
        
        with col3:
            flagged_pct = (filtered_df['Has Quality Flags'].sum() / len(filtered_df) * 100)
            st.metric("% with Flags", f"{flagged_pct:.1f}%")
        
        with col4:
            mean_sessions = filtered_df['session_count_total'].mean()
            st.metric("Avg Sessions", f"{mean_sessions:.1f}")
        
        st.divider()
        
        # Display data table
        st.subheader("📋 Data Table")
        
        # Select columns to display
        display_columns = [
            'Participant Name', 'Grade', 'Language', 'Program Name', 'Collected By',
            'Total cells correct - EGRA Letters', 'cohort_session_range',
            'session_count_total', 'session_count_30_days', 'session_count_90_days',
            'flag_moving_too_fast', 'flag_same_letter_groups', 'Response Date'
        ]
        
        display_df = filtered_df[display_columns].copy()
        
        # Rename for clarity
        display_df = display_df.rename(columns={
            'Total cells correct - EGRA Letters': 'EGRA Score',
            'cohort_session_range': 'Cohort',
            'session_count_total': 'Total Sessions',
            'session_count_30_days': '30-Day Sessions',
            'session_count_90_days': '90-Day Sessions',
            'flag_moving_too_fast': 'Moving Fast?',
            'flag_same_letter_groups': 'Same Letter?'
        })
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Export buttons
        col_export1, col_export2 = st.columns(2)
        
        with col_export1:
            csv = display_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f'nmb_endline_filtered_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv',
            )
        
        with col_export2:
            json_data = display_df.to_json(orient='records', date_format='iso').encode('utf-8')
            st.download_button(
                label="📥 Download as JSON",
                data=json_data,
                file_name=f'nmb_endline_filtered_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                mime='application/json',
            )
        
        st.divider()
        
        # Grouped by School & Grade Table
        st.subheader("📊 Summary by School & Grade")
        
        # Load baseline data for comparison
        baseline_df = load_baseline_data()
        
        # Calculate baseline scores by school and grade
        baseline_scores = {}
        if not baseline_df.empty:
            baseline_grouped = baseline_df.groupby(['Program Name', 'Grade']).agg({
                'Total cells correct - EGRA Letters': 'median'
            }).reset_index()
            for _, row in baseline_grouped.iterrows():
                key = (row['Program Name'], row['Grade'])
                baseline_scores[key] = row['Total cells correct - EGRA Letters']
        
        # Group filtered data by School (Program Name) and Grade
        grouped_data = filtered_df.groupby(['Program Name', 'Grade']).agg({
            'Total cells correct - EGRA Letters': 'median',
            'session_count_total': 'median',
            'flag_moving_too_fast': 'sum',
            'flag_same_letter_groups': 'sum',
            'Collected By': lambda x: ', '.join(sorted(x.unique())),
            'cohort_session_range': lambda x: x.mode()[0] if len(x.mode()) > 0 else '',
            'Language': lambda x: ', '.join(sorted(x.unique())),
            'response_id': 'count'
        }).reset_index()
        
        # Rename columns
        grouped_data.columns = [
            'School Name', 'Grade', 'EGRA Endline (Median)', 'Total Sessions (Median)',
            'Moving Too Fast (Count)', 'Same Letter Groups (Count)', 
            'EA Names', 'Most Common Cohort', 'Languages', 'Total Assessments'
        ]
        
        # Add baseline scores
        grouped_data['EGRA Baseline (Median)'] = grouped_data.apply(
            lambda row: baseline_scores.get((row['School Name'], row['Grade']), None), 
            axis=1
        )
        
        # Calculate improvement
        grouped_data['Improvement'] = grouped_data['EGRA Endline (Median)'] - grouped_data['EGRA Baseline (Median)']
        
        # Reorder columns
        summary_df = grouped_data[[
            'School Name', 'Grade', 'EGRA Baseline (Median)', 'EGRA Endline (Median)', 
            'Improvement', 'Total Sessions (Median)', 'Moving Too Fast (Count)', 
            'Same Letter Groups (Count)', 'EA Names', 'Most Common Cohort', 
            'Languages', 'Total Assessments'
        ]]
        
        # Sort by School Name and Grade
        grade_order_map = {'Grade R': 0, 'Grade 1': 1, 'Grade 2': 2}
        summary_df['Grade_Order'] = summary_df['Grade'].map(grade_order_map)
        summary_df = summary_df.sort_values(['School Name', 'Grade_Order']).drop('Grade_Order', axis=1)
        
        # Display the table
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        
        # Export buttons for grouped data
        col_export3, col_export4 = st.columns(2)
        
        with col_export3:
            summary_csv = summary_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Summary as CSV",
                data=summary_csv,
                file_name=f'nmb_endline_summary_by_school_grade_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv',
                key='summary_csv_download'
            )
        
        with col_export4:
            summary_json = summary_df.to_json(orient='records', date_format='iso').encode('utf-8')
            st.download_button(
                label="📥 Download Summary as JSON",
                data=summary_json,
                file_name=f'nmb_endline_summary_by_school_grade_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                mime='application/json',
                key='summary_json_download'
            )
    else:
        st.warning("No assessments match the selected filters")

# Run the app
if __name__ == "__main__":
    display_nmb_endline_cohort_analysis()
else:
    display_nmb_endline_cohort_analysis()

