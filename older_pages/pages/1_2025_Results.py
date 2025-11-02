import streamlit as st
import pandas as pd
import plotly.express as px
from process_survey_cto_updated import process_egra_data
from create_letter_tracker import create_letter_tracker
from letter_tracker_htmls import main as create_html_reports
import os
from datetime import datetime as dt
import pdfkit
import tempfile
import shutil
import zipfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if 'user' not in st.session_state or st.session_state.user is None:
    st.error("Please log in to access this page")
    st.stop()

@st.cache_data
def load_egra_data(children_filename: str, ta_filename: str):
    """
    Caches the DataFrame loading and processing so it doesn't
    re-run on every Streamlit re-execution or widget change.
    """
    children_path = os.path.join(ROOT_DIR, "data", children_filename)
    ta_path       = os.path.join(ROOT_DIR, "data", ta_filename)

    df, df_ecd = process_egra_data(
        children_file=children_path,
        ta_file=ta_path
    )
    return df, df_ecd

# Streamlit page header
st.set_page_config(page_title="TA Assessments", layout="wide")

# Create tabs
midline_tab, baseline_tab = st.tabs(["2025 Midline", "2025 Baseline"])

with midline_tab:
    st.title("2025 Midline Assessments")
    
    # Read and process data
    try:
            df_full, df_ecd = load_egra_data(
                children_filename="EGRA form [Eastern Cape]-assessment_repeat - June 4.csv",
                ta_filename="EGRA form [Eastern Cape] - June 4.csv"
            )
            df_full['submission_date'] = pd.to_datetime(df_full['date'])
            
            # Create initial and midline datasets for comparison charts
            initial_df = df_full[df_full['submission_date'] < pd.Timestamp('2025-04-15')]
            midline_df = df_full[df_full['submission_date'] >= pd.Timestamp('2025-04-15')]
            
            # START OF PAGE

            col1, col2, col3 = st.columns(3)

            with col1:# Total Assessed
                st.metric("Total Number of Children Assessed", len(midline_df))

            with col2:
                # Number of TAs that assessed >= 20 kids
                ta_counts = midline_df['name_ta_rep'].value_counts()
                ta_more_than_20 = ta_counts[ta_counts >= 20]
                st.metric("TAs That Assessed > 20 Children", f'{len(ta_more_than_20)}')

            with col3:
                # Number of TAs that submitted anything
                ta_counts = midline_df['name_ta_rep'].value_counts()
                st.metric("TAs That Submitted Results (1+ Children)", f'{len(ta_counts)}')

            st.divider()

            # Add the three charts from 1_Letter Knowledge.py
            with st.container():
                st.subheader('Letter EGRA Improvement')

                # Calculate summary for initial assessments
                initial_summary = initial_df.groupby('grade_label').agg({
                    'letters_correct': 'mean'
                }).round(1).reset_index()
                initial_summary.columns = ['Grade', 'Initial Score']

                # Calculate summary for midline assessments
                midline_summary = midline_df.groupby('grade_label').agg({
                    'letters_correct': 'mean'
                }).round(1).reset_index()
                midline_summary.columns = ['Grade', 'Midline Score']

                # Merge the summaries
                egra_summary = pd.merge(initial_summary, midline_summary, on='Grade', how='outer')

                # Melt the DataFrame for Plotly
                egra_summary_melted = egra_summary.melt(
                    id_vars='Grade',
                    value_vars=['Initial Score', 'Midline Score'],
                    var_name='Measurement',
                    value_name='Score'
                )

                # Create the Plotly bar graph with grouped bars
                egra_fig = px.bar(
                    egra_summary_melted,
                    x='Grade',
                    y='Score',
                    color='Measurement',
                    barmode='group',
                    labels={'Score': 'Average Score'},
                    color_discrete_map={'Initial Score': '#b3b3b3', 'Midline Score': '#ffd641'}
                )

                st.plotly_chart(egra_fig, width='stretch')

                with st.expander('Click to view data:'):
                    st.dataframe(egra_summary)

            st.divider()

            with st.container():
                st.subheader("Percentage of Grade 1's On Grade Level")
                st.success("The number of Grade 1 children 'On Grade Level' for letter knowledge more than quadrupled, increasing from 13% to 53%!")

                # Filter for Grade 1 only
                g1_initial = initial_df[initial_df['grade_label'] == 'Grade 1']
                g1_midline = midline_df[midline_df['grade_label'] == 'Grade 1']

                # Calculate percentages for initial
                initial_40_or_more = (g1_initial['letters_correct'] >= 40).sum()
                initial_less_than_40 = (g1_initial['letters_correct'] < 40).sum()
                total_initial = initial_40_or_more + initial_less_than_40

                initial_40_or_more_percent = (initial_40_or_more / total_initial).round(3) * 100 if total_initial > 0 else 0
                initial_less_than_40_percent = (initial_less_than_40 / total_initial).round(3) * 100 if total_initial > 0 else 0

                # Calculate percentages for midline
                midline_40_or_more = (g1_midline['letters_correct'] >= 40).sum()
                midline_less_than_40 = (g1_midline['letters_correct'] < 40).sum()
                total_midline = midline_40_or_more + midline_less_than_40

                midline_40_or_more_percent = (midline_40_or_more / total_midline).round(3) * 100 if total_midline > 0 else 0
                midline_less_than_40_percent = (midline_less_than_40 / total_midline).round(3) * 100 if total_midline > 0 else 0

                # Create DataFrame
                data = {
                    'Above Grade Level': [initial_40_or_more_percent, midline_40_or_more_percent]
                }

                df_grade_level = pd.DataFrame(data, index=['Initial', 'Midline'])

                # Melt the DataFrame for Plotly
                df_melted = df_grade_level.reset_index().melt(
                    id_vars='index',
                    value_vars=['Above Grade Level'],
                    var_name='Score Category',
                    value_name='Percentage'
                )

                # Create the Plotly bar graph
                grade_level_fig = px.bar(
                    df_melted,
                    x='index',
                    y='Percentage',
                    color='Score Category',
                    barmode='group',
                    labels={'index': 'Assessment', 'Percentage': 'Percentage (%)'},
                    color_discrete_map={'Above Grade Level': '#32c93c'}
                )

                # Add horizontal line at y=27 with label 'South Africa Average'
                grade_level_fig.add_hline(
                    y=27,
                    line_dash='dash',
                    line_color='red',
                    annotation_text='South Africa Average',
                    annotation_position='top left'
                )

                st.plotly_chart(grade_level_fig, width='stretch')

                with st.expander('Click to view data:'):
                    st.dataframe(df_grade_level)

            st.divider()

            # School Summary
            with st.container():
                st.header("School Summary")
                school_summary = midline_df.groupby(['school_rep', 'grade_label']).agg(
                    Number_Assessed=('name_first_learner', 'count'),
                    Average_Letters_Correct=('letters_correct_a1', 'mean'),
                    Letter_Score=('letters_score_a1', 'mean'),
                    Count_Above_40=('letters_correct_a1', lambda x: (x >= 40).sum())
                ).reset_index()
                school_summary['Average_Letters_Correct'] = school_summary['Average_Letters_Correct'].round(1)
                school_summary['Letter_Score'] = school_summary['Letter_Score'].round(1)
                school_summary = school_summary.sort_values(by='Average_Letters_Correct', ascending=False)

                # Setting a filter for which results end up displayed on the chart.
                school_summary = school_summary[school_summary['Number_Assessed'] > 10]

                fig = px.bar(
                    school_summary,
                    x="school_rep",
                    y="Average_Letters_Correct",
                    color="grade_label",
                    barmode="group",
                    title="Average Letters Correct by School and Grade",
                    labels={"school_rep": "School", "Average_Letters_Correct": "Average Letters Correct"},
                    color_discrete_sequence=px.colors.qualitative.Set2  # Optional: Use a qualitative color scheme
                )

                fig.update_layout(
                    xaxis_title="School",
                    yaxis_title="Average Letters Correct",
                    legend_title="Grade",
                )

                st.plotly_chart(fig, width='stretch')

                st.dataframe(school_summary, width='stretch')

            st.divider()
            # Add this section after your existing Grade 1 analyses (around line 285-300)
            with st.container():
                st.header("Grade 1 Benchmark by School")

                # Filter for Grade 1 only
                g1_letter_scores = midline_df[midline_df['grade_label'] == 'Grade 1']

                # Calculate percentage by school
                school_letter_score_summary = g1_letter_scores.groupby('school_rep').agg(
                    Total_Assessed=('name_first_learner', 'count'),
                    Above_40_Count=('letters_score', lambda x: (x >= 40).sum())
                ).reset_index()

                # Calculate percentage
                school_letter_score_summary['Percentage_Above_40'] = (
                        school_letter_score_summary['Above_40_Count'] /
                        school_letter_score_summary['Total_Assessed'] * 100
                ).round(1)

                # Sort by percentage descending
                school_letter_score_summary = school_letter_score_summary.sort_values(
                    by='Percentage_Above_40', ascending=False
                )

                # Create bar chart
                fig = px.bar(
                    school_letter_score_summary,
                    x='school_rep',
                    y='Percentage_Above_40',
                    title='Percentage of Grade 1 Learners with Letter Score >= 40 by School',
                    labels={'school_rep': 'School', 'Percentage_Above_40': 'Percentage (%)'},
                    color='Percentage_Above_40',
                    text='Percentage_Above_40',
                    color_continuous_scale='RdYlGn'
                )

                # Customize layout
                fig.update_layout(
                    xaxis_title="School",
                    yaxis_title="Percentage (%)",
                    showlegend=False,
                    yaxis_range=[0, 100]  # Set y-axis from 0 to 100%
                )

                # Display chart
                st.plotly_chart(fig, width='stretch')

                # Show detailed table
                st.dataframe(school_letter_score_summary, width='stretch')

            def generate_letter_tracker_pdfs(df):
                """Generate letter tracker PDFs through the full pipeline"""
                # Create temporary directory for processing
                temp_dir = tempfile.mkdtemp()
                try:
                    # Set up directories
                    os.makedirs(os.path.join(temp_dir, 'html_reports'), exist_ok=True)
                    os.makedirs(os.path.join(temp_dir, 'pdf_trackers'), exist_ok=True)

                    # Step 1: Create letter tracker
                    with st.spinner('Creating letter tracker...'):
                        letter_tracker_path = os.path.join(temp_dir, 'Letter Tracker.csv')
                        letter_tracker_df = create_letter_tracker(df, export_csv=True, output_path=letter_tracker_path)

                    # Step 2: Generate HTML reports
                    with st.spinner('Generating HTML reports...'):
                        original_dir = os.getcwd()
                        os.chdir(temp_dir)
                        create_html_reports()
                        os.chdir(original_dir)

                    # Step 3: Convert to PDFs
                    with st.spinner('Converting to PDFs...'):
                        options = {
                            'orientation': 'Landscape',
                            'page-size': 'A4',
                            'margin-top': '0.25in',
                            'margin-bottom': '0.25in',
                            'margin-left': '0.25in',
                            'margin-right': '0.25in',
                        }

                        html_dir = os.path.join(temp_dir, 'html_reports')
                        pdf_dir = os.path.join(temp_dir, 'pdf_trackers')

                        for filename in os.listdir(html_dir):
                            if filename.lower().endswith(".html"):
                                input_path = os.path.join(html_dir, filename)
                                output_path = os.path.join(
                                    pdf_dir,
                                    os.path.splitext(filename)[0] + ".pdf"
                                )
                                pdfkit.from_file(input_path, output_path, options=options)

                    # Create zip file of PDFs
                    zip_path = os.path.join(temp_dir, 'letter_trackers.zip')
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for root, dirs, files in os.walk(pdf_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, pdf_dir)
                                zipf.write(file_path, arcname)

                    # Read zip file
                    with open(zip_path, 'rb') as f:
                        return f.read()

                finally:
                    # Clean up temporary directory
                    shutil.rmtree(temp_dir)


            # OpenAI Analysis Section
            st.divider()
            with st.container():
                st.header("🤖 AI Data Analysis")
                st.write("Get insights from OpenAI's ChatGPT about your assessment data. You can ask about overall performance, underperforming schools, and more.")
                
                # Analysis type selection
                analysis_col1, analysis_col2 = st.columns(2)
                
                with analysis_col1:
                    analysis_type = st.selectbox(
                        "Select Analysis Type:",
                        ["general", "school_comparison", "grade_improvement"],
                        format_func=lambda x: {
                            "general": "📊 General Overview", 
                            "school_comparison": "🏫 School Performance",
                            "grade_improvement": "📈 Grade Analysis"
                        }[x]
                    )
                
                with analysis_col2:
                    model_choice = st.selectbox(
                        "Select AI Model:",
                        ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
                        help="gpt-4o-mini is faster and cheaper, gpt-4o is more capable"
                    )
                
                # Custom questions input
                custom_questions_input = st.text_area(
                    "Additional Questions (optional):",
                    placeholder="Enter specific questions you'd like the AI to address, one per line",
                    help="Ask specific questions about the data, e.g., 'What factors might explain school performance differences?'"
                )
                
                # Parse custom questions
                custom_questions = None
                if custom_questions_input.strip():
                    custom_questions = [q.strip() for q in custom_questions_input.split('\n') if q.strip()]
                
                # Analysis button
                if st.button("🚀 Generate AI Analysis", type="primary"):
                    if not os.getenv('OPENAI_API_KEY'):
                        st.error("⚠️ OPENAI_API_KEY not found in environment variables. Please add it to your .env file.")
                    else:
                        with st.spinner("🤔 AI is analyzing your data..."):
                            try:
                                # Import the tools analysis function
                                import sys
                                import os
                                sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
                                from AI_Tools.openai_tools_analysis import analyze_with_tools
                                
                                if custom_questions:
                                    analysis = analyze_with_tools(
                                        midline_df,
                                        analysis_type="question",
                                        question="\n".join(custom_questions),
                                        model=model_choice
                                    )
                                else:
                                    analysis = analyze_with_tools(
                                        midline_df,
                                        analysis_type="initial",
                                        model=model_choice
                                    )
                                
                                if analysis:
                                    st.success("✅ Analysis Complete!")
                                    
                                    # Display the analysis in an expandable section
                                    with st.expander("📋 AI Analysis Results", expanded=True):
                                        st.markdown(analysis)
                                    
                                    # Option to download the analysis
                                    st.download_button(
                                        label="📥 Download Analysis",
                                        data=analysis,
                                        file_name=f"ai_analysis_{analysis_type}_{dt.today().strftime('%Y-%m-%d')}.txt",
                                        mime="text/plain"
                                    )
                                else:
                                    st.error("❌ Failed to generate analysis. Please check your API key and try again.")
                                    
                            except ImportError:
                                st.error("❌ OpenAI tools analysis module not found. Please ensure openai_tools_analysis.py is in your project directory.")
                            except Exception as e:
                                st.error(f"❌ Error during analysis: {str(e)}")
                
                # Quick data preview for context
                with st.expander("📊 Data Preview", expanded=False):
                    st.write(f"**Total Students:** {len(midline_df)}")
                    st.write(f"**Schools:** {midline_df['school_rep'].nunique()}")
                    st.write(f"**Teaching Assistants:** {midline_df['name_ta_rep'].nunique()}")
                    st.write("**Sample Data:**")
                    st.dataframe(midline_df[['school_rep', 'grade_label', 'letters_correct', 'name_ta_rep']].head(), width='stretch')
            
            st.divider()
            with st.container():
                st.subheader("Data Export Tools")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if st.button("Generate Letter Tracker CSV (w Groups)", key="midline_letter_tracker"):
                        try:
                            letter_tracker_df = create_letter_tracker(midline_df, export_csv=False)
                            csv = letter_tracker_df.to_csv(index=False)
                            st.download_button(
                                label="Download Letter Tracker",
                                data=csv,
                                file_name="Letter_Tracker.csv",
                                mime="text/csv",
                            )
                            st.success("Letter Tracker generated successfully!")
                        except Exception as e:
                            st.error(f"Error generating Letter Tracker: {str(e)}")

                with col2:
                    if st.button("Generate Full Dataset", key="midline_full_dataset"):
                        try:
                            # Get current date for filename
                            date = dt.today().strftime('%Y-%m-%d')
                            # Convert full DataFrame to CSV
                            csv = midline_df.to_csv(index=False)
                            st.download_button(
                                label="Download Full Dataset",
                                data=csv,
                                file_name=f"merged_data_{date}.csv",
                                mime="text/csv",
                            )
                            st.success("Full dataset ready for download!")
                        except Exception as e:
                            st.error(f"Error generating full dataset: {str(e)}")

                with col3:
                    if st.button("Generate PDF Letter Trackers", key="midline_pdf_trackers"):
                        try:
                            zip_data = generate_letter_tracker_pdfs(midline_df)
                            st.download_button(
                                label="Download PDF Letter Trackers",
                                data=zip_data,
                                file_name="letter_trackers.zip",
                                mime="application/zip"
                            )
                            st.success("PDF Letter Trackers generated successfully!")
                        except Exception as e:
                            st.error(f"Error generating PDFs: {str(e)}")

                with col4:
                    if st.button("ECD Dataset", key="midline_ecd_dataset"):
                        try:
                            # Get current date for filename
                            date = dt.today().strftime('%Y-%m-%d')
                            # Convert full DataFrame to CSV
                            csv = df_ecd.to_csv(index=False)
                            st.download_button(
                                label="Download Full Dataset",
                                data=csv,
                                file_name=f"ecd_data_{date}.csv",
                                mime="text/csv",
                            )
                            st.success("Full dataset ready for download!")
                        except Exception as e:
                            st.error(f"Error generating full dataset: {str(e)}")
            
            st.divider()
            st.subheader("Assessment Stats")
            with st.expander("Show Assessment Stats"):
                # Assessments Per TA
                with st.container():
                    st.subheader("Assessments Per TA")

                    ta_counts = midline_df['name_ta_rep'].value_counts().reset_index()
                    ta_counts.columns = ['name_ta_rep', 'count']

                    fig = px.bar(
                        ta_counts,
                        x='name_ta_rep',
                        y='count',
                        title='Counts of TAs',
                        labels={'name_ta_rep': 'TA Name', 'count': 'Number of Kids Assessed'},
                        color='count',
                        text='count'
                    )

                    fig.update_layout(
                        xaxis_title="TA Name",
                        yaxis_title="Number of Kids Assessed",
                        showlegend=False
                    )


                    st.plotly_chart(fig, width='stretch')

                with st.container():
                    st.subheader("Assessments Per School & Grade")

                    # Group by school and grade, counting the number of assessments
                    school_grade_counts = (
                        midline_df.groupby(['school_rep', 'grade'])
                        .size()
                        .reset_index(name='count')
                    )

                    # Create a combined x-axis label for better readability
                    school_grade_counts['school_grade'] = (
                        school_grade_counts['school_rep'] + "_" + school_grade_counts['grade'].astype(str)
                    )

                    # Sort by count (descending)
                    school_grade_counts = school_grade_counts.sort_values(by='count', ascending=False)

                    # Plot using Plotly
                    fig = px.bar(
                        school_grade_counts,
                        x='school_grade',
                        y='count',
                        title="Assessments Per School & Grade",
                        labels={'school_grade': 'School - Grade', 'count': 'Number of Assessments'},
                        color='count',
                        text='count',
                        color_continuous_scale='Blues'  # Optional: Color gradient for visibility
                    )

                    # Improve layout
                    fig.update_layout(
                        height=700,
                        xaxis_title="School & Grade",
                        yaxis_title="Number of Assessments",
                        showlegend=False,
                        # xaxis_tickangle=-45  # Tilt x-axis labels for readability
                    )

                    # Display in Streamlit
                    st.plotly_chart(fig, width='stretch')

                with st.container():
                    st.subheader("Assessments Per School & Grade")

                    # Group by school and grade, counting the number of assessments
                    school_class_counts = (
                        midline_df.groupby(['school_rep','class'])
                        .size()
                        .reset_index(name='count')
                    )

                    # Create a combined x-axis label for better readability
                    school_class_counts['school_class'] = (
                        school_class_counts['school_rep'] + "_" + school_class_counts['class'].astype(str)
                    )

                    # Sort by count (descending)
                    school_class_counts = school_class_counts.sort_values(by='count', ascending=False)

                    # Plot using Plotly
                    fig = px.bar(
                        school_class_counts,
                        x='school_class',
                        y='count',
                        title="Assessments Per School & Class",
                        labels={'school_class': 'School - Class', 'count': 'Number of Assessments'},
                        color='count',
                        text='count',
                        color_continuous_scale='Blues'  # Optional: Color gradient for visibility
                    )

                    # Improve layout
                    fig.update_layout(
                        height=700,
                        xaxis_title="School & Class",
                        yaxis_title="Number of Assessments",
                        showlegend=False,
                        # xaxis_tickangle=-45  # Tilt x-axis labels for readability
                    )

                    # Display in Streamlit
                    st.plotly_chart(fig, width='stretch')

                # TA Assessments Summary
                with st.container():
                    st.header("Assessments Completed Per School & TA")
                    ta_assessments = midline_df.groupby(['school_rep', 'name_ta_rep', 'grade_label'])['name_first_learner'].count().reset_index()
                    ta_assessments.columns = ['School', 'TA', 'Grade', 'Count']
                    st.dataframe(ta_assessments, width='stretch')

            st.divider()
            
            # Missing Midline Assessments
            with st.expander("Schools & Grades Missing Midline Assessments"):
                st.subheader("Schools and Grades with Initial Results but No Midline Results")
                
                # Get unique combinations of school and grade from initial assessments
                initial_combinations = initial_df[['school_rep', 'grade_label']].drop_duplicates()
                initial_combinations['has_initial'] = True
                
                # Get unique combinations of school and grade from midline assessments  
                midline_combinations = midline_df[['school_rep', 'grade_label']].drop_duplicates()
                midline_combinations['has_midline'] = True
                
                # Merge to find combinations that exist in initial but not in midline
                comparison_df = pd.merge(
                    initial_combinations, 
                    midline_combinations, 
                    on=['school_rep', 'grade_label'], 
                    how='left'
                )
                
                # Filter for combinations that have initial but no midline
                missing_midline = comparison_df[comparison_df['has_midline'].isna()].copy()
                missing_midline = missing_midline[['school_rep', 'grade_label']]
                missing_midline.columns = ['School', 'Grade']
                
                # Add count of initial assessments for context
                initial_counts = initial_df.groupby(['school_rep', 'grade_label']).size().reset_index(name='Initial_Count')
                missing_midline = pd.merge(
                    missing_midline,
                    initial_counts,
                    left_on=['School', 'Grade'],
                    right_on=['school_rep', 'grade_label'],
                    how='left'
                )[['School', 'Grade', 'Initial_Count']]
                
                missing_midline = missing_midline.sort_values(['School', 'Grade'])
                
                if len(missing_midline) > 0:
                    st.warning(f"Found {len(missing_midline)} school-grade combinations with initial results but no midline results:")
                    st.dataframe(missing_midline, width='stretch')
                else:
                    st.success("All schools and grades with initial assessments also have midline assessments!")

    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        st.stop()

