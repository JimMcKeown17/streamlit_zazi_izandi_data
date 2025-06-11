import pandas as pd
import streamlit as st
import os
import json
from dotenv import load_dotenv
import traceback
from datetime import datetime

# Load environment variables
load_dotenv()

def run_comprehensive_diagnostics(df):
    """
    Run comprehensive diagnostics on the AI analysis system.
    Tests each component individually to identify issues.
    """
    
    st.header("🔍 AI Analysis System Diagnostics")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "overall_status": "UNKNOWN"
    }
    
    # Test 1: Environment Setup
    st.subheader("1. Environment Setup")
    env_status = test_environment()
    results["tests"].append({"test": "environment", "status": env_status["status"], "details": env_status})
    
    # Test 2: Data Structure
    st.subheader("2. Data Structure Validation")
    data_status = test_data_structure(df)
    results["tests"].append({"test": "data_structure", "status": data_status["status"], "details": data_status})
    
    # Test 3: OpenAI Connection
    st.subheader("3. OpenAI API Connection")
    api_status = test_openai_connection()
    results["tests"].append({"test": "openai_api", "status": api_status["status"], "details": api_status})
    
    # Test 4: Module Imports
    st.subheader("4. Module Import Tests")
    import_status = test_module_imports()
    results["tests"].append({"test": "module_imports", "status": import_status["status"], "details": import_status})
    
    # Test 5: Tool System
    st.subheader("5. Tool System Test")
    tool_status = test_tool_system(df)
    results["tests"].append({"test": "tool_system", "status": tool_status["status"], "details": tool_status})
    
    # Test 6: Context-Only System
    st.subheader("6. Context-Only System Test")
    context_status = test_context_system(df)
    results["tests"].append({"test": "context_system", "status": context_status["status"], "details": context_status})
    
    # Test 7: Simple OpenAI Call
    st.subheader("7. Simple OpenAI Test")
    simple_status = test_simple_openai_call()
    results["tests"].append({"test": "simple_openai", "status": simple_status["status"], "details": simple_status})
    
    # Overall Assessment
    st.subheader("🎯 Overall Assessment")
    overall_assessment(results)
    
    return results

def test_environment():
    """Test environment variables and basic setup."""
    status = {"status": "PASS", "issues": [], "details": {}}
    
    try:
        # Check API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            status["status"] = "FAIL"
            status["issues"].append("OPENAI_API_KEY not found in environment")
            st.error("❌ OPENAI_API_KEY not found")
        elif len(api_key) < 20:
            status["status"] = "WARN"
            status["issues"].append("API key seems too short")
            st.warning("⚠️ API key seems unusually short")
        else:
            st.success(f"✅ API key found (length: {len(api_key)})")
            status["details"]["api_key_length"] = len(api_key)
        
        # Check .env file existence
        if os.path.exists('.env'):
            st.success("✅ .env file exists")
            status["details"]["env_file_exists"] = True
        else:
            st.warning("⚠️ .env file not found")
            status["details"]["env_file_exists"] = False
            
    except Exception as e:
        status["status"] = "FAIL"
        status["issues"].append(f"Environment test error: {str(e)}")
        st.error(f"❌ Environment test failed: {str(e)}")
    
    return status

def test_data_structure(df):
    """Test DataFrame structure and expected columns."""
    status = {"status": "PASS", "issues": [], "details": {}}
    
    try:
        # Basic DataFrame info
        status["details"]["shape"] = df.shape
        status["details"]["columns"] = list(df.columns)
        
        st.write(f"📊 DataFrame shape: {df.shape}")
        st.write(f"📋 Columns: {len(df.columns)} total")
        
        # Expected columns for analysis
        expected_columns = {
            'letters_correct': 'letters_correct',
            'grade_label': 'grade_label', 
            'school_rep': 'school_rep',
            'name_ta_rep': 'name_ta_rep',
            'name_first_learner': 'name_first_learner'
        }
        
        missing_columns = []
        found_columns = []
        
        for key, col_name in expected_columns.items():
            if col_name in df.columns:
                found_columns.append(col_name)
                st.success(f"✅ {col_name} found")
            else:
                missing_columns.append(col_name)
                st.error(f"❌ {col_name} missing")
        
        status["details"]["found_columns"] = found_columns
        status["details"]["missing_columns"] = missing_columns
        
        if missing_columns:
            status["status"] = "FAIL" if len(missing_columns) > 2 else "WARN"
            status["issues"].append(f"Missing columns: {missing_columns}")
        
        # Data type checks
        if 'letters_correct' in df.columns:
            score_info = {
                "min": float(df['letters_correct'].min()),
                "max": float(df['letters_correct'].max()),
                "mean": float(df['letters_correct'].mean()),
                "null_count": int(df['letters_correct'].isnull().sum())
            }
            status["details"]["score_stats"] = score_info
            st.write(f"📈 Score range: {score_info['min']} - {score_info['max']} (avg: {score_info['mean']:.1f})")
            
    except Exception as e:
        status["status"] = "FAIL"
        status["issues"].append(f"Data structure test error: {str(e)}")
        st.error(f"❌ Data structure test failed: {str(e)}")
        st.code(traceback.format_exc())
    
    return status

