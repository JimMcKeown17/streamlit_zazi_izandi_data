import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="EGRA Data Processor", layout="wide")


def main():
    st.title("EGRA Data Processing Tool")

    st.markdown("""
    ### Instructions
    1. Upload both required CSV files
    2. We'll display basic information about the files
    """)

    # File uploaders
    children_file = st.file_uploader(
        "Upload Children Assessment CSV file",
        type=['csv']
    )

    ta_file = st.file_uploader(
        "Upload TA CSV file",
        type=['csv']
    )

    if children_file is not None:
        try:
            df_children = pd.read_csv(children_file)
            st.write("Children file successfully uploaded!")
            st.write(f"Number of rows: {len(df_children)}")
            st.write(f"Columns: {df_children.columns.tolist()}")
        except Exception as e:
            st.error(f"Error reading children file: {str(e)}")

    if ta_file is not None:
        try:
            df_ta = pd.read_csv(ta_file)
            st.write("TA file successfully uploaded!")
            st.write(f"Number of rows: {len(df_ta)}")
            st.write(f"Columns: {df_ta.columns.tolist()}")
        except Exception as e:
            st.error(f"Error reading TA file: {str(e)}")


if __name__ == "__main__":
    main()