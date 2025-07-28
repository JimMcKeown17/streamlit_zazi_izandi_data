import pandas as pd
from data_loader import load_zazi_izandi_2025, load_zazi_izandi_2023, load_zazi_izandi_2024
from zz_data_process_23 import process_zz_data_23
from zz_data_processing import process_zz_data_midline, process_zz_data_endline, grade1_df, gradeR_df

# Load 2025 data
df_full, df_ecd = load_zazi_izandi_2025()
df_full['submission_date'] = pd.to_datetime(df_full['date'])
initial_data = df_full[df_full['submission_date'] < pd.Timestamp('2025-04-15')]
midline_data = df_full[df_full['submission_date'] >= pd.Timestamp('2025-04-15')]

# Load 2023 data
endline_df_2023, sessions_df_2023 = load_zazi_izandi_2023()
endline_2023 = process_zz_data_23(endline_df_2023, sessions_df_2023)

# Load 2024 data
baseline_df_2024, midline_df_2024, sessions_df_2024, baseline2_df_2024, endline_df_2024, endline2_df_2024 = load_zazi_izandi_2024()
midline_2024, baseline_2024 = process_zz_data_midline(baseline_df_2024, midline_df_2024, sessions_df_2024)
endline_2024 = process_zz_data_endline(endline_df_2024)

def grade1_benchmark_per_school(school: str = None, benchmark: int = 40):
    """
    Calculate the percentage of Grade 1 children meeting the grade level benchmark.
    
    Args:
        school (str, optional): Name of the school to analyze. If None, calculates for all schools combined.
        benchmark (int): Letter knowledge benchmark (default: 40)
    
    Returns:
        dict: Dictionary containing initial and midline percentages above benchmark
    """
    
    if school is None:
        # Calculate for all Grade 1 students across all schools
        g1_initial = initial_data[initial_data['grade_label'] == 'Grade 1']
        g1_midline = midline_data[midline_data['grade_label'] == 'Grade 1']
        school_name = "All Schools"
    else:
        # Filter data for the specific school
        school_initial = initial_data[initial_data['school'] == school]
        school_midline = midline_data[midline_data['school'] == school]
        
        # Filter for Grade 1 students only
        g1_initial = school_initial[school_initial['grade_label'] == 'Grade 1']
        g1_midline = school_midline[school_midline['grade_label'] == 'Grade 1']
        school_name = school
    
    # Validate data exists
    if len(g1_initial) == 0 and len(g1_midline) == 0:
        return {
            'error': f'No Grade 1 data found for: {school_name}',
            'initial_above_benchmark_percent': 0,
            'midline_above_benchmark_percent': 0,
            'initial_total_students': 0,
            'midline_total_students': 0
        }

    # Calculate initial assessment percentages
    initial_above_benchmark = (g1_initial['letters_correct'] >= benchmark).sum()
    initial_total = len(g1_initial)
    initial_above_benchmark_percent = round((initial_above_benchmark / initial_total) * 100, 1) if initial_total > 0 else 0

    # Calculate midline assessment percentages
    midline_above_benchmark = (g1_midline['letters_correct'] >= benchmark).sum()
    midline_total = len(g1_midline)
    midline_above_benchmark_percent = round((midline_above_benchmark / midline_total) * 100, 1) if midline_total > 0 else 0

    # Return comprehensive data
    result = {
        'school': school_name,
        'benchmark': benchmark,
        'initial_above_benchmark_percent': initial_above_benchmark_percent,
        'midline_above_benchmark_percent': midline_above_benchmark_percent,
        'initial_total_students': initial_total,
        'midline_total_students': midline_total,
        'improvement': round(midline_above_benchmark_percent - initial_above_benchmark_percent, 1)
    }
    
    # If analyzing all schools, add school count for context
    if school is None:
        unique_schools_initial = initial_data[initial_data['grade_label'] == 'Grade 1']['school'].nunique()
        unique_schools_midline = midline_data[midline_data['grade_label'] == 'Grade 1']['school'].nunique()
        result['schools_in_initial'] = unique_schools_initial
        result['schools_in_midline'] = unique_schools_midline
    
    return result

