"""
Convert 2023 and 2024 Excel data to Parquet format for faster loading.

This script:
1. Loads all 2023 & 2024 Excel files
2. Saves raw DataFrames to data/parquet/raw/
3. Runs processing functions
4. Saves processed DataFrames to data/parquet/processed/
5. Reports file sizes and performance metrics
"""

import pandas as pd
import os
import sys
import time
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Import data loading and processing functions
from data_loader import load_zazi_izandi_2023, load_zazi_izandi_2024
from zz_data_process_23 import process_zz_data_23
from zz_data_processing import process_zz_data_midline, process_zz_data_endline

# Create directories if they don't exist
RAW_DIR = ROOT_DIR / "data" / "parquet" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "parquet" / "processed"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def format_size(bytes_size):
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def clean_dataframe_for_parquet(df):
    """
    Clean DataFrame to ensure parquet compatibility.
    Converts object columns with mixed types to strings.
    """
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == 'object':
            # Convert object columns to string, handling NaN
            df[col] = df[col].astype(str).replace('nan', None)
    return df


def get_file_size(path):
    """Get file size in bytes"""
    if os.path.exists(path):
        return os.path.getsize(path)
    return 0


def convert_2023_data():
    """Convert 2023 data to Parquet"""
    print("\n" + "="*60)
    print("Converting 2023 Data")
    print("="*60)
    
    # Load raw data from Excel
    print("\n[1/3] Loading 2023 Excel files...")
    start_time = time.time()
    
    # Temporarily set streamlit session state to load anonymized data
    import streamlit as st
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    endline_df, sessions_df = load_zazi_izandi_2023()
    excel_load_time = time.time() - start_time
    print(f"✓ Excel load time: {excel_load_time:.2f}s")
    
    # Save raw DataFrames
    print("\n[2/3] Saving raw Parquet files...")
    raw_endline_path = RAW_DIR / "2023_endline.parquet"
    raw_sessions_path = RAW_DIR / "2023_sessions.parquet"
    
    # Clean DataFrames for parquet compatibility
    endline_df_clean = clean_dataframe_for_parquet(endline_df)
    sessions_df_clean = clean_dataframe_for_parquet(sessions_df)
    
    endline_df_clean.to_parquet(raw_endline_path, index=False, compression='snappy')
    sessions_df_clean.to_parquet(raw_sessions_path, index=False, compression='snappy')
    
    raw_endline_size = get_file_size(raw_endline_path)
    raw_sessions_size = get_file_size(raw_sessions_path)
    
    print(f"✓ Raw endline: {format_size(raw_endline_size)}")
    print(f"✓ Raw sessions: {format_size(raw_sessions_size)}")
    
    # Process data
    print("\n[3/3] Processing and saving processed Parquet...")
    start_time = time.time()
    processed_df = process_zz_data_23(endline_df, sessions_df)
    processing_time = time.time() - start_time
    print(f"✓ Processing time: {processing_time:.2f}s")
    
    processed_path = PROCESSED_DIR / "2023_processed.parquet"
    processed_df_clean = clean_dataframe_for_parquet(processed_df)
    processed_df_clean.to_parquet(processed_path, index=False, compression='snappy')
    processed_size = get_file_size(processed_path)
    
    print(f"✓ Processed file: {format_size(processed_size)}")
    print(f"\n✓ 2023 data conversion complete!")
    
    return excel_load_time


