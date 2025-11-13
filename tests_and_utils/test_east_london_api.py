#!/usr/bin/env python3
"""
Test script for East London EGRA API to check record counts
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.east_london_egra_api import fetch_east_london_egra_data

def test_east_london_api():
    """Test the East London EGRA API and report record counts"""
    
    print("=" * 60)
    print("TESTING EAST LONDON EGRA API")
    print("=" * 60)
    
    # Check if API token is available
    api_token = os.getenv('TEAMPACT_API_TOKEN')
    if not api_token:
        print("❌ ERROR: TEAMPACT_API_TOKEN not found in environment variables")
        print("Please set your API token in .env file")
        return False
    
    print(f"✅ API Token found (length: {len(api_token)} chars)")
    print()
    
    # Fetch the data
    try:
        print("🔄 Fetching data from East London EGRA surveys...")
        print("   - Survey 644 (isiXhosa) - EGRA Letter Assessment")
        print("   - Survey 646 (English) - EGRA Letter Assessment")
        print("   - Survey 647 (Afrikaans) - EGRA Letter Assessment")
        print()
        
        xhosa_df, english_df, afrikaans_df = fetch_east_london_egra_data()
        
        if all(df is not None for df in [xhosa_df, english_df, afrikaans_df]):
            print("=" * 60)
            print("📊 RESULTS SUMMARY")
            print("=" * 60)
            
            # Record counts
            print(f"isiXhosa (Survey 644):  {len(xhosa_df):,} records")
            print(f"English (Survey 646):   {len(english_df):,} records")
            print(f"Afrikaans (Survey 647): {len(afrikaans_df):,} records")
            print(f"TOTAL RECORDS:          {len(xhosa_df) + len(english_df) + len(afrikaans_df):,}")
            print()
            
            # Column information
            if not xhosa_df.empty:
                print(f"📋 Column count (isiXhosa): {len(xhosa_df.columns)} columns")
                print("Sample columns:")
                for i, col in enumerate(list(xhosa_df.columns)[:10]):
                    print(f"   {i+1:2d}. {col}")
                if len(xhosa_df.columns) > 10:
                    print(f"   ... and {len(xhosa_df.columns) - 10} more columns")
                print()
            
            # Data preview
            if not xhosa_df.empty:
                print("🔍 SAMPLE DATA (isiXhosa - first record):")
                print("-" * 40)
                sample_record = xhosa_df.iloc[0].to_dict()
                for key, value in list(sample_record.items())[:10]:
                    print(f"   {key}: {value}")
                if len(sample_record) > 10:
                    print(f"   ... and {len(sample_record) - 10} more fields")
                print()
            
            # Check for EGRA survey response structure
            if not xhosa_df.empty:
                print("🎯 EGRA SURVEY STRUCTURE CHECK:")
                print("-" * 30)
                
                # Check if we have the answers array structure
                if 'answers' in xhosa_df.columns:
                    print("   ✅ answers (EGRA data structure present)")
                    
                    # Look at first record's answers to see the EGRA structure
                    sample_answers = xhosa_df.iloc[0]['answers']
                    if isinstance(sample_answers, list) and len(sample_answers) > 0:
                        print(f"   ✅ Found {len(sample_answers)} question answers in first record")
                        
                        # Look for EGRA question (usually the longest/most complex answer)
                        egra_answer = None
                        for answer in sample_answers:
                            if isinstance(answer.get('answer'), dict) and 'cells' in answer.get('answer', {}):
                                egra_answer = answer['answer']
                                break
                        
                        if egra_answer:
                            print("   ✅ EGRA assessment data found!")
                            print(f"      - Total correct: {egra_answer.get('total_correct', 'N/A')}")
                            print(f"      - Total attempted: {egra_answer.get('total_attempted', 'N/A')}")
                            print(f"      - Total cells: {len(egra_answer.get('cells', []))}")
                            print(f"      - Timer elapsed: {egra_answer.get('timer_elapsed', 'N/A')}")
                        else:
                            print("   ❌ No EGRA assessment data found in answers")
                    else:
                        print("   ❌ Empty or invalid answers array")
                else:
                    print("   ❌ No 'answers' column found")
                
                # Check basic response fields
                basic_fields = ['user_name', 'response_id', 'survey_id', 'is_completed']
                print("\n   📋 Basic response fields:")
                for field in basic_fields:
                    if field in xhosa_df.columns:
                        print(f"      ✅ {field}")
                    else:
                        print(f"      ❌ {field}")
                print()
            
            print("✅ TEST COMPLETED SUCCESSFULLY!")
            return True
            
        else:
            print("❌ ERROR: Failed to fetch data from one or more surveys")
            return False
            
    except Exception as e:
        print(f"❌ ERROR during testing: {str(e)}")
        import traceback
        print("\nFull error traceback:")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_east_london_api()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TEST PASSED - API is working correctly!")
    else:
        print("💥 TEST FAILED - Check errors above")
    print("=" * 60)