def percentage_at_benchmark_2023(grade: str = "All Grades", school: str = "All Schools", top_n: int = None):
    """
    Calculate the percentage of children meeting the grade level benchmark for 2023 data.
    
    Args:
        grade (str): Grade level ('Grade R', 'Grade 1', or 'All Grades')
        school (str): School name or 'All Schools' for all schools combined
        top_n (int, optional): Return top n performing schools
    
    Returns:
        dict: Dictionary containing baseline and endline percentages above benchmark
    """
    
    # Filter by grade
    if grade == "All Grades":
        filtered_data = endline_2023
    else:
        filtered_data = endline_2023[endline_2023['Grade'] == grade]
    
    # Filter by school
    if school != "All Schools":
        filtered_data = filtered_data[filtered_data['School'] == school]
    
    if len(filtered_data) == 0:
        return {'error': f'No data found for Grade: {grade}, School: {school}'}
    
    # Set benchmark based on grade
    if grade == "Grade R":
        benchmark = 20
        baseline_col = 'Masi Egra Full Baseline'
        endline_col = 'Masi Egra Full Endline'
    elif grade == "Grade 1":
        benchmark = 40
        baseline_col = 'Masi Egra Full Baseline'
        endline_col = 'Masi Egra Full Endline'
    else:  # All Grades - use weighted approach
        results = {}
        for g in ['Grade R', 'Grade 1']:
            grade_data = endline_2023[endline_2023['Grade'] == g]
            if school != "All Schools":
                grade_data = grade_data[grade_data['School'] == school]
            
            if len(grade_data) > 0:
                bench = 20 if g == "Grade R" else 40
                baseline_above = (grade_data['Masi Egra Full Baseline'] >= bench).sum()
                endline_above = (grade_data['Masi Egra Full Endline'] >= bench).sum()
                total = len(grade_data)
                
                results[g] = {
                    'baseline_above_benchmark_percent': round((baseline_above / total) * 100, 1),
                    'endline_above_benchmark_percent': round((endline_above / total) * 100, 1),
                    'total_students': total,
                    'benchmark': bench
                }
        return {
            'grade': grade,
            'school': school,
            'results_by_grade': results
        }
    
    # Calculate for specific grade
    baseline_above = (filtered_data[baseline_col] >= benchmark).sum()
    endline_above = (filtered_data[endline_col] >= benchmark).sum()
    total = len(filtered_data)
    
    baseline_percent = round((baseline_above / total) * 100, 1) if total > 0 else 0
    endline_percent = round((endline_above / total) * 100, 1) if total > 0 else 0
    
    result = {
        'grade': grade,
        'school': school,
        'benchmark': benchmark,
        'baseline_above_benchmark_percent': baseline_percent,
        'endline_above_benchmark_percent': endline_percent,
        'improvement': round(endline_percent - baseline_percent, 1),
        'total_students': total
    }
    
    # Handle top_n schools if requested and analyzing all schools
    if top_n and school == "All Schools":
        school_results = []
        for sch in filtered_data['School'].unique():
            school_data = filtered_data[filtered_data['School'] == sch]
            school_endline_above = (school_data[endline_col] >= benchmark).sum()
            school_total = len(school_data)
            school_percent = round((school_endline_above / school_total) * 100, 1) if school_total > 0 else 0
            
            school_results.append({
                'school': sch,
                'endline_above_benchmark_percent': school_percent,
                'total_students': school_total
            })
        
        # Sort by performance and take top_n
        school_results.sort(key=lambda x: x['endline_above_benchmark_percent'], reverse=True)
        result['top_schools'] = school_results[:top_n]
    
    return result

