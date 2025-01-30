import streamlit as st
import os
import pandas as pd
import pdfkit
from process_survey_cto_updated import process_egra_data
from create_letter_tracker import create_letter_tracker
from letter_tracker_htmls import main as create_html_reports
import tempfile
import shutil
import zipfile
import io

# Initialize session state
if 'process_complete' not in st.session_state:
    st.session_state.process_complete = False


def read_file_chunk(uploaded_file):
    """Read uploaded file in chunks to handle large files"""
    chunk_size = 1024 * 1024  # 1MB chunks
    buffer = io.StringIO()

    while True:
        chunk = uploaded_file.read(chunk_size)
        if not chunk:
            break
        buffer.write(chunk.decode('utf-8'))

    buffer.seek(0)
    return buffer


def process_files(children_file, ta_file):
    """Process the uploaded files through all steps"""
    temp_dir = None
    try:
        # Create temporary directories
        temp_dir = tempfile.mkdtemp()
        html_dir = os.path.join(temp_dir, 'html_reports')
        pdf_dir = os.path.join(temp_dir, 'pdf_trackers')
        os.makedirs(html_dir, exist_ok=True)
        os.makedirs(pdf_dir, exist_ok=True)

        # Save uploaded files to temp directory
        children_path = os.path.join(temp_dir, "children.csv")
        ta_path = os.path.join(temp_dir, "ta.csv")

        # Read and save files in chunks
        with open(children_path, 'w') as f:
            children_content = read_file_chunk(children_file)
            f.write(children_content.getvalue())

        with open(ta_path, 'w') as f:
            ta_content = read_file_chunk(ta_file)
            f.write(ta_content.getvalue())

        # Step 1: Process EGRA data
        with st.spinner('Processing EGRA data...'):
            df = process_egra_data(
                children_file=children_path,
                ta_file=ta_path
            )
            st.success('✅ EGRA data processed successfully')

        # Step 2: Create letter tracker
        with st.spinner('Creating letter tracker...'):
            letter_tracker_path = os.path.join(temp_dir, 'Letter Tracker.csv')
            create_letter_tracker(df, export_csv=True, output_path=letter_tracker_path)
            st.success('✅ Letter tracker created successfully')

        # Step 3: Generate HTML reports
        with st.spinner('Generating HTML reports...'):
            original_dir = os.getcwd()
            os.chdir(temp_dir)
            create_html_reports()
            os.chdir(original_dir)
            st.success('✅ HTML reports generated successfully')

        # Step 4: Convert to PDF
        with st.spinner('Converting to PDF...'):
            options = {
                'orientation': 'Landscape',
                'page-size': 'A4',
                'margin-top': '0.25in',
                'margin-bottom': '0.25in',
                'margin-left': '0.25in',
                'margin-right': '0.25in',
            }

            for filename in os.listdir(html_dir):
                if filename.lower().endswith(".html"):
                    input_path = os.path.join(html_dir, filename)
                    output_path = os.path.join(
                        pdf_dir,
                        os.path.splitext(filename)[0] + ".pdf"
                    )
                    try:
                        pdfkit.from_file(input_path, output_path, options=options)
                    except Exception as e:
                        st.error(f"Error converting {filename} to PDF: {str(e)}")
                        continue
            st.success('✅ PDFs created successfully')

        # Create zip file of PDFs
        zip_path = os.path.join(temp_dir, 'letter_trackers.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(pdf_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, pdf_dir)
                    zipf.write(file_path, arcname)

        return zip_path, temp_dir

    except Exception as e:
        st.error(f'An error occurred during processing: {str(e)}')
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return None, None


def main():
    st.title("EGRA Data Processing Tool")

    st.markdown("""
    ### Instructions
    1. Upload both required CSV files
    2. Click 'Process Files' to generate the letter trackers
    3. Download the generated PDF reports
    """)

    # Split the upload interface into two columns
    col1, col2 = st.columns(2)

    with col1:
        children_file = st.file_uploader(
            "Upload Children Assessment CSV file",
            type=['csv'],
            help="Upload the EGRA form-assessment_repeat CSV file",
            key='children_file'
        )

    with col2:
        ta_file = st.file_uploader(
            "Upload TA CSV file",
            type=['csv'],
            help="Upload the EGRA form CSV file",
            key='ta_file'
        )

    # Add some spacing
    st.write("")

    if children_file is not None and ta_file is not None:
        if st.button("Process Files", type="primary", key='process_button'):
            try:
                # Process files
                zip_path, temp_dir = process_files(children_file, ta_file)

                if zip_path and os.path.exists(zip_path):
                    st.session_state.process_complete = True
                    # Create download button
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            label="Download PDF Letter Trackers",
                            data=f,
                            file_name="letter_trackers.zip",
                            mime="application/zip",
                            key='download_button'
                        )

                    # Cleanup
                    if temp_dir and os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)

            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
                st.session_state.process_complete = False

    # Add deployment information
    st.sidebar.markdown("""
    ### Deployment Information
    This app can be deployed using:
    - Streamlit Cloud
    - Heroku
    - AWS
    - Google Cloud Platform

    Make sure to install `wkhtmltopdf` on the deployment server:
    ```bash
    # Ubuntu/Debian
    apt-get install wkhtmltopdf

    # CentOS/RHEL
    yum install wkhtmltopdf
    ```
    """)


if __name__ == "__main__":
    main()