import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
from io import BytesIO
import plotly.io as pio
from data_utility_functions.data_manager import data_manager
from process_survey_cto_updated import process_egra_data
from data_loader import load_zazi_izandi_2025

# Page configuration
# st.set_page_config(layout="wide", page_title="School Reports")

def load_assessment_data():
    """Load and prepare assessment data for school reports - using 2025 data"""
    try:
        # Load 2025 EGRA data (same as midline_2025.py)
        df_full, df_ecd = load_zazi_izandi_2025()
        
        # Convert submission date (same as midline_2025.py)
        df_full['submission_date'] = pd.to_datetime(df_full['date'])
        
        # Split into baseline and midline based on submission date (same as midline_2025.py)
        baseline_cutoff = pd.Timestamp('2025-04-15')
        baseline_data = df_full[df_full['submission_date'] < baseline_cutoff].copy()
        midline_data = df_full[df_full['submission_date'] >= baseline_cutoff].copy()
        
        # Check if we have data
        if baseline_data.empty and midline_data.empty:
            st.warning("No 2025 data found in the datasets.")
            return None, None
        
        # Debug: Show available columns and data counts
        st.sidebar.info(f"Baseline assessments: {len(baseline_data)}")
        st.sidebar.info(f"Midline assessments: {len(midline_data)}")
        
        return baseline_data, midline_data
        
    except Exception as e:
        st.error(f"Error loading 2025 data: {e}")
        st.error("Please ensure the 2025 assessment data files are available.")
        return None, None

def calculate_school_stats(baseline_data, midline_data, school_name):
    """Calculate statistics for a specific school using exact column names from midline_2025.py"""
    
    # Filter data for the school using 'school_rep' column (same as midline_2025.py)
    school_baseline = baseline_data[baseline_data['school_rep'] == school_name] if baseline_data is not None else pd.DataFrame()
    school_midline = midline_data[midline_data['school_rep'] == school_name] if midline_data is not None else pd.DataFrame()
    
    stats = {
        'school_name': school_name,
        'reporting_period': 'Start of Year - Mid-Year 2025',
        'summary': {
            'total_tas': 0,
            'total_children': 0, 
            'total_classes': 0
        },
        'grade_r': {
            'baseline_score': 0,
            'midline_score': 0,
            'improvement': 0
        },
        'grade_1': {
            'baseline_score': 0,
            'midline_score': 0, 
            'improvement': 0
        }
    }
    
    if not school_baseline.empty:
        # Calculate summary stats using correct column names
        stats['summary']['total_children'] = len(school_baseline)
        
        # Use 'name_ta_rep' column for TAs (same as midline_2025.py)
        if 'name_ta_rep' in school_baseline.columns:
            stats['summary']['total_tas'] = school_baseline['name_ta_rep'].nunique()
                
        # Try different class column names  
        class_cols = ['Class', 'class', 'class_name', 'classroom']
        for col in class_cols:
            if col in school_baseline.columns:
                stats['summary']['total_classes'] = school_baseline[col].nunique()
                break
             
        # Calculate Grade R stats using 'grade_label' and 'letters_correct_a1' (same as midline_2025.py)
        grade_r_baseline = school_baseline[school_baseline['grade_label'] == 'Grade R']
        grade_r_midline = school_midline[school_midline['grade_label'] == 'Grade R']
        
        if not grade_r_baseline.empty and 'letters_correct_a1' in grade_r_baseline.columns:
            stats['grade_r']['baseline_score'] = grade_r_baseline['letters_correct_a1'].mean()
        if not grade_r_midline.empty and 'letters_correct_a1' in grade_r_midline.columns:
            stats['grade_r']['midline_score'] = grade_r_midline['letters_correct_a1'].mean()
            
        stats['grade_r']['improvement'] = stats['grade_r']['midline_score'] - stats['grade_r']['baseline_score']
        
        # Calculate Grade 1 stats using 'grade_label' and 'letters_correct_a1' (same as midline_2025.py)
        grade_1_baseline = school_baseline[school_baseline['grade_label'] == 'Grade 1']
        grade_1_midline = school_midline[school_midline['grade_label'] == 'Grade 1']
        
        if not grade_1_baseline.empty and 'letters_correct_a1' in grade_1_baseline.columns:
            stats['grade_1']['baseline_score'] = grade_1_baseline['letters_correct_a1'].mean()
        if not grade_1_midline.empty and 'letters_correct_a1' in grade_1_midline.columns:
            stats['grade_1']['midline_score'] = grade_1_midline['letters_correct_a1'].mean()
            
        stats['grade_1']['improvement'] = stats['grade_1']['midline_score'] - stats['grade_1']['baseline_score']
    
    return stats