def convert_2024_data():
    """Convert 2024 data to Parquet"""
    print("\n" + "="*60)
    print("Converting 2024 Data")
    print("="*60)
    
    # Load raw data from Excel
    print("\n[1/3] Loading 2024 Excel files...")
    start_time = time.time()
    
    # Temporarily set streamlit session state to load anonymized data
    import streamlit as st
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df = load_zazi_izandi_2024()
    excel_load_time = time.time() - start_time
    print(f"✓ Excel load time: {excel_load_time:.2f}s")
    
    # Save raw DataFrames
    print("\n[2/3] Saving raw Parquet files...")
    raw_files = {
        "2024_baseline.parquet": baseline_df,
        "2024_midline.parquet": midline_df,
        "2024_sessions.parquet": sessions_df,
        "2024_baseline2.parquet": baseline2_df,
        "2024_endline.parquet": endline_df,
        "2024_endline2.parquet": endline2_df,
    }
    
    total_raw_size = 0
    for filename, df in raw_files.items():
        path = RAW_DIR / filename
        df_clean = clean_dataframe_for_parquet(df)
        df_clean.to_parquet(path, index=False, compression='snappy')
        size = get_file_size(path)
        total_raw_size += size
        print(f"✓ {filename}: {format_size(size)}")
    
    # Process data
    print("\n[3/3] Processing and saving processed Parquet...")
    start_time = time.time()
    
    # Process midline and baseline
    midline_processed, baseline_processed = process_zz_data_midline(baseline_df, midline_df, sessions_df)
    
    # Process endline
    endline_processed = process_zz_data_endline(endline_df)
    
    processing_time = time.time() - start_time
    print(f"✓ Processing time: {processing_time:.2f}s")
    
    # Save processed DataFrames
    processed_files = {
        "2024_midline_processed.parquet": midline_processed,
        "2024_baseline_processed.parquet": baseline_processed,
        "2024_endline_processed.parquet": endline_processed,
    }
    
    total_processed_size = 0
    for filename, df in processed_files.items():
        path = PROCESSED_DIR / filename
        df_clean = clean_dataframe_for_parquet(df)
        df_clean.to_parquet(path, index=False, compression='snappy')
        size = get_file_size(path)
        total_processed_size += size
        print(f"✓ {filename}: {format_size(size)}")
    
    print(f"\n✓ 2024 data conversion complete!")
    print(f"Total raw size: {format_size(total_raw_size)}")
    print(f"Total processed size: {format_size(total_processed_size)}")
    
    return excel_load_time


def test_parquet_loading():
    """Test loading speed of Parquet files"""
    print("\n" + "="*60)
    print("Testing Parquet Load Performance")
    print("="*60)
    
    # Test 2023 processed
    print("\n2023 Processed Data:")
    path = PROCESSED_DIR / "2023_processed.parquet"
    start_time = time.time()
    df = pd.read_parquet(path)
    load_time = time.time() - start_time
    print(f"✓ Load time: {load_time:.4f}s")
    print(f"✓ Rows: {len(df):,}")
    print(f"✓ Columns: {len(df.columns)}")
    
    # Test 2024 processed
    print("\n2024 Midline Processed Data:")
    path = PROCESSED_DIR / "2024_midline_processed.parquet"
    start_time = time.time()
    df = pd.read_parquet(path)
    load_time = time.time() - start_time
    print(f"✓ Load time: {load_time:.4f}s")
    print(f"✓ Rows: {len(df):,}")
    print(f"✓ Columns: {len(df.columns)}")
    
    print("\n2024 Endline Processed Data:")
    path = PROCESSED_DIR / "2024_endline_processed.parquet"
    start_time = time.time()
    df = pd.read_parquet(path)
    load_time = time.time() - start_time
    print(f"✓ Load time: {load_time:.4f}s")
    print(f"✓ Rows: {len(df):,}")
    print(f"✓ Columns: {len(df.columns)}")


def main():
    """Main conversion script"""
    print("\n" + "="*60)
    print("Parquet Conversion Script")
    print("Converting 2023-2024 Data to Parquet Format")
    print("="*60)
    
    total_start = time.time()
    
    # Convert 2023 data
    excel_time_2023 = convert_2023_data()
    
    # Convert 2024 data
    excel_time_2024 = convert_2024_data()
    
    # Test Parquet loading
    test_parquet_loading()
    
    # Summary
    total_time = time.time() - total_start
    total_excel_time = excel_time_2023 + excel_time_2024
    
    print("\n" + "="*60)
    print("Conversion Summary")
    print("="*60)
    print(f"Total Excel load time: {total_excel_time:.2f}s")
    print(f"Total conversion time: {total_time:.2f}s")
    print(f"Expected Parquet speedup: {total_excel_time / 0.5:.1f}x faster")
    print("\n✓ All conversions complete!")
    print(f"✓ Raw files saved to: {RAW_DIR}")
    print(f"✓ Processed files saved to: {PROCESSED_DIR}")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()

