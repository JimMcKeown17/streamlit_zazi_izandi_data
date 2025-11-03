"""
Tool for calculating improvement scores for EGRA or Letters Known for 2024 data
"""
from agents import function_tool
from .data_loader_2024 import baseline_2024, midline_2024, endline_2024
from .utils import clean_nan_values


def _improvement_scores_2024(
    metric: str = "EGRA",
    grade: str = "All Grades",
    school: str = "All Schools",
    assessment: str = "Endline",
    top_n: int = None
):
    """
    Calculate improvement scores for EGRA or Letters Known assessments for 2024 data.
    Shows baseline to midline or endline improvement averages.
    
    Args:
        metric: Which assessment metric to analyze - 'EGRA' or 'Letters'
        grade: Grade level to analyze - 'Grade R', 'Grade 1', or 'All Grades'
        school: Name of the school to analyze. Use 'All Schools' for combined analysis.
        assessment: Target assessment period - 'Midline' or 'Endline'
        top_n: Return top n improving schools (only applicable when school='All Schools')
    
    Returns:
        Dictionary containing improvement analysis results
    """
    
    # Select appropriate dataset based on assessment
    if assessment == "Midline":
        data = midline_2024
        if metric == "EGRA":
            baseline_col = 'EGRA Baseline'
            current_col = 'EGRA Midline'
            improvement_col = 'Egra Improvement Agg'
        else:  # Letters
            baseline_col = 'Baseline Letters Known'
            current_col = 'Midline Letters Known'
            improvement_col = 'Letters Learned'
    else:  # Endline
        data = endline_2024
        if metric == "EGRA":
            baseline_col = 'EGRA Baseline'
            current_col = 'EGRA Endline'
            improvement_col = 'Egra Improvement Agg'
        else:  # Letters
            # Endline dataset doesn't have Baseline Letters Known
            # We can use Midline Letters Known as a proxy for baseline if available
            if 'Midline Letters Known' in data.columns:
                baseline_col = 'Midline Letters Known'
                current_col = 'Letters Known'  # endline uses 'Letters Known'
                # Calculate Letters Learned for endline
                data = data.copy()
                data['Letters Learned Endline'] = data[current_col] - data[baseline_col]
                improvement_col = 'Letters Learned Endline'
            else:
                return {'error': 'Letters improvement data not available for Endline assessment. Please use Midline assessment for Letters metric.'}
    
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
    
    # Calculate averages
    baseline_avg = round(filtered_data[baseline_col].mean(), 1)
    current_avg = round(filtered_data[current_col].mean(), 1)
    improvement_avg = round(filtered_data[improvement_col].mean(), 1)
    total_students = len(filtered_data)
    
    result = {
        'metric': metric,
        'grade': grade,
        'school': school,
        'assessment': assessment,
        'baseline_average': baseline_avg,
        f'{assessment.lower()}_average': current_avg,
        'improvement_average': improvement_avg,
        'total_students': total_students
    }
    
    # Handle top_n schools if requested and analyzing all schools
    if top_n and school == "All Schools":
        school_results = []
        for sch in filtered_data['School'].unique():
            school_data = filtered_data[filtered_data['School'] == sch]
            school_improvement = round(school_data[improvement_col].mean(), 1)
            school_total = len(school_data)
            
            school_results.append({
                'school': sch,
                'improvement_average': school_improvement,
                'total_students': school_total
            })
        
        # Sort by improvement and take top_n
        school_results.sort(key=lambda x: x['improvement_average'], reverse=True)
        result['top_schools'] = school_results[:top_n]
    
    return clean_nan_values(result)


# Export decorated version for agent use
improvement_scores_2024 = function_tool(_improvement_scores_2024)

