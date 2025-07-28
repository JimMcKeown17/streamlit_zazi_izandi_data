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
    
    st.header("🔧 AI Analysis System Diagnostics")
    st.write("This diagnostic tool will test all components of the AI analysis system.")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "overall_status": "UNKNOWN"
    }
    
    # Test sequence
    test_functions = [
        ("environment", test_environment),
        ("data_structure", lambda: test_data_structure(df)),
        ("openai_api", test_openai_connection),
        ("module_imports", test_module_imports),
        ("tool_system", lambda: test_tool_system(df)),
        ("simple_openai_call", test_simple_openai_call)
    ]
    
    for test_name, test_func in test_functions:
        st.subheader(f"🧪 Testing: {test_name.replace('_', ' ').title()}")
        
        try:
            test_result = test_func()
            test_result["test"] = test_name
            results["tests"].append(test_result)
            
        except Exception as e:
            error_result = {
                "test": test_name,
                "status": "FAIL",
                "issues": [f"Test crashed: {str(e)}"],
                "details": {"exception": str(e), "traceback": traceback.format_exc()}
            }
            results["tests"].append(error_result)
            st.error(f"❌ Test {test_name} crashed: {str(e)}")
            st.code(traceback.format_exc())
    
    # Overall assessment
    st.divider()
    st.header("📋 Overall Assessment")
    overall_assessment(results)
    
    return results

def test_environment():
    """Test environment setup and dependencies."""
    status = {"status": "PASS", "issues": [], "details": {}}
    
    # Test API key
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        st.success("✅ OPENAI_API_KEY found in environment")
        status["details"]["api_key_present"] = True
        
        # Basic validation
        if len(api_key) > 20 and api_key.startswith(('sk-', 'sk-proj-')):
            st.success("✅ API key format looks valid")
            status["details"]["api_key_format_valid"] = True
        else:
            status["status"] = "WARN"
            status["issues"].append("API key format may be invalid")
            st.warning("⚠️ API key format may be invalid")
    else:
        status["status"] = "FAIL"
        status["issues"].append("OPENAI_API_KEY not found in environment")
        st.error("❌ OPENAI_API_KEY not found in environment variables")
    
    # Test required packages
    required_packages = ['openai', 'pandas', 'streamlit']
    for package in required_packages:
        try:
            __import__(package)
            st.success(f"✅ {package} is available")
            status["details"][f"{package}_available"] = True
        except ImportError:
            status["status"] = "FAIL"
            status["issues"].append(f"Required package {package} not available")
            st.error(f"❌ Required package {package} not available")
    
    return status

def test_data_structure(df):
    """Test that the DataFrame has the expected structure."""
    status = {"status": "PASS", "issues": [], "details": {}}
    
    # Basic DataFrame checks
    if not isinstance(df, pd.DataFrame):
        status["status"] = "FAIL"
        status["issues"].append("Input is not a pandas DataFrame")
        st.error("❌ Input is not a pandas DataFrame")
        return status
    
    if len(df) == 0:
        status["status"] = "FAIL"
        status["issues"].append("DataFrame is empty")
        st.error("❌ DataFrame is empty")
        return status
    
    st.success(f"✅ DataFrame has {len(df)} rows and {len(df.columns)} columns")
    status["details"]["total_rows"] = len(df)
    status["details"]["total_columns"] = len(df.columns)
    
    # Check for key columns expected by analysis tools
    expected_columns = ['letters_correct', 'school_rep', 'grade_label', 'name_ta_rep']
    missing_columns = []
    
    for col in expected_columns:
        if col in df.columns:
            st.success(f"✅ Key column '{col}' found")
            status["details"][f"has_{col}"] = True
        else:
            missing_columns.append(col)
            status["details"][f"has_{col}"] = False
    
    if missing_columns:
        status["status"] = "WARN"
        status["issues"].append(f"Missing expected columns: {missing_columns}")
        st.warning(f"⚠️ Missing expected columns: {missing_columns}")
    
    # Check data types and ranges
    if 'letters_correct' in df.columns:
        if pd.api.types.is_numeric_dtype(df['letters_correct']):
            st.success("✅ 'letters_correct' is numeric")
            status["details"]["letters_correct_numeric"] = True
            
            min_val = df['letters_correct'].min()
            max_val = df['letters_correct'].max()
            st.info(f"📊 Letters correct range: {min_val} to {max_val}")
            status["details"]["letters_correct_range"] = {"min": float(min_val), "max": float(max_val)}
        else:
            status["status"] = "WARN"
            status["issues"].append("'letters_correct' column is not numeric")
            st.warning("⚠️ 'letters_correct' column is not numeric")
    
    return status

def test_openai_connection():
    """Test OpenAI API connection."""
    status = {"status": "PASS", "issues": [], "details": {}}
    
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            status["status"] = "FAIL"
            status["issues"].append("No API key available for testing")
            st.error("❌ No API key available for testing")
            return status
        
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        # Test with a minimal call
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Hello, respond with just 'OK'"}
            ],
            max_tokens=10
        )
        
        if response.choices[0].message.content:
            st.success("✅ OpenAI API connection successful")
            status["details"]["api_response"] = response.choices[0].message.content.strip()
        else:
            status["status"] = "WARN"
            status["issues"].append("API call succeeded but no content returned")
            st.warning("⚠️ API call succeeded but no content returned")
            
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
        ("openai_tools_analysis", "Tool-enabled analysis module"),
        ("ai_tools", "Analysis tools module"),
        ("openai", "OpenAI library"),
    ]
    
    for module_name, description in modules_to_test:
        try:
            if module_name == "openai":
                import openai
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