def create_comparison_chart(stats, grade):
    """Create bar chart comparing Start of Year vs Mid-Year scores for a grade"""
    
    # Convert grade name to dictionary key
    if grade == 'Grade R':
        grade_key = 'grade_r'
    elif grade == 'Grade 1':
        grade_key = 'grade_1'
    else:
        grade_key = f'grade_{grade.lower().replace(" ", "_")}'
    
    grade_stats = stats[grade_key]
    
    data = {
        'Period': ['Start of Year', 'Mid-Year'],
        'Letter Score': [grade_stats['baseline_score'], grade_stats['midline_score']]
    }
    
    df = pd.DataFrame(data)
    
    fig = px.bar(
        df,
        x='Period',
        y='Letter Score',
        title=f'Start of Year vs Mid-Year Letter Scores for {grade}',
        color='Period',
        color_discrete_map={'Start of Year': '#87CEEB', 'Mid-Year': '#32CD32'},
        text='Letter Score'
    )
    
    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig.update_layout(
        showlegend=False,
        yaxis_title="Letter Score",
        height=400
    )
    
    return fig

def render_school_report(stats):
    """Render the school report based on the template"""
    
    st.markdown(f"""
    <div style="border: 2px solid #4CAF50; padding: 20px; margin: 20px 0;">
        <h2 style="color: #4CAF50; text-align: center;">{stats['school_name']}</h2>
        <h3 style="text-align: center;">Mid-Year Report</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Program description
    st.markdown("""
    **Zazi iZandi** is designed to help children at {school_name} improve their letter knowledge. 
    Letter knowledge is highly correlated with future reading, so it's a critical skill to teach children early in life. 
    
    Our Teacher Assistants work as support to your teachers and your children. Our goal is to help your school and your children. We are proud to work with you in helping {school_name} children learn their letter sounds.
    """.format(school_name=stats['school_name']))
    
    # Create two columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Summary Stats")
        st.markdown(f"""
        **Number of TAs:** {stats['summary']['total_tas']}  
        **Number of Children:** {stats['summary']['total_children']}  
        **Number of Classes:** {stats['summary']['total_classes']}
        """)
        
        st.markdown("### Grade R Stats")
        st.markdown(f"""
        **Start of Year Letter Score:** {stats['grade_r']['baseline_score']:.1f}  
        **Mid-Year Letter Score:** {stats['grade_r']['midline_score']:.1f}  
        **Mid-Year Improvement:** {stats['grade_r']['improvement']:.1f}
        """)
        
        st.markdown("### Grade 1 Stats")
        st.markdown(f"""
        **Start of Year Letter Score:** {stats['grade_1']['baseline_score']:.1f}  
        **Mid-Year Letter Score:** {stats['grade_1']['midline_score']:.1f}  
        **Mid-Year Improvement:** {stats['grade_1']['improvement']:.1f}
        """)
    
    with col2:
        # Create and display charts
        if stats['grade_r']['baseline_score'] > 0 or stats['grade_r']['midline_score'] > 0:
            st.markdown("### Grade R Progress Chart")
            fig_r = create_comparison_chart(stats, 'Grade R')
            st.plotly_chart(fig_r, width='stretch')
        
        if stats['grade_1']['baseline_score'] > 0 or stats['grade_1']['midline_score'] > 0:
            st.markdown("### Grade 1 Progress Chart") 
            fig_1 = create_comparison_chart(stats, 'Grade 1')
            st.plotly_chart(fig_1, width='stretch')
    
    # Contact information
    st.markdown("---")
    st.markdown("""
    **Thank you for partnering with us on this journey!** If you have any questions or concerns, please let us know.  
    You can reach Stanford at XXX-XXX-XXXX or stanford@masinyusane.org
    """)

def create_pdf_download_link(stats):
    """Create a download link for the school report as text/HTML"""
    
    # Create HTML content for the report
    html_content = f"""
    <html>
    <head>
        <title>{stats['school_name']} Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ border: 2px solid #4CAF50; padding: 20px; text-align: center; }}
            .stats {{ margin: 20px 0; }}
            .grade-section {{ margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>{stats['school_name']}</h2>
            <h3>{stats['reporting_period']} Report</h3>
        </div>
        
        <div class="stats">
            <h3>Summary Stats</h3>
            <p>Number of TAs: {stats['summary']['total_tas']}</p>
            <p>Number of Children: {stats['summary']['total_children']}</p>
            <p>Number of Classes: {stats['summary']['total_classes']}</p>
            
            <div class="grade-section">
                <h3>Grade R Stats</h3>
                <p>Start of Year Letter Score: {stats['grade_r']['baseline_score']:.1f}</p>
                <p>Mid-Year Letter Score: {stats['grade_r']['midline_score']:.1f}</p>
                <p>Mid-Year Improvement: {stats['grade_r']['improvement']:.1f}</p>
            </div>
            
            <div class="grade-section">
                <h3>Grade 1 Stats</h3>
                <p>Start of Year Letter Score: {stats['grade_1']['baseline_score']:.1f}</p>
                <p>Mid-Year Letter Score: {stats['grade_1']['midline_score']:.1f}</p>
                <p>Mid-Year Improvement: {stats['grade_1']['improvement']:.1f}</p>
            </div>
        </div>
        
        <hr>
        <p><strong>Thank you for partnering with us on this journey!</strong> If you have any questions or concerns, please let us know.<br>
        You can reach Stanford at XXX-XXX-XXXX or stanford@masinyusane.org</p>
    </body>
    </html>
    """
    
    # Convert to bytes for download
    b64 = base64.b64encode(html_content.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="{stats["school_name"]}_report.html">Download {stats["school_name"]} Report</a>'
    return href

def main():
    st.title("📊 School Reports Generator")
    st.markdown("Generate detailed reports for individual schools showing Start of Year vs Mid-Year letter knowledge progress.")
    
    # Load data
    with st.spinner("Loading 2025 assessment data..."):
        baseline_data, midline_data = load_assessment_data()
    
    if baseline_data is None or midline_data is None:
        st.error("Failed to load 2025 assessment data. Please check your data sources.")
        return
    
    # Get available schools using 'school_rep' column (same as midline_2025.py)
    available_schools = []
    if baseline_data is not None and 'school_rep' in baseline_data.columns:
        available_schools = sorted(baseline_data['school_rep'].unique())
    
    if not available_schools:
        st.warning("No schools found in the data.")
        return
    
    # School selection
    st.sidebar.header("Filter Options")
    selected_school = st.sidebar.selectbox(
        "Select School:",
        options=available_schools,
        help="Choose a school to generate its report"
    )
    
    if selected_school:
        # Calculate stats for selected school
        with st.spinner(f"Generating report for {selected_school}..."):
            school_stats = calculate_school_stats(baseline_data, midline_data, selected_school)
        
        # Render the report
        render_school_report(school_stats)
        
        # Add download button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            download_link = create_pdf_download_link(school_stats)
            st.markdown(download_link, unsafe_allow_html=True)
            st.info("📄 Click the link above to download this report as an HTML file")


main() 