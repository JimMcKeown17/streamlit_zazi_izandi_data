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
st.title("2025 Initial Assessments")
# st.info("Utilizing SurveyCTO's EGRA Plugin. As of Jan 25, 2025, we have 41 TAs starting with assessments. The next 40 will begin once their TLT contracts are signed.")

# Read and process data
try:
    df, df_ecd = load_egra_data(
        children_filename="EGRA form [Eastern Cape]-assessment_repeat - Apr 10.csv",
        ta_filename="EGRA form [Eastern Cape] - Apr 10.csv"
    )

    # START OF PAGE

    col1, col2, col3 = st.columns(3)

    with col1:# Total Assessed
        st.metric("Total Number of Children Assessed", len(df))

    with col2:
        # Number of TAs that assessed >= 20 kids
        ta_counts = df['name_ta_rep'].value_counts()
        ta_more_than_20 = ta_counts[ta_counts >= 20]
        st.metric("TAs That Assessed > 20 Children", f'{len(ta_more_than_20)}')

    with col3:
        # Number of TAs that submitted anything
        ta_counts = df['name_ta_rep'].value_counts()
        st.metric("TAs That Submitted Results (1+ Children)", f'{len(ta_counts)}')


    st.divider()

    # Grade Summary
    with st.container():
        st.subheader("EGRA Letters per Grade")
        grade_summary = df.groupby(['grade_label']).agg(
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

        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Show results"):
            st.dataframe(grade_summary, use_container_width=True)

    st.divider()

    # Assessments Per TA
    with st.container():
        st.subheader("Assessments Per TA")

        ta_counts = df['name_ta_rep'].value_counts().reset_index()
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


        st.plotly_chart(fig, use_container_width=True)

    with st.container():
        st.subheader("Assessments Per School & Grade")

        # Group by school and grade, counting the number of assessments
        school_grade_counts = (
            df.groupby(['school_rep', 'grade'])
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
        st.plotly_chart(fig, use_container_width=True)

    with st.container():
        st.subheader("Assessments Per School & Grade")

        # Group by school and grade, counting the number of assessments
        school_class_counts = (
            df.groupby(['school_rep','class'])
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
        st.plotly_chart(fig, use_container_width=True)

    # TA Assessments Summary
    with st.container():
        st.header("Assessments Completed Per School & TA")
        ta_assessments = df.groupby(['school_rep', 'name_ta_rep', 'grade_label'])['name_first_learner'].count().reset_index()
        ta_assessments.columns = ['School', 'TA', 'Grade', 'Count']
        st.dataframe(ta_assessments, use_container_width=True)

    # School Summary
    with st.container():
        st.header("School Summary")
        school_summary = df.groupby(['school_rep', 'grade_label']).agg(
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

    # Grade 1 Non-Words Summary
    with st.container():
        st.header("Grade 1 Non-Words Summary")
        g1 = df[df['grade_label'] == 'Grade 1']
        school_non_words_summary = g1.groupby(['school_rep', 'class']).agg(
            Number_Assessed=('name_first_learner', 'count'),
            Average_NonWords_Correct=('nonwords_correct_a1', 'mean')
        ).reset_index()
        school_non_words_summary['Average_NonWords_Correct'] = school_non_words_summary['Average_NonWords_Correct'].round(1)
        school_non_words_summary = school_non_words_summary.sort_values(by='Average_NonWords_Correct', ascending=False)

        # Setting a filter for which results end up displayed on the chart.
        school_non_words_summary = school_non_words_summary[school_non_words_summary['Number_Assessed'] > 10]

        fig = px.bar(
            school_non_words_summary,
            x="school_rep",
            y="Average_NonWords_Correct",
            color="class",
            barmode="group",
            title="Average Non-Words Correct by School and Class",
            labels={
                "school_rep": "School",
                "Average_NonWords_Correct": "Average Non-Words Correct",
                "class": "Class"
            },
            color_discrete_sequence=px.colors.qualitative.Set2  # Optional: Use a qualitative color scheme
        )

        # Customize chart layout
        fig.update_layout(
            xaxis_title="School",
            yaxis_title="Average Non-Words Correct",
            legend_title="Class",
        )

        # Display the chart in Streamlit
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(school_non_words_summary, use_container_width=True)

    # Grade 1 Words Summary
    with st.container():
        st.header("Grade 1 Words Summary")
        school_words_summary = g1.groupby(['school_rep', 'class']).agg(
            Number_Assessed=('name_first_learner', 'count'),
            Average_Words_Correct=('words_correct_a1', 'mean')
        ).reset_index()
        school_words_summary['Average_Words_Correct'] = school_words_summary['Average_Words_Correct'].round(1)
        school_words_summary = school_words_summary.sort_values(by='Average_Words_Correct', ascending=False)

        # Setting a filter for which results end up displayed on the chart.
        school_words_summary = school_words_summary[school_words_summary['Number_Assessed'] > 10]


        fig = px.bar(
            school_words_summary,
            x="school_rep",  # Schools on the x-axis
            y="Average_Words_Correct",  # Values for the y-axis
            color="class",  # Differentiate bars by class
            barmode="group",  # Grouped bars for classes
            title="Average Words Correct by School and Class",
            labels={
                "school_rep": "School",
                "Average_Words_Correct": "Average Words Correct",
                "class": "Class"
            },
            color_discrete_sequence=px.colors.qualitative.Set2  # Optional: Use a qualitative color scheme
        )

        # Customize chart layout
        fig.update_layout(
            xaxis_title="School",
            yaxis_title="Average Words Correct",
            legend_title="Class",
        )

        # Display the chart in Streamlit
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(school_words_summary, use_container_width=True)

    st.divider()


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


    with st.container():
        st.subheader("Data Export Tools")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("Generate Letter Tracker CSV (w Groups)"):
                try:
                    letter_tracker_df = create_letter_tracker(df, export_csv=False)
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
                    csv = df.to_csv(index=False)
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
                    zip_data = generate_letter_tracker_pdfs(df)
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

except Exception as e:
    st.error(f"Error processing data: {str(e)}")
    st.stop()