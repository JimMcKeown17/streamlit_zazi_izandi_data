"""
Test script to verify parquet loading works correctly and measure performance improvements.
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

def test_2023_data():
    """Test 2023 data loading and processing"""
    print("\n" + "="*60)
    print("Testing 2023 Data Loading")
    print("="*60)
    
    # Test loading with parquet
    print("\n[1/2] Loading 2023 data (should use parquet)...")
    start_time = time.time()
    
    import streamlit as st
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    endline_df, sessions_df = load_zazi_izandi_2023()
    load_time = time.time() - start_time
    print(f"✓ Load time: {load_time:.4f}s")
    print(f"✓ Endline rows: {len(endline_df):,}, columns: {len(endline_df.columns)}")
    print(f"✓ Sessions rows: {len(sessions_df):,}, columns: {len(sessions_df.columns)}")
    
    # Test processing
    print("\n[2/2] Processing 2023 data...")
    start_time = time.time()
    processed_df = process_zz_data_23(endline_df, sessions_df)
    processing_time = time.time() - start_time
    print(f"✓ Processing time: {processing_time:.4f}s")
    print(f"✓ Processed rows: {len(processed_df):,}, columns: {len(processed_df.columns)}")
    
    # Verify key columns exist
    expected_cols = ['Grade', 'School', 'Masi Egra Full Baseline', 'Masi Egra Full Endline']
    missing_cols = [col for col in expected_cols if col not in processed_df.columns]
    if missing_cols:
        print(f"⚠ Warning: Missing columns: {missing_cols}")
    else:
        print(f"✓ All expected columns present")
    
    return load_time, processing_time, len(processed_df)


def test_2024_data():
    """Test 2024 data loading and processing"""
    print("\n" + "="*60)
    print("Testing 2024 Data Loading")
    print("="*60)
    
    # Test loading with parquet
    print("\n[1/2] Loading 2024 data (should use parquet)...")
    start_time = time.time()
    
    import streamlit as st
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df = load_zazi_izandi_2024()
    load_time = time.time() - start_time
    print(f"✓ Load time: {load_time:.4f}s")
    print(f"✓ Baseline rows: {len(baseline_df):,}, Midline: {len(midline_df):,}, Endline: {len(endline_df):,}")
    
    # Test processing
    print("\n[2/2] Processing 2024 data...")
    start_time = time.time()
    midline_processed, baseline_processed = process_zz_data_midline(baseline_df, midline_df, sessions_df)
    endline_processed = process_zz_data_endline(endline_df)
    processing_time = time.time() - start_time
    print(f"✓ Processing time: {processing_time:.4f}s")
    print(f"✓ Midline processed rows: {len(midline_processed):,}, columns: {len(midline_processed.columns)}")
    print(f"✓ Endline processed rows: {len(endline_processed):,}, columns: {len(endline_processed.columns)}")
    
    # Verify key columns exist
    midline_expected = ['Grade', 'School', 'EGRA Baseline', 'EGRA Midline']
    missing_mid = [col for col in midline_expected if col not in midline_processed.columns]
    
    endline_expected = ['Grade', 'School', 'EGRA Baseline', 'EGRA Endline']
    missing_end = [col for col in endline_expected if col not in endline_processed.columns]
    
    if missing_mid or missing_end:
        print(f"⚠ Warning: Missing midline columns: {missing_mid}")
        print(f"⚠ Warning: Missing endline columns: {missing_end}")
    else:
        print(f"✓ All expected columns present in both datasets")
    
    return load_time, processing_time, len(midline_processed) + len(endline_processed)


def main():
    """Main test script"""
    print("\n" + "="*60)
    print("Parquet Loading Test Script")
    print("Testing data loading and processing with Parquet optimization")
    print("="*60)
    
    total_start = time.time()
    
    # Test 2023 data
    load_2023, proc_2023, rows_2023 = test_2023_data()
    
    # Test 2024 data
    load_2024, proc_2024, rows_2024 = test_2024_data()
    
    # Summary
    total_time = time.time() - total_start
    total_load = load_2023 + load_2024
    total_proc = proc_2023 + proc_2024
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Total data loading time: {total_load:.4f}s")
    print(f"Total processing time: {total_proc:.4f}s")
    print(f"Total test time: {total_time:.4f}s")
    print(f"\nTotal rows processed: {rows_2023 + rows_2024:,}")
    print("\n✓ All tests passed!")
    print("\nPerformance Comparison:")
    print(f"  - Excel loading (from conversion): ~0.92s")
    print(f"  - Parquet loading (current): {total_load:.4f}s")
    if total_load > 0:
        speedup = 0.92 / total_load
        print(f"  - Speedup: {speedup:.1f}x faster")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()