def test_openai_connection():
    """Test OpenAI API connection."""
    status = {"status": "PASS", "issues": [], "details": {}}
    
    try:
        import openai
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            status["status"] = "FAIL"
            status["issues"].append("No API key available")
            st.error("❌ No API key for OpenAI test")
            return status
        
        client = openai.OpenAI(api_key=api_key)
        
        # Test with a simple call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'test successful'"}],
            max_tokens=10
        )
        
        if response.choices[0].message.content:
            st.success("✅ OpenAI API connection successful")
            status["details"]["response_received"] = True
            status["details"]["model_used"] = "gpt-4o-mini"
        else:
            status["status"] = "WARN"
            status["issues"].append("API connected but no content received")
            st.warning("⚠️ API connected but response empty")
            
    except Exception as e:
        status["status"] = "FAIL"
        status["issues"].append(f"OpenAI connection error: {str(e)}")
        st.error(f"❌ OpenAI connection failed: {str(e)}")
        st.code(traceback.format_exc())
    
    return status

def test_module_imports():
    """Test importing all required modules."""
    status = {"status": "PASS", "issues": [], "details": {"imported_modules": []}}
    
    modules_to_test = [
        ("openai_analysis", "Context-only analysis module"),
        ("openai_tools_analysis", "Tool-enabled analysis module"),
        ("ai_tools", "Analysis tools module"),
        ("openai", "OpenAI library"),
    ]
    
    for module_name, description in modules_to_test:
        try:
            if module_name == "openai":
                import openai
            elif module_name == "openai_analysis":
                import openai_analysis
            elif module_name == "openai_tools_analysis":
                import openai_tools_analysis
            elif module_name == "ai_tools":
                import ai_tools
            
            st.success(f"✅ {description} imported successfully")
            status["details"]["imported_modules"].append(module_name)
            
        except Exception as e:
            status["status"] = "FAIL"
            status["issues"].append(f"Failed to import {module_name}: {str(e)}")
            st.error(f"❌ Failed to import {description}: {str(e)}")
    
    return status

def test_tool_system(df):
    """Test the tool-enabled analysis system."""
    status = {"status": "PASS", "issues": [], "details": {}}
    
    try:
        from ai_tools import DataAnalysisToolkit
        
        # Test toolkit initialization
        toolkit = DataAnalysisToolkit(df)
        st.success("✅ DataAnalysisToolkit initialized")
        
        # Test basic tool function
        column_info = toolkit.get_column_info()
        if isinstance(column_info, dict) and "total_rows" in column_info:
            st.success(f"✅ get_column_info() works (found {column_info['total_rows']} rows)")
            status["details"]["column_info_works"] = True
        else:
            status["status"] = "WARN"
            status["issues"].append("get_column_info() returned unexpected format")
            st.warning("⚠️ get_column_info() returned unexpected format")
        
        # Test JSON serialization
        try:
            json.dumps(column_info)
            st.success("✅ Tool output is JSON serializable")
            status["details"]["json_serializable"] = True
        except Exception as json_error:
            status["status"] = "FAIL"
            status["issues"].append(f"JSON serialization failed: {str(json_error)}")
            st.error(f"❌ JSON serialization failed: {str(json_error)}")
            
    except Exception as e:
        status["status"] = "FAIL"
        status["issues"].append(f"Tool system test error: {str(e)}")
        st.error(f"❌ Tool system test failed: {str(e)}")
        st.code(traceback.format_exc())
    
    return status

