import streamlit as st
import pandas as pd
import plotly.express as px
from process_survey_cto_updated import process_egra_data
import os
from datetime import datetime as dt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def show():
    # Check authentication
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Execute the content from the original 2025 results page - Midline tab only
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

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

                st.plotly_chart(egra_fig, use_container_width=True)

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

                st.plotly_chart(grade_level_fig, use_container_width=True)

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

                st.plotly_chart(fig, use_container_width=True)

                st.dataframe(school_summary, use_container_width=True)

            st.divider()
            
            # Add this section after your existing Grade 1 analyses
            with st.container():
                st.header("Grade 1 Learners Hitting Benchmark")
                st.info("This is a measure of how many Grade 1 learners are hitting the benchmark of 40 letters correct.")

                # Filter for Grade 1 only
                g1_letter_scores = midline_df[midline_df['grade_label'] == 'Grade 1']

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
                st.plotly_chart(fig, use_container_width=True)

                # Show summary stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Grade 1 Students", total_g1_students)
                with col2:
                    st.metric("Students with Score >= 40", students_above_40)
                with col3:
                    st.metric("Percentage Above 40", f"{percentage_above_40:.1f}%")

            st.divider()
            
            # Grade 1 Benchmark by School
            with st.container():
                st.header("Grade 1 Benchmark by School")

                # Filter for Grade 1 only
                g1_letter_scores = midline_df[midline_df['grade_label'] == 'Grade 1']

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
                st.plotly_chart(fig, use_container_width=True)

                # Show detailed table
                st.dataframe(school_letter_score_summary, use_container_width=True)

            st.divider()

            # Baseline vs Midline Comparison by School
            with st.container():
                st.header("Baseline vs Midline Comparison by School")
                
                # Grade selection dropdown for both charts
                grade_selection = st.selectbox(
                    "Select Grade for Comparison Charts:",
                    ["Grade R", "Grade 1"],
                    key="grade_comparison_selector"
                )

                st.subheader(f"1. Average Letters Correct - {grade_selection}")
                
                # Filter data for selected grade
                baseline_grade_data = initial_df[initial_df['grade_label'] == grade_selection]
                midline_grade_data = midline_df[midline_df['grade_label'] == grade_selection]
                
                # Calculate baseline averages by school
                baseline_school_avg = baseline_grade_data.groupby('school_rep')['letters_correct_a1'].mean().reset_index()
                baseline_school_avg.columns = ['School', 'Baseline Avg']
                baseline_school_avg['Baseline Avg'] = baseline_school_avg['Baseline Avg'].round(1)
                
                # Calculate midline averages by school
                midline_school_avg = midline_grade_data.groupby('school_rep')['letters_correct_a1'].mean().reset_index()
                midline_school_avg.columns = ['School', 'Midline Avg']
                midline_school_avg['Midline Avg'] = midline_school_avg['Midline Avg'].round(1)
                
                # Merge baseline and midline data
                school_comparison = pd.merge(baseline_school_avg, midline_school_avg, on='School', how='outer')
                school_comparison = school_comparison.fillna(0)  # Fill NaN with 0 for schools not in both datasets
                
                # Calculate improvement and sort by it
                school_comparison['Improvement'] = school_comparison['Midline Avg'] - school_comparison['Baseline Avg']
                school_comparison = school_comparison.sort_values(by='Improvement', ascending=False)
                
                # Melt the DataFrame for Plotly grouped bar chart
                school_comparison_melted = school_comparison.melt(
                    id_vars=['School', 'Improvement'],
                    value_vars=['Baseline Avg', 'Midline Avg'],
                    var_name='Assessment Period',
                    value_name='Average Letters Correct'
                )
                
                # Create grouped bar chart with custom order
                fig = px.bar(
                    school_comparison_melted,
                    x='School',
                    y='Average Letters Correct',
                    color='Assessment Period',
                    barmode='group',
                    title=f'Baseline vs Midline Average Letters Correct by School - {grade_selection}',
                    labels={'School': 'School', 'Average Letters Correct': 'Average Letters Correct'},
                    color_discrete_map={'Baseline Avg': '#b3b3b3', 'Midline Avg': '#ffd641'},
                    category_orders={'School': school_comparison['School'].tolist()}  # Custom order by improvement
                )
                
                fig.update_layout(
                    xaxis_title="School",
                    yaxis_title="Average Letters Correct",
                    legend_title="Assessment Period"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander(f'View {grade_selection} Average Data'):
                    st.dataframe(school_comparison, use_container_width=True)

                st.subheader(f"2. Percentage at Benchmark (≥40) - {grade_selection}")
                
                # Calculate baseline benchmark percentages by school
                baseline_benchmark = baseline_grade_data.groupby('school_rep').agg(
                    Total_Assessed=('name_first_learner', 'count'),
                    Above_40_Count=('letters_correct_a1', lambda x: (x >= 40).sum())
                ).reset_index()
                baseline_benchmark['Baseline %'] = (
                    baseline_benchmark['Above_40_Count'] / baseline_benchmark['Total_Assessed'] * 100
                ).round(1)
                baseline_benchmark = baseline_benchmark[['school_rep', 'Baseline %']]
                baseline_benchmark.columns = ['School', 'Baseline %']
                
                # Calculate midline benchmark percentages by school
                midline_benchmark = midline_grade_data.groupby('school_rep').agg(
                    Total_Assessed=('name_first_learner', 'count'),
                    Above_40_Count=('letters_correct_a1', lambda x: (x >= 40).sum())
                ).reset_index()
                midline_benchmark['Midline %'] = (
                    midline_benchmark['Above_40_Count'] / midline_benchmark['Total_Assessed'] * 100
                ).round(1)
                midline_benchmark = midline_benchmark[['school_rep', 'Midline %']]
                midline_benchmark.columns = ['School', 'Midline %']
                
                # Merge baseline and midline benchmark data
                benchmark_comparison = pd.merge(baseline_benchmark, midline_benchmark, on='School', how='outer')
                benchmark_comparison = benchmark_comparison.fillna(0)  # Fill NaN with 0 for schools not in both datasets
                
                # Calculate improvement and sort by it
                benchmark_comparison['Improvement'] = benchmark_comparison['Midline %'] - benchmark_comparison['Baseline %']
                benchmark_comparison = benchmark_comparison.sort_values(by='Improvement', ascending=False)
                
                # Melt the DataFrame for Plotly grouped bar chart
                benchmark_comparison_melted = benchmark_comparison.melt(
                    id_vars=['School', 'Improvement'],
                    value_vars=['Baseline %', 'Midline %'],
                    var_name='Assessment Period',
                    value_name='Percentage at Benchmark'
                )
                
                # Create grouped bar chart with custom order
                fig = px.bar(
                    benchmark_comparison_melted,
                    x='School',
                    y='Percentage at Benchmark',
                    color='Assessment Period',
                    barmode='group',
                    title=f'Baseline vs Midline Percentage at Benchmark by School - {grade_selection}',
                    labels={'School': 'School', 'Percentage at Benchmark': 'Percentage at Benchmark (%)'},
                    color_discrete_map={'Baseline %': '#b3b3b3', 'Midline %': '#32c93c'},
                    category_orders={'School': benchmark_comparison['School'].tolist()}  # Custom order by improvement
                )
                
                fig.update_layout(
                    xaxis_title="School",
                    yaxis_title="Percentage at Benchmark (%)",
                    legend_title="Assessment Period",
                    yaxis_range=[0, 100]  # Set y-axis from 0 to 100%
                )
                
                # Add horizontal line at national average
                fig.add_hline(
                    y=27,
                    line_dash='dash',
                    line_color='red',
                    annotation_text='South Africa Average (27%)',
                    annotation_position='top left'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander(f'View {grade_selection} Benchmark Data'):
                    st.dataframe(benchmark_comparison, use_container_width=True)
            
            # OpenAI Analysis Section
            st.divider()
            with st.container():
                st.header("🤖 AI Data Analysis")
                st.write("Get insights from OpenAI's ChatGPT about your assessment data")
                
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
                                # Import the analysis function
                                from openai_analysis import analyze_data_with_openai
                                
                                analysis = analyze_data_with_openai(
                                    midline_df, 
                                    analysis_type=analysis_type, 
                                    custom_questions=custom_questions,
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
                                st.error("❌ OpenAI analysis module not found. Please ensure openai_analysis.py is in your project directory.")
                            except Exception as e:
                                st.error(f"❌ Error during analysis: {str(e)}")
                
                # Quick data preview for context
                with st.expander("📊 Data Preview", expanded=False):
                    st.write(f"**Total Students:** {len(midline_df)}")
                    st.write(f"**Schools:** {midline_df['school_rep'].nunique()}")
                    st.write(f"**Teaching Assistants:** {midline_df['name_ta_rep'].nunique()}")
                    st.write("**Sample Data:**")
                    st.dataframe(midline_df[['school_rep', 'grade_label', 'letters_correct', 'name_ta_rep']].head(), use_container_width=True)

    except Exception as e:
        st.error(f"Error loading data: {e}") 