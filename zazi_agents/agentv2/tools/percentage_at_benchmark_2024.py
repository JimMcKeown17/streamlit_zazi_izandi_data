"""
Tool for calculating percentage of children meeting grade level benchmarks for 2024 data
"""
from agents import function_tool
from .data_loader_2024 import baseline_2024, midline_2024, endline_2024
from .utils import clean_nan_values


def _percentage_at_benchmark_2024(
    grade: str = "All Grades",
    school: str = "All Schools",
    assessment: str = "Endline",
    top_n: int = None
):
    """
    Calculate the percentage of children meeting grade level benchmarks for 2024 data.
    Grade R benchmark is 20+ on EGRA, Grade 1 benchmark is 40+ on EGRA.
    Can analyze baseline, midline, or endline assessments.
    
    Args:
        grade: Grade level to analyze - 'Grade R', 'Grade 1', or 'All Grades'
        school: Name of the school to analyze. Use 'All Schools' for combined analysis.
        assessment: Assessment period - 'Baseline', 'Midline', or 'Endline'
        top_n: Return top n performing schools (only applicable when school='All Schools')
    
    Returns:
        Dictionary containing benchmark analysis results including percentages above benchmark
    """
    
    # Select appropriate dataset based on assessment
    if assessment == "Midline":
        data = midline_2024
        egra_col = 'EGRA Midline'
    elif assessment == "Endline":
        data = endline_2024
        egra_col = 'EGRA Endline'
    else:  # Baseline
        data = baseline_2024
        egra_col = 'EGRA Baseline'
    
    # Filter by grade
    if grade == "All Grades":
        filtered_data = data
    else:
        filtered_data = data[data['Grade'] == grade]
    
    # Filter by school
    if school != "All Schools":
        filtered_data = filtered_data[filtered_data['School'] == school]
    
    if len(filtered_data) == 0:
        return {'error': f'No data found for Grade: {grade}, School: {school}, Assessment: {assessment}'}
    
    # Set benchmark based on grade
    if grade == "Grade R":
        benchmark = 20
    elif grade == "Grade 1":
        benchmark = 40
    else:  # All Grades - use weighted approach
        results = {}
        for g in ['Grade R', 'Grade 1']:
            grade_data = data[data['Grade'] == g]
            if school != "All Schools":
                grade_data = grade_data[grade_data['School'] == school]
            
            if len(grade_data) > 0:
                bench = 20 if g == "Grade R" else 40
                baseline_above = (grade_data['EGRA Baseline'] >= bench).sum()
                current_above = (grade_data[egra_col] >= bench).sum()
                total = len(grade_data)
                
                results[g] = {
                    'baseline_above_benchmark_percent': round((baseline_above / total) * 100, 1),
                    f'{assessment.lower()}_above_benchmark_percent': round((current_above / total) * 100, 1),
                    'total_students': total,
                    'benchmark': bench
                }
        return clean_nan_values({
            'grade': grade,
            'school': school,
            'assessment': assessment,
            'results_by_grade': results
        })
    
    # Calculate for specific grade
    baseline_above = (filtered_data['EGRA Baseline'] >= benchmark).sum()
    current_above = (filtered_data[egra_col] >= benchmark).sum()
    total = len(filtered_data)
    
    baseline_percent = round((baseline_above / total) * 100, 1) if total > 0 else 0
    current_percent = round((current_above / total) * 100, 1) if total > 0 else 0
    
    result = {
        'grade': grade,
        'school': school,
        'assessment': assessment,
        'benchmark': benchmark,
        'baseline_above_benchmark_percent': baseline_percent,
        f'{assessment.lower()}_above_benchmark_percent': current_percent,
        'improvement': round(current_percent - baseline_percent, 1),
        'total_students': total
    }
    
    # Handle top_n schools if requested and analyzing all schools
    if top_n and school == "All Schools":
        school_results = []
        for sch in filtered_data['School'].unique():
            school_data = filtered_data[filtered_data['School'] == sch]
            school_current_above = (school_data[egra_col] >= benchmark).sum()
            school_total = len(school_data)
            school_percent = round((school_current_above / school_total) * 100, 1) if school_total > 0 else 0
            
            school_results.append({
                'school': sch,
                f'{assessment.lower()}_above_benchmark_percent': school_percent,
                'total_students': school_total
            })
        
        # Sort by performance and take top_n
        school_results.sort(key=lambda x: x[f'{assessment.lower()}_above_benchmark_percent'], reverse=True)
        result['top_schools'] = school_results[:top_n]
    
    return clean_nan_values(result)


# Export decorated version for agent use
percentage_at_benchmark_2024 = function_tool(_percentage_at_benchmark_2024)