def improvement_scores_2023(metric: str = "EGRA", grade: str = "All Grades", school: str = "All Schools", top_n: int = None):
    """
    Calculate improvement scores for EGRA or Letters Known for 2023 data.
    
    Args:
        metric (str): 'EGRA' or 'Letters' to specify which assessment
        grade (str): Grade level ('Grade R', 'Grade 1', or 'All Grades')
        school (str): School name or 'All Schools' for all schools combined
        top_n (int, optional): Return top n performing schools
    
    Returns:
        dict: Dictionary containing improvement data
    """
    
    # Filter by grade
    if grade == "All Grades":
        filtered_data = endline_2023
    else:
        filtered_data = endline_2023[endline_2023['Grade'] == grade]
    
    # Filter by school
    if school != "All Schools":
        filtered_data = filtered_data[filtered_data['School'] == school]
    
    if len(filtered_data) == 0:
        return {'error': f'No data found for Grade: {grade}, School: {school}'}
    
    # Set columns based on metric
    if metric == "EGRA":
        baseline_col = 'Masi Egra Full Baseline'
        endline_col = 'Masi Egra Full Endline'
        improvement_col = 'Egra Improvement Endline'
    elif metric == "Letters":
        baseline_col = 'Masi Letters Known Baseline'
        endline_col = 'Masi Letters Known Endline'
        improvement_col = 'Letters Learned Endline'
    else:
        return {'error': 'Metric must be either "EGRA" or "Letters"'}
    
    # Calculate averages
    baseline_avg = round(filtered_data[baseline_col].mean(), 1)
    endline_avg = round(filtered_data[endline_col].mean(), 1)
    improvement_avg = round(filtered_data[improvement_col].mean(), 1)
    total_students = len(filtered_data)
    
    result = {
        'metric': metric,
        'grade': grade,
        'school': school,
        'baseline_average': baseline_avg,
        'endline_average': endline_avg,
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
    
    return result

def total_scores_2023(metric: str = "EGRA", assessment: str = "Endline", grade: str = "All Grades", school: str = "All Schools", top_n: int = None):
    """
    Get total scores for EGRA or Letters Known assessments for 2023 data.
    
    Args:
        metric (str): 'EGRA' or 'Letters' to specify which assessment
        assessment (str): 'Baseline' or 'Endline' to specify which assessment point
        grade (str): Grade level ('Grade R', 'Grade 1', or 'All Grades')
        school (str): School name or 'All Schools' for all schools combined
        top_n (int, optional): Return top n performing schools
    
    Returns:
        dict: Dictionary containing score data
    """
    
    # Filter by grade
    if grade == "All Grades":
        filtered_data = endline_2023
    else:
        filtered_data = endline_2023[endline_2023['Grade'] == grade]
    
    # Filter by school
    if school != "All Schools":
        filtered_data = filtered_data[filtered_data['School'] == school]
    
    if len(filtered_data) == 0:
        return {'error': f'No data found for Grade: {grade}, School: {school}'}
    
    # Set column based on metric and assessment
    if metric == "EGRA":
        if assessment == "Baseline":
            score_col = 'Masi Egra Full Baseline'
        else:
            score_col = 'Masi Egra Full Endline'
    elif metric == "Letters":
        if assessment == "Baseline":
            score_col = 'Masi Letters Known Baseline'
        else:
            score_col = 'Masi Letters Known Endline'
    else:
        return {'error': 'Metric must be either "EGRA" or "Letters"'}
    
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
    
    return result

def percentage_at_benchmark_2024(grade: str = "All Grades", school: str = "All Schools", assessment: str = "Endline", top_n: int = None):
    """
    Calculate the percentage of children meeting the grade level benchmark for 2024 data.
    
    Args:
        grade (str): Grade level ('Grade R', 'Grade 1', or 'All Grades')
        school (str): School name or 'All Schools' for all schools combined
        assessment (str): Assessment period ('Baseline', 'Midline', or 'Endline')
        top_n (int, optional): Return top n performing schools
    
    Returns:
        dict: Dictionary containing baseline and current assessment percentages above benchmark
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
        return {
            'grade': grade,
            'school': school,
            'assessment': assessment,
            'results_by_grade': results
        }
    
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
    
    return result

def improvement_scores_2024(metric: str = "EGRA", grade: str = "All Grades", school: str = "All Schools", assessment: str = "Endline", top_n: int = None):
    """
    Calculate improvement scores for EGRA or Letters Known for 2024 data.
    
    Args:
        metric (str): 'EGRA' or 'Letters' to specify which assessment
        grade (str): Grade level ('Grade R', 'Grade 1', or 'All Grades')
        school (str): School name or 'All Schools' for all schools combined
        assessment (str): Target assessment ('Midline' or 'Endline')
        top_n (int, optional): Return top n performing schools
    
    Returns:
        dict: Dictionary containing improvement data
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
            baseline_col = 'Baseline Letters Known'
            current_col = 'Letters Known'  # endline uses 'Letters Known'
            # Calculate Letters Learned for endline
            data = data.copy()
            data['Letters Learned Endline'] = data[current_col] - data[baseline_col]
            improvement_col = 'Letters Learned Endline'
    
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
    
    return result

def total_scores_2024(metric: str = "EGRA", assessment: str = "Endline", grade: str = "All Grades", school: str = "All Schools", top_n: int = None):
    """
    Get total scores for EGRA or Letters Known assessments for 2024 data.
    
    Args:
        metric (str): 'EGRA' or 'Letters' to specify which assessment
        assessment (str): 'Baseline', 'Midline', or 'Endline' to specify which assessment point
        grade (str): Grade level ('Grade R', 'Grade 1', or 'All Grades')
        school (str): School name or 'All Schools' for all schools combined
        top_n (int, optional): Return top n performing schools
    
    Returns:
        dict: Dictionary containing score data
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
    
    return result

def percentage_at_benchmark_2025(grade: str = "All Grades", school: str = "All Schools", assessment: str = "Midline", top_n: int = None):
    """
    Calculate the percentage of children meeting the grade level benchmark for 2025 data.
    
    Args:
        grade (str): Grade level ('Grade R', 'Grade 1', or 'All Grades')
        school (str): School name or 'All Schools' for all schools combined
        assessment (str): Assessment period ('Initial' or 'Midline')
        top_n (int, optional): Return top n performing schools
    
    Returns:
        dict: Dictionary containing initial and current assessment percentages above benchmark
    """
    
    # Select appropriate dataset based on assessment
    if assessment == "Initial":
        data = initial_data
        current_col = 'letters_correct'
    else:  # Midline
        data = midline_data
        current_col = 'letters_correct'
    
    # Filter by grade
    if grade == "All Grades":
        filtered_data = data
    else:
        filtered_data = data[data['grade_label'] == grade]
    
    # Filter by school
    if school != "All Schools":
        filtered_data = filtered_data[filtered_data['school'] == school]
    
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
            grade_data_initial = initial_data[initial_data['grade_label'] == g]
            grade_data_current = data[data['grade_label'] == g]
            
            if school != "All Schools":
                grade_data_initial = grade_data_initial[grade_data_initial['school'] == school]
                grade_data_current = grade_data_current[grade_data_current['school'] == school]
            
            if len(grade_data_current) > 0:
                bench = 20 if g == "Grade R" else 40
                initial_above = (grade_data_initial['letters_correct'] >= bench).sum() if len(grade_data_initial) > 0 else 0
                current_above = (grade_data_current['letters_correct'] >= bench).sum()
                initial_total = len(grade_data_initial)
                current_total = len(grade_data_current)
                
                results[g] = {
                    'initial_above_benchmark_percent': round((initial_above / initial_total) * 100, 1) if initial_total > 0 else 0,
                    f'{assessment.lower()}_above_benchmark_percent': round((current_above / current_total) * 100, 1),
                    'total_students': current_total,
                    'benchmark': bench
                }
        return {
            'grade': grade,
            'school': school,
            'assessment': assessment,
            'results_by_grade': results
        }
    
    # Calculate for specific grade
    # Get initial data for comparison
    initial_grade_data = initial_data[initial_data['grade_label'] == grade]
    if school != "All Schools":
        initial_grade_data = initial_grade_data[initial_grade_data['school'] == school]
    
    initial_above = (initial_grade_data['letters_correct'] >= benchmark).sum() if len(initial_grade_data) > 0 else 0
    initial_total = len(initial_grade_data)
    initial_percent = round((initial_above / initial_total) * 100, 1) if initial_total > 0 else 0
    
    # Current assessment data
    current_above = (filtered_data[current_col] >= benchmark).sum()
    current_total = len(filtered_data)
    current_percent = round((current_above / current_total) * 100, 1) if current_total > 0 else 0
    
    result = {
        'grade': grade,
        'school': school,
        'assessment': assessment,
        'benchmark': benchmark,
        'initial_above_benchmark_percent': initial_percent,
        f'{assessment.lower()}_above_benchmark_percent': current_percent,
        'improvement': round(current_percent - initial_percent, 1),
        'total_students': current_total
    }
    
    # Handle top_n schools if requested and analyzing all schools
    if top_n and school == "All Schools":
        school_results = []
        for sch in filtered_data['school'].unique():
            school_data = filtered_data[filtered_data['school'] == sch]
            school_current_above = (school_data[current_col] >= benchmark).sum()
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
    
    return result

def improvement_scores_2025(grade: str = "All Grades", school: str = "All Schools", top_n: int = None):
    """
    Calculate improvement scores from initial to midline for 2025 data.
    
    Args:
        grade (str): Grade level ('Grade R', 'Grade 1', or 'All Grades')
        school (str): School name or 'All Schools' for all schools combined
        top_n (int, optional): Return top n performing schools
    
    Returns:
        dict: Dictionary containing improvement data
    """
    
    # Filter initial data by grade
    if grade == "All Grades":
        filtered_initial = initial_data
        filtered_midline = midline_data
    else:
        filtered_initial = initial_data[initial_data['grade_label'] == grade]
        filtered_midline = midline_data[midline_data['grade_label'] == grade]
    
    # Filter by school
    if school != "All Schools":
        filtered_initial = filtered_initial[filtered_initial['school'] == school]
        filtered_midline = filtered_midline[filtered_midline['school'] == school]
    
    if len(filtered_initial) == 0 or len(filtered_midline) == 0:
        return {'error': f'No data found for Grade: {grade}, School: {school}'}
    
    # Calculate averages
    initial_avg = round(filtered_initial['letters_correct'].mean(), 1)
    midline_avg = round(filtered_midline['letters_correct'].mean(), 1)
    improvement_avg = round(midline_avg - initial_avg, 1)
    
    result = {
        'grade': grade,
        'school': school,
        'initial_average': initial_avg,
        'midline_average': midline_avg,
        'improvement_average': improvement_avg,
        'initial_total_students': len(filtered_initial),
        'midline_total_students': len(filtered_midline)
    }
    
    # Handle top_n schools if requested and analyzing all schools
    if top_n and school == "All Schools":
        school_results = []
        
        # Get unique schools from midline data
        for sch in filtered_midline['school'].unique():
            school_initial = filtered_initial[filtered_initial['school'] == sch]
            school_midline = filtered_midline[filtered_midline['school'] == sch]
            
            if len(school_initial) > 0 and len(school_midline) > 0:
                school_initial_avg = school_initial['letters_correct'].mean()
                school_midline_avg = school_midline['letters_correct'].mean()
                school_improvement = round(school_midline_avg - school_initial_avg, 1)
                
                school_results.append({
                    'school': sch,
                    'improvement_average': school_improvement,
                    'midline_students': len(school_midline),
                    'initial_students': len(school_initial)
                })
        
        # Sort by improvement and take top_n
        school_results.sort(key=lambda x: x['improvement_average'], reverse=True)
        result['top_schools'] = school_results[:top_n]
    
    return result

def total_scores_2025(assessment: str = "Midline", grade: str = "All Grades", school: str = "All Schools", top_n: int = None):
    """
    Get total scores for letter assessments for 2025 data.
    
    Args:
        assessment (str): 'Initial' or 'Midline' to specify which assessment point
        grade (str): Grade level ('Grade R', 'Grade 1', or 'All Grades')
        school (str): School name or 'All Schools' for all schools combined
        top_n (int, optional): Return top n performing schools
    
    Returns:
        dict: Dictionary containing score data
    """
    
    # Select appropriate dataset based on assessment
    if assessment == "Initial":
        data = initial_data
    else:  # Midline
        data = midline_data
    
    score_col = 'letters_correct'
    
    # Filter by grade
    if grade == "All Grades":
        filtered_data = data
    else:
        filtered_data = data[data['grade_label'] == grade]
    
    # Filter by school
    if school != "All Schools":
        filtered_data = filtered_data[filtered_data['school'] == school]
    
    if len(filtered_data) == 0:
        return {'error': f'No data found for Grade: {grade}, School: {school}, Assessment: {assessment}'}
    
    # Calculate statistics
    average_score = round(filtered_data[score_col].mean(), 1)
    median_score = round(filtered_data[score_col].median(), 1)
    max_score = round(filtered_data[score_col].max(), 1)
    min_score = round(filtered_data[score_col].min(), 1)
    total_students = len(filtered_data)
    
    result = {
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
        for sch in filtered_data['school'].unique():
            school_data = filtered_data[filtered_data['school'] == sch]
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
    
    return result

def program_summary_stats():
    """
    Calculate comprehensive participation statistics for the Zazi iZandi program across all years (2023-2025).
    
    Returns:
        dict: Dictionary containing comprehensive program participation statistics
    """
    
    # Prepare data from each year with standardized column names
    participation_data = []
    
    # 2025 data (use midline for most current)
    if len(midline_data) > 0:
        data_2025 = midline_data.copy()
        data_2025['year'] = '2025'
        data_2025['grade'] = data_2025['grade_label']
        data_2025['school_name'] = data_2025['school']
        data_2025['ta_name'] = data_2025['name_ta_rep']
        participation_data.append(data_2025[['year', 'grade', 'school_name', 'ta_name']])
    
    # 2024 data (use endline for most comprehensive)
    if len(endline_2024) > 0:
        data_2024 = endline_2024.copy()
        data_2024['year'] = '2024'
        data_2024['grade'] = data_2024['Grade']
        data_2024['school_name'] = data_2024['School']
        data_2024['ta_name'] = data_2024['EA Name']
        participation_data.append(data_2024[['year', 'grade', 'school_name', 'ta_name']])
    
    # 2023 data (use endline)
    if len(endline_2023) > 0:
        data_2023 = endline_2023.copy()
        data_2023['year'] = '2023'
        data_2023['grade'] = data_2023['Grade']
        data_2023['school_name'] = data_2023['School']
        data_2023['ta_name'] = data_2023['EA Name']
        participation_data.append(data_2023[['year', 'grade', 'school_name', 'ta_name']])
    
    if len(participation_data) == 0:
        return {'error': 'No participation data found across any years'}
    
    # Combine all years
    all_data = pd.concat(participation_data, ignore_index=True)
    
    # Calculate overall participation statistics
    total_children = len(all_data)
    grade_r_children = len(all_data[all_data['grade'] == 'Grade R'])
    grade_1_children = len(all_data[all_data['grade'] == 'Grade 1'])
    
    # Unique counts across all years
    unique_schools_all_years = all_data['school_name'].nunique()
    unique_tas_all_years = all_data['ta_name'].nunique()
    
    # Calculate by year
    year_stats = {}
    for year in ['2023', '2024', '2025']:
        year_data = all_data[all_data['year'] == year]
        if len(year_data) > 0:
            year_stats[year] = {
                'total_children': len(year_data),
                'grade_r_children': len(year_data[year_data['grade'] == 'Grade R']),
                'grade_1_children': len(year_data[year_data['grade'] == 'Grade 1']),
                'unique_schools': year_data['school_name'].nunique(),
                'unique_tas': year_data['ta_name'].nunique()
            }
    
    # School and TA participation across years
    schools_with_grade_r = all_data[all_data['grade'] == 'Grade R']['school_name'].nunique()
    schools_with_grade_1 = all_data[all_data['grade'] == 'Grade 1']['school_name'].nunique()
    
    # Calculate averages
    children_per_school = round(total_children / unique_schools_all_years, 1) if unique_schools_all_years > 0 else 0
    children_per_ta = round(total_children / unique_tas_all_years, 1) if unique_tas_all_years > 0 else 0
    
    # Schools that participated in multiple years
    school_year_combinations = all_data.groupby('school_name')['year'].nunique()
    schools_multiple_years = (school_year_combinations > 1).sum()
    
    # TAs that worked in multiple years
    ta_year_combinations = all_data.groupby('ta_name')['year'].nunique()
    tas_multiple_years = (ta_year_combinations > 1).sum()
    
    result = {
        'program_totals': {
            'total_children_across_all_years': total_children,
            'grade_r_children_total': grade_r_children,
            'grade_1_children_total': grade_1_children,
            'unique_schools_across_all_years': unique_schools_all_years,
            'unique_tas_across_all_years': unique_tas_all_years,
            'children_per_school_average': children_per_school,
            'children_per_ta_average': children_per_ta
        },
        'participation_by_grade': {
            'schools_with_grade_r': schools_with_grade_r,
            'schools_with_grade_1': schools_with_grade_1,
            'schools_with_both_grades': all_data.groupby('school_name')['grade'].nunique().gt(1).sum()
        },
        'multi_year_participation': {
            'schools_in_multiple_years': schools_multiple_years,
            'tas_in_multiple_years': tas_multiple_years
        },
        'year_breakdown': year_stats,
        'years_covered': list(year_stats.keys())
    }
    
    return result

TOOLS = {
    "grade1_benchmark_per_school": grade1_benchmark_per_school,
    "percentage_at_benchmark_2023": percentage_at_benchmark_2023,
    "improvement_scores_2023": improvement_scores_2023,
    "total_scores_2023": total_scores_2023,
    "percentage_at_benchmark_2024": percentage_at_benchmark_2024,
    "improvement_scores_2024": improvement_scores_2024,
    "total_scores_2024": total_scores_2024,
    "percentage_at_benchmark_2025": percentage_at_benchmark_2025,
    "improvement_scores_2025": improvement_scores_2025,
    "total_scores_2025": total_scores_2025,
    "program_summary_stats": program_summary_stats,
}