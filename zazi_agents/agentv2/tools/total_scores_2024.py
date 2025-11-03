"""
Tool for getting total score statistics for EGRA or Letters Known assessments for 2024 data
"""
from agents import function_tool
from .data_loader_2024 import baseline_2024, midline_2024, endline_2024
from .utils import clean_nan_values


def _total_scores_2024(
    metric: str = "EGRA",
    assessment: str = "Endline",
    grade: str = "All Grades",
    school: str = "All Schools",
    top_n: int = None
):
    """
    Get total score statistics (average, median, max, min) for EGRA or Letters Known assessments for 2024 data.
    Can analyze baseline, midline, or endline assessments.
    
    Args:
        metric: Which assessment metric to analyze - 'EGRA' or 'Letters'
        assessment: Which assessment point to analyze - 'Baseline', 'Midline', or 'Endline'
        grade: Grade level to analyze - 'Grade R', 'Grade 1', or 'All Grades'
        school: Name of the school to analyze. Use 'All Schools' for combined analysis.
        top_n: Return top n scoring schools (only applicable when school='All Schools')
    
    Returns:
        Dictionary containing score statistics including average, median, max, and min
    """
    
    # Select appropriate dataset and column based on assessment
    if assessment == "Baseline":
        data = baseline_2024
        if metric == "EGRA":
            score_col = 'EGRA Baseline'
        else:  # Letters
            score_col = 'Baseline Letters Known'
    elif assessment == "Midline":
        data = midline_2024
        if metric == "EGRA":
            score_col = 'EGRA Midline'
        else:  # Letters
            score_col = 'Midline Letters Known'
    else:  # Endline
        data = endline_2024
        if metric == "EGRA":
            score_col = 'EGRA Endline'
        else:  # Letters
            score_col = 'Letters Known'  # endline uses 'Letters Known'
    
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
    
    # Calculate statistics
    average_score = round(filtered_data[score_col].mean(), 1)
    median_score = round(filtered_data[score_col].median(), 1)
    max_score = round(filtered_data[score_col].max(), 1)
    min_score = round(filtered_data[score_col].min(), 1)
    total_students = len(filtered_data)
    
    result = {
        'metric': metric,
        'assessment': assessment,
        'grade': grade,
        'school': school,
        'average_score': average_score,
        'median_score': median_score,
        'max_score': max_score,
        'min_score': min_score,
        'total_students': total_students
    }
    
    # Handle top_n schools if requested and analyzing all schools
    if top_n and school == "All Schools":
        school_results = []
        for sch in filtered_data['School'].unique():
            school_data = filtered_data[filtered_data['School'] == sch]
            school_avg = round(school_data[score_col].mean(), 1)
            school_total = len(school_data)
            
            school_results.append({
                'school': sch,
                'average_score': school_avg,
                'total_students': school_total
            })
        
        # Sort by average score and take top_n
        school_results.sort(key=lambda x: x['average_score'], reverse=True)
        result['top_schools'] = school_results[:top_n]
    
    return clean_nan_values(result)


# Export decorated version for agent use
total_scores_2024 = function_tool(_total_scores_2024)

