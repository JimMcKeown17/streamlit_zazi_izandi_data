"""
Comprehensive tool for getting complete grade performance analysis for 2024 data.
This tool combines functionality from percentage_at_benchmark, improvement_scores, and total_scores
to provide a complete picture in a single call.
"""
from agents import function_tool
from .data_loader_2024 import baseline_2024, midline_2024, endline_2024
from .utils import clean_nan_values


def _get_grade_performance_2024(
    grade: str = "Grade 1",
    school: str = "All Schools",
    assessment: str = "Endline",
    include_letters: bool = True
):
    """
    Get comprehensive performance analysis for a specific grade in 2024.
    Returns EGRA scores, improvements, benchmark percentages, and optionally letters data - all in one call.
    
    This is the recommended tool for analyzing grade performance as it provides complete information
    without requiring multiple tool calls.
    
    Args:
        grade: Grade level to analyze - 'Grade R', 'Grade 1', or 'All Grades'
        school: Name of the school to analyze. Use 'All Schools' for programme-wide analysis.
        assessment: Assessment period - 'Baseline', 'Midline', or 'Endline'
        include_letters: Whether to include Letters Known statistics (default: True)
    
    Returns:
        Dictionary containing:
        - EGRA statistics (average, median, min, max) for baseline and target assessment
        - EGRA improvement (average gain from baseline)
        - Percentage at benchmark (baseline vs target)
        - Letters statistics (if include_letters=True)
        - Letters improvement (if include_letters=True)
        - Total students analyzed
    """
    
    # Select appropriate dataset based on assessment
    if assessment == "Baseline":
        data = baseline_2024
        egra_col = 'EGRA Baseline'
        letters_col = 'Baseline Letters Known'
    elif assessment == "Midline":
        data = midline_2024
        egra_col = 'EGRA Midline'
        letters_col = 'Midline Letters Known'
    else:  # Endline
        data = endline_2024
        egra_col = 'EGRA Endline'
        letters_col = 'Letters Known'
    
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
    else:  # All Grades - will calculate per grade
        benchmark = None
    
    total_students = len(filtered_data)
    
    # Build comprehensive result
    result = {
        'grade': grade,
        'school': school,
        'assessment': assessment,
        'total_students': total_students,
        'egra_analysis': {},
        'benchmark_analysis': {}
    }
    
    # EGRA Statistics
    egra_baseline_avg = round(filtered_data['EGRA Baseline'].mean(), 1)
    egra_current_avg = round(filtered_data[egra_col].mean(), 1)
    egra_baseline_median = round(filtered_data['EGRA Baseline'].median(), 1)
    egra_current_median = round(filtered_data[egra_col].median(), 1)
    
    result['egra_analysis'] = {
        'baseline': {
            'average': egra_baseline_avg,
            'median': egra_baseline_median,
            'min': round(filtered_data['EGRA Baseline'].min(), 1),
            'max': round(filtered_data['EGRA Baseline'].max(), 1)
        },
        assessment.lower(): {
            'average': egra_current_avg,
            'median': egra_current_median,
            'min': round(filtered_data[egra_col].min(), 1),
            'max': round(filtered_data[egra_col].max(), 1)
        },
        'improvement_average': round(egra_current_avg - egra_baseline_avg, 1)
    }
    
    # Benchmark Analysis
    if benchmark is not None:
        baseline_above = (filtered_data['EGRA Baseline'] >= benchmark).sum()
        current_above = (filtered_data[egra_col] >= benchmark).sum()
        
        baseline_percent = round((baseline_above / total_students) * 100, 1)
        current_percent = round((current_above / total_students) * 100, 1)
        
        result['benchmark_analysis'] = {
            'benchmark_score': benchmark,
            'baseline_above_benchmark_percent': baseline_percent,
            f'{assessment.lower()}_above_benchmark_percent': current_percent,
            'improvement_percentage_points': round(current_percent - baseline_percent, 1)
        }
    else:
        # All Grades - calculate for each grade
        result['benchmark_analysis'] = {}
        for g in ['Grade R', 'Grade 1']:
            grade_data = filtered_data[filtered_data['Grade'] == g]
            if len(grade_data) > 0:
                bench = 20 if g == "Grade R" else 40
                baseline_above = (grade_data['EGRA Baseline'] >= bench).sum()
                current_above = (grade_data[egra_col] >= bench).sum()
                total = len(grade_data)
                
                result['benchmark_analysis'][g] = {
                    'benchmark_score': bench,
                    'baseline_above_benchmark_percent': round((baseline_above / total) * 100, 1),
                    f'{assessment.lower()}_above_benchmark_percent': round((current_above / total) * 100, 1),
                    'total_students': total
                }
    
    # Letters Analysis (if requested and available)
    if include_letters:
        if letters_col in filtered_data.columns:
            result['letters_analysis'] = {}
            
            # For endline, we use Midline as baseline for letters
            if assessment == "Endline" and 'Midline Letters Known' in filtered_data.columns:
                letters_baseline_col = 'Midline Letters Known'
                letters_baseline_avg = round(filtered_data[letters_baseline_col].mean(), 1)
            elif 'Baseline Letters Known' in filtered_data.columns:
                letters_baseline_col = 'Baseline Letters Known'
                letters_baseline_avg = round(filtered_data[letters_baseline_col].mean(), 1)
            else:
                letters_baseline_col = None
                letters_baseline_avg = None
            
            letters_current_avg = round(filtered_data[letters_col].mean(), 1)
            
            result['letters_analysis'] = {
                assessment.lower(): {
                    'average': letters_current_avg,
                    'median': round(filtered_data[letters_col].median(), 1),
                    'min': round(filtered_data[letters_col].min(), 1),
                    'max': round(filtered_data[letters_col].max(), 1)
                }
            }
            
            if letters_baseline_col and letters_baseline_avg is not None:
                result['letters_analysis']['baseline'] = {
                    'average': letters_baseline_avg
                }
                result['letters_analysis']['improvement_average'] = round(letters_current_avg - letters_baseline_avg, 1)
        else:
            result['letters_analysis'] = {
                'note': f'Letters data not available for {assessment} assessment'
            }
    
    return clean_nan_values(result)


# Export decorated version for agent use
get_grade_performance_2024 = function_tool(_get_grade_performance_2024)