with baseline_tab:
    st.title("2025 Initial Assessments")
# st.info("Utilizing SurveyCTO's EGRA Plugin. As of Jan 25, 2025, we have 41 TAs starting with assessments. The next 40 will begin once their TLT contracts are signed.")

# Read and process data
    try:
        df_full, df_ecd = load_egra_data(
            children_filename="EGRA form [Eastern Cape]-assessment_repeat - June 4.csv",
            ta_filename="EGRA form [Eastern Cape] - June 4.csv"
        )
        df_full['submission_date'] = pd.to_datetime(df_full['date'])
        
        # Create initial dataset for initial assessments (before midline cutoff)
        initial_df = df_full[df_full['submission_date'] < pd.Timestamp('2025-04-15')]

        # START OF PAGE

        col1, col2, col3 = st.columns(3)

        with col1:# Total Assessed
            st.metric("Total Number of Children Assessed", len(initial_df))

        with col2:
            # Number of TAs that assessed >= 20 kids
            ta_counts = initial_df['name_ta_rep'].value_counts()
            ta_more_than_20 = ta_counts[ta_counts >= 20]
            st.metric("TAs That Assessed > 20 Children", f'{len(ta_more_than_20)}')

        with col3:
            # Number of TAs that submitted anything
            ta_counts = initial_df['name_ta_rep'].value_counts()
            st.metric("TAs That Submitted Results (1+ Children)", f'{len(ta_counts)}')


        st.divider()

        # Grade Summary
        with st.container():
            st.subheader("EGRA Letters per Grade")
            grade_summary = initial_df.groupby(['grade_label']).agg(
                Number_Assessed=('name_first_learner', 'count'),
                Average_Letters_Correct=('letters_correct_a1', 'mean'),
                Letter_Score=('letters_score_a1', 'mean'),
                Count_Above_40=('letters_correct_a1', lambda x: (x >= 40).sum())
            ).reset_index()
            grade_summary['Average_Letters_Correct'] = grade_summary['Average_Letters_Correct'].round(1)
            grade_summary['Letter_Score'] = grade_summary['Letter_Score'].round(1)

            # Setting a filter for which results end up displayed on the chart.
            grade_summary = grade_summary[grade_summary['Number_Assessed'] > 10]

            fig = px.bar(
                grade_summary,
                x="grade_label",
                y="Average_Letters_Correct",
                title="Avg Score",
                labels={'grade_label': 'Grade', 'Average_Letters_Correct': 'EGRA Score'},
                color="Average_Letters_Correct",
                text="Average_Letters_Correct",
                color_continuous_scale="Blues"  # Optional: Use color to indicate values
            )

            # Adjust layout
            fig.update_layout(
                xaxis_title="Grade",
                yaxis_title="EGRA Scores",
                showlegend=False
            )

            st.plotly_chart(fig, width='stretch')

            with st.expander("Show results"):
                st.dataframe(grade_summary, width='stretch')

        st.divider()

        
        # School Summary
        with st.container():
            st.header("School Summary")
            school_summary = initial_df.groupby(['school_rep', 'grade_label']).agg(
                Number_Assessed=('name_first_learner', 'count'),
                Average_Letters_Correct=('letters_correct_a1', 'mean'),
                Letter_Score=('letters_score_a1', 'mean'),
                Count_Above_40=('letters_correct_a1', lambda x: (x >= 40).sum())
            ).reset_index()
            school_summary['Average_Letters_Correct'] = school_summary['Average_Letters_Correct'].round(1)
            school_summary['Letter_Score'] = school_summary['Letter_Score'].round(1)
            school_summary = school_summary.sort_values(by='Average_Letters_Correct', ascending=False)

            # Setting a filter for which results end up displayed on the chart.
            school_summary = school_summary[school_summary['Number_Assessed'] > 10]

            fig = px.bar(
                school_summary,
                x="school_rep",
                y="Average_Letters_Correct",
                color="grade_label",
                barmode="group",
                title="Average Letters Correct by School and Grade",
                labels={"school_rep": "School", "Average_Letters_Correct": "Average Letters Correct"},
                color_discrete_sequence=px.colors.qualitative.Set2  # Optional: Use a qualitative color scheme
            )

            fig.update_layout(
                xaxis_title="School",
                yaxis_title="Average Letters Correct",
                legend_title="Grade",
            )

            st.plotly_chart(fig, width='stretch')

            st.dataframe(school_summary, width='stretch')



        st.divider()
        # Add this section after your existing Grade 1 analyses
        with st.container():
            st.header("Grade 1 Learners Hitting Benchmark")
            st.info("This is a measure of how many Grade 1 learners are hitting the benchmark of 40 letters correct.")

            # Filter for Grade 1 only
            g1_letter_scores = initial_df[initial_df['grade_label'] == 'Grade 1']

            # Calculate overall statistics
            total_g1_students = len(g1_letter_scores)
            students_above_40 = len(g1_letter_scores[g1_letter_scores['letters_score_a1'] >= 40])
            percentage_above_40 = (students_above_40 / total_g1_students * 100) if total_g1_students > 0 else 0

            # Create a simple bar chart showing percentage
            fig = px.bar(
                x=['Grade 1'],
                y=[percentage_above_40],
                title='Percentage of Grade 1 Learners with Letter Score >= 40',
                labels={'x': 'Grade', 'y': 'Percentage (%)'},
                text=[f'{percentage_above_40:.1f}%'],
                color=[percentage_above_40],
                color_continuous_scale='RdYlGn'
            )

            # Customize layout
            fig.update_layout(
                xaxis_title="",
                yaxis_title="Percentage (%)",
                showlegend=False,
                yaxis_range=[0, 100],  # Set y-axis from 0 to 100%
                height=400
            )

            # Display chart
            st.plotly_chart(fig, width='stretch')

            # Show summary stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Grade 1 Students", total_g1_students)
            with col2:
                st.metric("Students with Score >= 40", students_above_40)
            with col3:
                st.metric("Percentage Above 40", f"{percentage_above_40:.1f}%")

        st.divider()
        # Add this section after your existing Grade 1 analyses (around line 285-300)
        with st.container():
            st.header("Grade 1 Benchmark by School")

            # Filter for Grade 1 only
            g1_letter_scores = initial_df[initial_df['grade_label'] == 'Grade 1']

            # Calculate percentage by school
            school_letter_score_summary = g1_letter_scores.groupby('school_rep').agg(
                Total_Assessed=('name_first_learner', 'count'),
                Above_40_Count=('letters_score_a1', lambda x: (x >= 40).sum())
            ).reset_index()

            # Calculate percentage
            school_letter_score_summary['Percentage_Above_40'] = (
                    school_letter_score_summary['Above_40_Count'] /
                    school_letter_score_summary['Total_Assessed'] * 100
            ).round(1)

            # Sort by percentage descending
            school_letter_score_summary = school_letter_score_summary.sort_values(
                by='Percentage_Above_40', ascending=False
            )

            # Create bar chart
            fig = px.bar(
                school_letter_score_summary,
                x='school_rep',
                y='Percentage_Above_40',
                title='Percentage of Grade 1 Learners with Letter Score >= 40 by School',
                labels={'school_rep': 'School', 'Percentage_Above_40': 'Percentage (%)'},
                color='Percentage_Above_40',
                text='Percentage_Above_40',
                color_continuous_scale='RdYlGn'
            )

            # Customize layout
            fig.update_layout(
                xaxis_title="School",
                yaxis_title="Percentage (%)",
                showlegend=False,
                yaxis_range=[0, 100]  # Set y-axis from 0 to 100%
            )

            # Display chart
            st.plotly_chart(fig, width='stretch')

            # Show detailed table
            st.dataframe(school_letter_score_summary, width='stretch')

        with st.container():
            st.subheader("Data Export Tools")
            
            def generate_letter_tracker_pdfs(initial_df):
                """Generate letter tracker PDFs through the full pipeline"""
                # Create temporary directory for processing
                temp_dir = tempfile.mkdtemp()
                try:
                    # Set up directories
                    os.makedirs(os.path.join(temp_dir, 'html_reports'), exist_ok=True)
                    os.makedirs(os.path.join(temp_dir, 'pdf_trackers'), exist_ok=True)

                    # Step 1: Create letter tracker
                    with st.spinner('Creating letter tracker...'):
                        letter_tracker_path = os.path.join(temp_dir, 'Letter Tracker.csv')
                        letter_tracker_df = create_letter_tracker(initial_df, export_csv=True, output_path=letter_tracker_path)

                    # Step 2: Generate HTML reports
                    with st.spinner('Generating HTML reports...'):
                        original_dir = os.getcwd()
                        os.chdir(temp_dir)
                        create_html_reports()
                        os.chdir(original_dir)

                    # Step 3: Convert to PDFs
                    with st.spinner('Converting to PDFs...'):
                        options = {
                            'orientation': 'Landscape',
                            'page-size': 'A4',
                            'margin-top': '0.25in',
                            'margin-bottom': '0.25in',
                            'margin-left': '0.25in',
                            'margin-right': '0.25in',
                        }

                        html_dir = os.path.join(temp_dir, 'html_reports')
                        pdf_dir = os.path.join(temp_dir, 'pdf_trackers')

                        for filename in os.listdir(html_dir):
                            if filename.lower().endswith(".html"):
                                input_path = os.path.join(html_dir, filename)
                                output_path = os.path.join(
                                    pdf_dir,
                                    os.path.splitext(filename)[0] + ".pdf"
                                )
                                pdfkit.from_file(input_path, output_path, options=options)

                    # Create zip file of PDFs
                    zip_path = os.path.join(temp_dir, 'letter_trackers.zip')
                    with zipfile.ZipFile(zip_path, 'w') as zipf:
                        for root, dirs, files in os.walk(pdf_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, pdf_dir)
                                zipf.write(file_path, arcname)

                    # Read zip file
                    with open(zip_path, 'rb') as f:
                        return f.read()

                finally:
                    # Clean up temporary directory
                    shutil.rmtree(temp_dir)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("Generate Letter Tracker CSV (w Groups)"):
                    try:
                        letter_tracker_df = create_letter_tracker(initial_df, export_csv=False)
                        csv = letter_tracker_df.to_csv(index=False)
                        st.download_button(
                            label="Download Letter Tracker",
                            data=csv,
                            file_name="Letter_Tracker.csv",
                            mime="text/csv",
                        )
                        st.success("Letter Tracker generated successfully!")
                    except Exception as e:
                        st.error(f"Error generating Letter Tracker: {str(e)}")

            with col2:
                if st.button("Generate Full Dataset"):
                    try:
                        # Get current date for filename
                        date = dt.today().strftime('%Y-%m-%d')
                        # Convert full DataFrame to CSV
                        csv = initial_df.to_csv(index=False)
                        st.download_button(
                            label="Download Full Dataset",
                            data=csv,
                            file_name=f"merged_data_{date}.csv",
                            mime="text/csv",
                        )
                        st.success("Full dataset ready for download!")
                    except Exception as e:
                        st.error(f"Error generating full dataset: {str(e)}")

            with col3:
                if st.button("Generate PDF Letter Trackers"):
                    try:
                        zip_data = generate_letter_tracker_pdfs(initial_df)
                        st.download_button(
                            label="Download PDF Letter Trackers",
                            data=zip_data,
                            file_name="letter_trackers.zip",
                            mime="application/zip"
                        )
                        st.success("PDF Letter Trackers generated successfully!")
                    except Exception as e:
                        st.error(f"Error generating PDFs: {str(e)}")

            with col4:
                if st.button("ECD Dataset"):
                    try:
                        # Get current date for filename
                        date = dt.today().strftime('%Y-%m-%d')
                        # Convert full DataFrame to CSV
                        csv = df_ecd.to_csv(index=False)
                        st.download_button(
                            label="Download Full Dataset",
                            data=csv,
                            file_name=f"ecd_data_{date}.csv",
                            mime="text/csv",
                        )
                        st.success("Full dataset ready for download!")
                    except Exception as e:
                        st.error(f"Error generating full dataset: {str(e)}")
        
        st.divider()
        st.subheader("Assessment Stats")
        with st.expander("Show Assessment Stats"):
            # Assessments Per TA
            with st.container():
                st.subheader("Assessments Per TA")

                ta_counts = initial_df['name_ta_rep'].value_counts().reset_index()
                ta_counts.columns = ['name_ta_rep', 'count']

                fig = px.bar(
                    ta_counts,
                    x='name_ta_rep',
                    y='count',
                    title='Counts of TAs',
                    labels={'name_ta_rep': 'TA Name', 'count': 'Number of Kids Assessed'},
                    color='count',
                    text='count'
                )

                fig.update_layout(
                    xaxis_title="TA Name",
                    yaxis_title="Number of Kids Assessed",
                    showlegend=False
                )


                st.plotly_chart(fig, width='stretch')

            with st.container():
                st.subheader("Assessments Per School & Grade")

                # Group by school and grade, counting the number of assessments
                school_grade_counts = (
                    initial_df.groupby(['school_rep', 'grade'])
                    .size()
                    .reset_index(name='count')
                )

                # Create a combined x-axis label for better readability
                school_grade_counts['school_grade'] = (
                    school_grade_counts['school_rep'] + "_" + school_grade_counts['grade'].astype(str)
                )

                # Sort by count (descending)
                school_grade_counts = school_grade_counts.sort_values(by='count', ascending=False)

                # Plot using Plotly
                fig = px.bar(
                    school_grade_counts,
                    x='school_grade',
                    y='count',
                    title="Assessments Per School & Grade",
                    labels={'school_grade': 'School - Grade', 'count': 'Number of Assessments'},
                    color='count',
                    text='count',
                    color_continuous_scale='Blues'  # Optional: Color gradient for visibility
                )

                # Improve layout
                fig.update_layout(
                    height=700,
                    xaxis_title="School & Grade",
                    yaxis_title="Number of Assessments",
                    showlegend=False,
                    # xaxis_tickangle=-45  # Tilt x-axis labels for readability
                )

                # Display in Streamlit
                st.plotly_chart(fig, width='stretch')

            with st.container():
                st.subheader("Assessments Per School & Grade")

                # Group by school and grade, counting the number of assessments
                school_class_counts = (
                    initial_df.groupby(['school_rep','class'])
                    .size()
                    .reset_index(name='count')
                )

                # Create a combined x-axis label for better readability
                school_class_counts['school_class'] = (
                    school_class_counts['school_rep'] + "_" + school_class_counts['class'].astype(str)
                )

                # Sort by count (descending)
                school_class_counts = school_class_counts.sort_values(by='count', ascending=False)

                # Plot using Plotly
                fig = px.bar(
                    school_class_counts,
                    x='school_class',
                    y='count',
                    title="Assessments Per School & Class",
                    labels={'school_class': 'School - Class', 'count': 'Number of Assessments'},
                    color='count',
                    text='count',
                    color_continuous_scale='Blues'  # Optional: Color gradient for visibility
                )

                # Improve layout
                fig.update_layout(
                    height=700,
                    xaxis_title="School & Class",
                    yaxis_title="Number of Assessments",
                    showlegend=False,
                    # xaxis_tickangle=-45  # Tilt x-axis labels for readability
                )

                # Display in Streamlit
                st.plotly_chart(fig, width='stretch')

            # TA Assessments Summary
            with st.container():
                st.header("Assessments Completed Per School & TA")
                ta_assessments = initial_df.groupby(['school_rep', 'name_ta_rep', 'grade_label'])['name_first_learner'].count().reset_index()
                ta_assessments.columns = ['School', 'TA', 'Grade', 'Count']
                st.dataframe(ta_assessments, width='stretch')


    except Exception as e:
        st.error(f"Error processing data: {str(e)}")
        st.stop()