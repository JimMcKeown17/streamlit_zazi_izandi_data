"""
Verify data integrity after parquet conversion.
Compare Excel vs Parquet data to ensure no values were corrupted.
"""

import pandas as pd
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

def compare_dataframes(df_excel, df_parquet, name):
    """Compare two dataframes for differences"""
    print(f"\n{'='*60}")
    print(f"Comparing {name}")
    print(f"{'='*60}")
    
    # Check shapes
    if df_excel.shape != df_parquet.shape:
        print(f"⚠ WARNING: Shape mismatch!")
        print(f"  Excel: {df_excel.shape}, Parquet: {df_parquet.shape}")
        return False
    else:
        print(f"✓ Shape match: {df_excel.shape}")
    
    # Check column dtypes
    print(f"\nColumn Data Types Comparison:")
    dtype_differences = []
    for col in df_excel.columns:
        if col in df_parquet.columns:
            excel_dtype = df_excel[col].dtype
            parquet_dtype = df_parquet[col].dtype
            if excel_dtype != parquet_dtype:
                dtype_differences.append({
                    'column': col,
                    'excel_dtype': excel_dtype,
                    'parquet_dtype': parquet_dtype
                })
    
    if dtype_differences:
        print(f"\n⚠ Found {len(dtype_differences)} columns with different dtypes:")
        for diff in dtype_differences[:10]:  # Show first 10
            print(f"  - {diff['column']}: {diff['excel_dtype']} → {diff['parquet_dtype']}")
        if len(dtype_differences) > 10:
            print(f"  ... and {len(dtype_differences) - 10} more")
    else:
        print("✓ All dtypes match")
    
    # Check numeric columns for value differences
    print(f"\nChecking numeric columns for value changes:")
    numeric_cols = df_excel.select_dtypes(include=['int64', 'float64']).columns
    value_issues = []
    
    for col in numeric_cols:
        if col in df_parquet.columns:
            # Convert parquet column to numeric for comparison
            parquet_numeric = pd.to_numeric(df_parquet[col], errors='coerce')
            
            # Compare non-null values
            excel_values = df_excel[col].dropna()
            parquet_values = parquet_numeric[df_excel[col].notna()]
            
            if len(excel_values) > 0:
                # Check if values are approximately equal
                try:
                    if not excel_values.equals(parquet_values):
                        # Check if they're numerically close
                        diff = (excel_values.values - parquet_values.values)
                        max_diff = abs(diff).max()
                        if max_diff > 0.0001:  # Allow for floating point precision
                            value_issues.append({
                                'column': col,
                                'max_difference': max_diff,
                                'excel_sample': excel_values.head(3).tolist(),
                                'parquet_sample': parquet_values.head(3).tolist()
                            })
                except Exception as e:
                    value_issues.append({
                        'column': col,
                        'error': str(e)
                    })
    
    if value_issues:
        print(f"⚠ WARNING: Found {len(value_issues)} columns with value differences:")
        for issue in value_issues[:5]:  # Show first 5
            print(f"  - {issue['column']}:")
            if 'error' in issue:
                print(f"    Error: {issue['error']}")
            else:
                print(f"    Max difference: {issue.get('max_difference', 'N/A')}")
                print(f"    Excel sample: {issue.get('excel_sample', [])}")
                print(f"    Parquet sample: {issue.get('parquet_sample', [])}")
    else:
        print(f"✓ All {len(numeric_cols)} numeric columns have matching values")
    
    # Check for new NaN values
    print(f"\nChecking for introduced NaN values:")
    nan_issues = []
    for col in df_excel.columns:
        if col in df_parquet.columns:
            excel_nulls = df_excel[col].isna().sum()
            parquet_nulls = pd.to_numeric(df_parquet[col], errors='coerce').isna().sum()
            
            if parquet_nulls > excel_nulls:
                nan_issues.append({
                    'column': col,
                    'excel_nulls': excel_nulls,
                    'parquet_nulls': parquet_nulls,
                    'new_nulls': parquet_nulls - excel_nulls
                })
    
    if nan_issues:
        print(f"⚠ WARNING: Found {len(nan_issues)} columns with new NaN values:")
        for issue in nan_issues[:10]:
            print(f"  - {issue['column']}: {issue['excel_nulls']} → {issue['parquet_nulls']} (+{issue['new_nulls']} new NaNs)")
    else:
        print("✓ No new NaN values introduced")
    
    return len(dtype_differences) == 0 and len(value_issues) == 0 and len(nan_issues) == 0


def main():
    """Main verification script"""
    print("\n" + "="*60)
    print("Data Integrity Verification")
    print("Comparing Excel vs Parquet Data")
    print("="*60)
    
    import streamlit as st
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    # Test 2023 data
    print("\n[1/2] Loading 2023 data from both sources...")
    
    # Load from Excel
    dir_path = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(dir_path, "../data/ZZ Children's Database 2023 (Endline) 20231130 - anonymized.xlsx")
    df_2023_excel = pd.read_excel(excel_path, sheet_name="Database", engine='openpyxl')
    
    # Load from Parquet
    parquet_path = os.path.join(dir_path, "../data/parquet/raw/2023_endline.parquet")
    df_2023_parquet = pd.read_parquet(parquet_path)
    
    # Convert numeric columns back
    numeric_cols = ['Mcode']
    for col in numeric_cols:
        if col in df_2023_parquet.columns:
            df_2023_parquet[col] = pd.to_numeric(df_2023_parquet[col], errors='coerce')
    
    compare_dataframes(df_2023_excel, df_2023_parquet, "2023 Endline Data")
    
    # Test 2024 data
    print("\n[2/2] Loading 2024 data from both sources...")
    
    # Load from Excel
    excel_path_2024 = os.path.join(dir_path, "../data/Zazi iZandi Children's database (Baseline)7052024 - anonymized.xlsx")
    df_2024_excel = pd.read_excel(excel_path_2024, sheet_name="ZZ Childrens Database", engine='openpyxl')
    
    # Load from Parquet
    parquet_path_2024 = os.path.join(dir_path, "../data/parquet/raw/2024_baseline.parquet")
    df_2024_parquet = pd.read_parquet(parquet_path_2024)
    
    # Convert numeric columns back
    for col in ['Mcode', 'Number of Sessions']:
        if col in df_2024_parquet.columns:
            df_2024_parquet[col] = pd.to_numeric(df_2024_parquet[col], errors='coerce')
    
    compare_dataframes(df_2024_excel, df_2024_parquet, "2024 Baseline Data")
    
    print("\n" + "="*60)
    print("Verification Complete")
    print("="*60)


if __name__ == "__main__":
    main()

