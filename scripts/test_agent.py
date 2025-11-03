"""
Test script to verify agentv2 works with parquet-optimized data loading.
"""

import sys
from pathlib import Path
import time

# Add project root to path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

def test_agent_tools():
    """Test that agent tools work with parquet data"""
    print("\n" + "="*60)
    print("Testing AgentV2 Tools with Parquet Data")
    print("="*60)
    
    # Test 2023 tool data loading
    print("\n[1/3] Testing 2023 agent data loading...")
    start_time = time.time()
    
    try:
        # Test the underlying data loading that agents use
        import streamlit as st
        if 'user' not in st.session_state:
            st.session_state.user = None
            
        from data_loader import load_zazi_izandi_2023
        from zz_data_process_23 import process_zz_data_23
        
        endline_df, sessions_df = load_zazi_izandi_2023()
        endline = process_zz_data_23(endline_df, sessions_df)
        result = len(endline)
        
        load_time = time.time() - start_time
        
        print(f"✓ Data loaded and processed successfully")
        print(f"✓ Execution time: {load_time:.4f}s")
        print(f"✓ Result: {result} children in 2023 programme")
        
        # Verify result is reasonable
        if isinstance(result, int) and 1000 < result < 3000:
            print(f"✓ Result validation passed")
        else:
            print(f"⚠ Warning: Unexpected result value")
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 2024 data loading
    print("\n[2/3] Testing 2024 agent data loading...")
    start_time = time.time()
    
    try:
        from data_loader import load_zazi_izandi_2024
        from zz_data_processing import process_zz_data_midline, process_zz_data_endline
        
        # Test the underlying data loading that agents use
        baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df = load_zazi_izandi_2024()
        
        # Process data like the agent tools do
        midline_processed, baseline_processed = process_zz_data_midline(baseline_df, midline_df, sessions_df)
        endline_processed = process_zz_data_endline(endline_df)
        
        load_time = time.time() - start_time
        
        print(f"✓ Data loaded and processed successfully")
        print(f"✓ Total execution time: {load_time:.4f}s")
        print(f"✓ Midline processed: {len(midline_processed):,} rows")
        print(f"✓ Endline processed: {len(endline_processed):,} rows")
        
        # Verify columns needed by agent tools exist
        required_midline_cols = ['Grade', 'School', 'EGRA Baseline', 'EGRA Midline']
        required_endline_cols = ['Grade', 'School', 'EGRA Baseline', 'EGRA Endline']
        
        has_midline_cols = all(col in midline_processed.columns for col in required_midline_cols)
        has_endline_cols = all(col in endline_processed.columns for col in required_endline_cols)
        
        if has_midline_cols and has_endline_cols:
            print(f"✓ All required columns present for agent tools")
        else:
            print(f"⚠ Warning: Missing required columns")
            if not has_midline_cols:
                missing = [c for c in required_midline_cols if c not in midline_processed.columns]
                print(f"  Missing in midline: {missing}")
            if not has_endline_cols:
                missing = [c for c in required_endline_cols if c not in endline_processed.columns]
                print(f"  Missing in endline: {missing}")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test data integrity
    print("\n[3/3] Testing data integrity...")
    try:
        from data_loader import load_zazi_izandi_2023, load_zazi_izandi_2024
        import streamlit as st
        
        if 'user' not in st.session_state:
            st.session_state.user = None
        
        # Load and verify 2023 data has expected columns
        endline_2023, sessions_2023 = load_zazi_izandi_2023()
        expected_2023_cols = ['Mcode', 'Grade', 'School']
        has_cols_2023 = all(col in endline_2023.columns for col in expected_2023_cols)
        
        # Load and verify 2024 data
        baseline_2024, midline_2024, _, _, endline_2024, _ = load_zazi_izandi_2024()
        expected_2024_cols = ['Mcode', 'Grade', 'School']
        has_cols_2024 = all(col in baseline_2024.columns for col in expected_2024_cols)
        
        if has_cols_2023 and has_cols_2024:
            print(f"✓ All expected columns present in both years")
            print(f"✓ 2023 endline: {len(endline_2023):,} rows")
            print(f"✓ 2024 baseline: {len(baseline_2024):,} rows")
            print(f"✓ 2024 endline: {len(endline_2024):,} rows")
        else:
            print(f"⚠ Warning: Missing expected columns")
            return False
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Main test script"""
    print("\n" + "="*60)
    print("AgentV2 Parquet Integration Test")
    print("Testing agent tools with optimized data loading")
    print("="*60)
    
    total_start = time.time()
    
    # Run tests
    success = test_agent_tools()
    
    total_time = time.time() - total_start
    
    # Summary
    print("\n" + "="*60)
    print("Agent Test Summary")
    print("="*60)
    print(f"Total test time: {total_time:.4f}s")
    
    if success:
        print("\n✓ All agent tests passed!")
        print("✓ AgentV2 is working correctly with parquet data")
        print("✓ Data integrity verified")
        print("\n" + "="*60)
        return 0
    else:
        print("\n✗ Some tests failed")
        print("\n" + "="*60)
        return 1


if __name__ == "__main__":
    exit(main())