def test_context_system(df):
    """Test the context-only analysis system."""
    status = {"status": "PASS", "issues": [], "details": {}}
    
    try:
        from openai_analysis import prepare_data_summary
        
        # Test data summary preparation
        summary = prepare_data_summary(df, "general")
        if isinstance(summary, dict):
            st.success("✅ prepare_data_summary() works")
            status["details"]["data_summary_works"] = True
            
            # Test JSON serialization
            try:
                json.dumps(summary)
                st.success("✅ Context data is JSON serializable")
                status["details"]["json_serializable"] = True
            except Exception as json_error:
                status["status"] = "FAIL"
                status["issues"].append(f"JSON serialization failed: {str(json_error)}")
                st.error(f"❌ JSON serialization failed: {str(json_error)}")
        else:
            status["status"] = "WARN"
            status["issues"].append("prepare_data_summary() returned unexpected format")
            st.warning("⚠️ prepare_data_summary() returned unexpected format")
            
    except Exception as e:
        status["status"] = "FAIL"
        status["issues"].append(f"Context system test error: {str(e)}")
        st.error(f"❌ Context system test failed: {str(e)}")
        st.code(traceback.format_exc())
    
    return status

def test_simple_openai_call():
    """Test a simple OpenAI call with structured data."""
    status = {"status": "PASS", "issues": [], "details": {}}
    
    try:
        import openai
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            status["status"] = "FAIL"
            status["issues"].append("No API key available")
            return status
        
        client = openai.OpenAI(api_key=api_key)
        
        # Test with a simple structured prompt
        test_data = {"total_students": 100, "avg_score": 25.5}
        prompt = f"Analyze this test data: {json.dumps(test_data)}"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50
        )
        
        if response.choices[0].message.content:
            st.success("✅ Simple OpenAI call with structured data successful")
            status["details"]["structured_call_works"] = True
            # Show first 100 chars of response
            response_preview = response.choices[0].message.content[:100] + "..."
            st.write(f"📝 Response preview: {response_preview}")
        else:
            status["status"] = "WARN"
            status["issues"].append("OpenAI call succeeded but no content")
            st.warning("⚠️ OpenAI call succeeded but no content received")
            
    except Exception as e:
        status["status"] = "FAIL"
        status["issues"].append(f"Simple OpenAI call error: {str(e)}")
        st.error(f"❌ Simple OpenAI call failed: {str(e)}")
        st.code(traceback.format_exc())
    
    return status

def overall_assessment(results):
    """Provide overall assessment and recommendations."""
    
    total_tests = len(results["tests"])
    passed_tests = len([t for t in results["tests"] if t["status"] == "PASS"])
    failed_tests = len([t for t in results["tests"] if t["status"] == "FAIL"])
    warning_tests = len([t for t in results["tests"] if t["status"] == "WARN"])
    
    st.write(f"**Test Results: {passed_tests}/{total_tests} passed, {warning_tests} warnings, {failed_tests} failures**")
    
    if failed_tests == 0:
        st.success("🎉 All tests passed! The system should be working.")
        results["overall_status"] = "HEALTHY"
    elif failed_tests <= 2:
        st.warning(f"⚠️ {failed_tests} test(s) failed. System partially functional.")
        results["overall_status"] = "DEGRADED"
    else:
        st.error(f"❌ {failed_tests} test(s) failed. System needs attention.")
        results["overall_status"] = "BROKEN"
    
    # Specific recommendations
    st.subheader("🔧 Recommendations")
    
    failed_test_names = [t["test"] for t in results["tests"] if t["status"] == "FAIL"]
    
    if "environment" in failed_test_names:
        st.error("🚨 **Priority 1:** Fix environment setup (API key)")
    if "openai_api" in failed_test_names:
        st.error("🚨 **Priority 2:** Fix OpenAI API connection")
    if "data_structure" in failed_test_names:
        st.error("🚨 **Priority 3:** Check data structure and column names")
    if "module_imports" in failed_test_names:
        st.error("🚨 **Priority 4:** Fix module import issues")
    
    # Show detailed error logs
    with st.expander("📋 Detailed Error Log", expanded=False):
        for test in results["tests"]:
            if test["status"] == "FAIL":
                st.write(f"**{test['test']}:** {test['details'].get('issues', [])}")
    
    return results 