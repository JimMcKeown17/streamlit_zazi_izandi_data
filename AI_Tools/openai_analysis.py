import openai
import os
import json
from dotenv import load_dotenv
import pandas as pd
import streamlit as st

# Load environment variables
load_dotenv()

def setup_openai_client():
    """Initialize OpenAI client with API key from environment variables."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        st.error("OPENAI_API_KEY not found in environment variables. Please add it to your .env file.")
        return None
    
    client = openai.OpenAI(api_key=api_key)
    return client

def prepare_data_summary(df, analysis_type="general"):
    """
    Prepare structured data summary for OpenAI analysis.
    
    Args:
        df: DataFrame to analyze
        analysis_type: Type of analysis ("general", "school_comparison", "grade_improvement")
    
    Returns:
        Dictionary with structured data for the prompt
    """
    
    def convert_numpy_types(obj):
        """Convert numpy types to native Python types for JSON serialization."""
        if hasattr(obj, 'item'):
            return obj.item()
        elif isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(v) for v in obj]
        return obj
    
    if analysis_type == "general":
        # Calculate midline expectations (50-60% of year-end benchmarks)
        grade_r_df = df[df['grade_label'] == 'Grade R']
        grade_1_df = df[df['grade_label'] == 'Grade 1']
        
        summary = {
            "total_students": int(len(df)),
            "unique_schools": int(df['school_rep'].nunique()),
            "unique_tas": int(df['name_ta_rep'].nunique()),
            "grade_distribution": convert_numpy_types(df['grade_label'].value_counts().to_dict()),
            "average_letters_correct": {
                "overall": float(df['letters_correct'].mean()),
                "by_grade": convert_numpy_types(df.groupby('grade_label')['letters_correct'].mean().to_dict())
            },
            "midline_progress_indicators": {
                "grade_r_above_midline_target": {
                    "count": int((grade_r_df['letters_correct'] >= 10).sum()) if len(grade_r_df) > 0 else 0,
                    "percentage": float((grade_r_df['letters_correct'] >= 10).sum() / len(grade_r_df) * 100) if len(grade_r_df) > 0 else 0.0,
                    "target_explanation": "10+ letters (50% of 20-letter year-end benchmark)"
                },
                "grade_1_above_midline_target": {
                    "count": int((grade_1_df['letters_correct'] >= 20).sum()) if len(grade_1_df) > 0 else 0,
                    "percentage": float((grade_1_df['letters_correct'] >= 20).sum() / len(grade_1_df) * 100) if len(grade_1_df) > 0 else 0.0,
                    "target_explanation": "20+ letters (50% of 40-letter year-end benchmark)"
                }
            },
            "year_end_benchmark_performance": {
                "grade_r_above_year_end": {
                    "count": int((grade_r_df['letters_correct'] >= 20).sum()) if len(grade_r_df) > 0 else 0,
                    "percentage": float((grade_r_df['letters_correct'] >= 20).sum() / len(grade_r_df) * 100) if len(grade_r_df) > 0 else 0.0
                },
                "grade_1_above_year_end": {
                    "count": int((grade_1_df['letters_correct'] >= 40).sum()) if len(grade_1_df) > 0 else 0,
                    "percentage": float((grade_1_df['letters_correct'] >= 40).sum() / len(grade_1_df) * 100) if len(grade_1_df) > 0 else 0.0
                }
            }
        }
        
    elif analysis_type == "school_comparison":
        school_summary = df.groupby('school_rep').agg({
            'letters_correct': ['count', 'mean'],
            'name_first_learner': 'count'
        }).round(2)
        
        school_summary.columns = ['students_assessed', 'avg_letters_correct', 'total_students']
        summary = {
            "school_performance": convert_numpy_types(school_summary.to_dict('index')),
            "top_performers": convert_numpy_types(school_summary.nlargest(5, 'avg_letters_correct').to_dict('index')),
            "schools_needing_support": convert_numpy_types(school_summary.nsmallest(3, 'avg_letters_correct').to_dict('index'))
        }
        
    elif analysis_type == "grade_improvement":
        # This would be used when comparing initial vs midline data
        grade_stats = df.groupby('grade_label').agg({
            'letters_correct': ['count', 'mean', 'std'],
            'letters_score_a1': 'mean'
        }).round(2)
        
        grade_r_df = df[df['grade_label'] == 'Grade R']
        grade_1_df = df[df['grade_label'] == 'Grade 1']
        
        summary = {
            "grade_performance": convert_numpy_types(grade_stats.to_dict()),
            "grade_r_above_benchmark": float((grade_r_df['letters_correct'] >= 20).sum() / len(grade_r_df) * 100) if len(grade_r_df) > 0 else 0.0,
            "grade_1_above_benchmark": float((grade_1_df['letters_correct'] >= 40).sum() / len(grade_1_df) * 100) if len(grade_1_df) > 0 else 0.0
        }
    
    return summary

def create_analysis_prompt(data_summary, analysis_type="general", custom_questions=None):
    """
    Create a structured prompt for OpenAI analysis.
    
    Args:
        data_summary: Structured data from prepare_data_summary()
        analysis_type: Type of analysis
        custom_questions: Optional list of specific questions to ask
    
    Returns:
        String prompt for OpenAI
    """
    
    base_context = """
    You are an education data analyst specializing in early grade reading assessments (EGRA). 
    You're analyzing data from a literacy intervention program in South Africa called "Zazi iZandi".
    
    Key context:
    - This is letter knowledge assessment data from June 2025 (midway through the South African school year)
    - Grade R students (age 5-6): Full year benchmark is 20+ letters correct
    - Grade 1 students (age 6-7): Full year benchmark is 40+ letters correct  
    - The program uses Teaching Assistants (TAs) to support learning
    - South African national average for Grade 1 is 27% above benchmark (measured at year-end)
    
    IMPORTANT TIMING CONTEXT:
    - This is MIDLINE data collected in June 2025, approximately halfway through the school year
    - Students started in January 2025, so they've had about 5-6 months of instruction
    - We would expect students to be roughly halfway toward their year-end benchmarks at this point
    - For Grade R: Expected midline progress might be around 10-12 letters correct (50-60% of 20-letter benchmark)
    - For Grade 1: Expected midline progress might be around 20-24 letters correct (50-60% of 40-letter benchmark)
    - Performance should be interpreted relative to this midline expectation, not the full year-end benchmark
    """
    
    if analysis_type == "general":
        prompt = f"""
        {base_context}
        
        Please analyze this assessment data and provide insights:
        
        DATA SUMMARY:
        {json.dumps(data_summary, indent=2)}
        
        Please provide:
        1. Overall program performance assessment (considering this is midline, not year-end data)
        2. Progress evaluation relative to expected midline performance (50-60% of year-end benchmarks)
        3. Key strengths and areas for improvement
        4. Realistic projections for year-end performance based on current midline progress
        5. 3-4 specific, actionable recommendations for the remaining months of the school year
        6. Any patterns or trends you notice in the data
        
        Keep your response clear, data-driven, and focused on educational outcomes. Remember to frame all assessments in the context of midline expectations, not year-end benchmarks.
        """
        
    elif analysis_type == "school_comparison":
        prompt = f"""
        {base_context}
        
        Please analyze this school-level performance data:
        
        SCHOOL PERFORMANCE DATA:
        {json.dumps(data_summary, indent=2)}
        
        Please provide:
        1. Analysis of school performance variation (relative to midline expectations)
        2. Identification of schools on track for strong year-end performance and their potential success factors
        3. Support recommendations for schools that may need additional help to reach year-end benchmarks
        4. Insights about equity and access across schools
        5. Realistic year-end projections for each school based on current midline progress
        6. Suggestions for peer learning opportunities between schools
        """
        
    elif analysis_type == "grade_improvement":
        prompt = f"""
        {base_context}
        
        Please analyze this grade-level performance data:
        
        GRADE PERFORMANCE DATA:
        {json.dumps(data_summary, indent=2)}
        
        Please provide:
        1. Grade-specific performance analysis relative to midline expectations
        2. Comparison between Grade R and Grade 1 outcomes and progress rates
        3. Assessment of age-appropriate progress (considering 5-6 months of instruction)
        4. Recommendations for grade-specific interventions for the remaining school year
        5. Projections for year-end readiness and next grade level preparation
        6. Identification of students/grades that may need intensive support in the final months
        """
    
    if custom_questions:
        prompt += f"\n\nAdditional specific questions to address:\n"
        for i, question in enumerate(custom_questions, 1):
            prompt += f"{i}. {question}\n"
    
    return prompt

def get_openai_analysis(prompt, model="gpt-4o-mini", max_tokens=1500):
    """
    Send prompt to OpenAI and get analysis response.
    
    Args:
        prompt: The analysis prompt
        model: OpenAI model to use
        max_tokens: Maximum response length
    
    Returns:
        Analysis response string or None if error
    """
    
    client = setup_openai_client()
    if not client:
        return None
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert education data analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        st.error(f"Error calling OpenAI API: {str(e)}")
        return None

def analyze_data_with_openai(df, analysis_type="general", custom_questions=None, model="gpt-4o-mini"):
    """
    Complete pipeline to analyze DataFrame with OpenAI.
    
    Args:
        df: DataFrame to analyze
        analysis_type: Type of analysis to perform
        custom_questions: Optional custom questions
        model: OpenAI model to use
    
    Returns:
        Analysis response string or None if error
    """
    
    # Prepare data summary
    data_summary = prepare_data_summary(df, analysis_type)
    
    # Create prompt
    prompt = create_analysis_prompt(data_summary, analysis_type, custom_questions)
    
    # Get analysis
    analysis = get_openai_analysis(prompt, model)
    
    return analysis 