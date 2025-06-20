import pandas as pd
import numpy as np
import json
from typing import Dict, List, Optional, Union, Tuple
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

class DataAnalysisToolkit:
    """
    A comprehensive toolkit for analyzing education assessment data.
    Designed for identifying performance patterns, variance analysis, and benchmark comparisons.
    """
    
    def __init__(self, df: pd.DataFrame):
        """Initialize with assessment DataFrame."""
        self.df = df.copy()
        self.original_size = len(df)
        
        # Define benchmark values
        self.benchmarks = {
            'Grade R': {
                'year_end': 20,
                'midline': 10,
                'description': 'Grade R: 20 letters year-end, 10 letters midline target'
            },
            'Grade 1': {
                'year_end': 40,
                'midline': 20,
                'description': 'Grade 1: 40 letters year-end, 20 letters midline target'
            }
        }
        
        # Common column mappings (adjust based on your actual column names)
        self.column_map = {
            'score': 'letters_correct',
            'grade': 'grade_label', 
            'school': 'school_rep',
            'ta': 'name_ta_rep',
            'student': 'name_first_learner',
            'class': 'class'
        }
    
    def convert_to_json_serializable(self, obj):
        """
        Convert pandas/numpy objects to JSON-serializable Python types.
        Handles timestamps, numpy types, and nested structures.
        """
        # Handle pandas Series and Index objects first
        if isinstance(obj, (pd.Series, pd.Index)):
            return obj.tolist()
        
        # Handle numpy arrays
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        
        # Check for None (but not for pd.isna on arrays)
        if obj is None:
            return None
        
        # For scalar values, check if they're NaN
        if isinstance(obj, (int, float, str, bool)):
            if pd.isna(obj):
                return None
            return obj
        
        # Handle timestamps
        if isinstance(obj, (pd.Timestamp, datetime, date)):
            return obj.isoformat() if hasattr(obj, 'isoformat') else str(obj)
        
        # Handle numpy scalars
        if hasattr(obj, 'item'):
            return obj.item()
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        
        # Handle collections
        elif isinstance(obj, dict):
            return {k: self.convert_to_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self.convert_to_json_serializable(v) for v in obj]
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict('records')
        
        # Default: return as-is
        else:
            return obj
    
    def get_column_info(self) -> Dict:
        """Get information about available columns and data structure."""
        result = {
            "total_rows": len(self.df),
            "columns": list(self.df.columns),
            "grade_values": list(self.df[self.column_map['grade']].unique()) if self.column_map['grade'] in self.df.columns else [],
            "school_count": self.df[self.column_map['school']].nunique() if self.column_map['school'] in self.df.columns else 0,
            "ta_count": self.df[self.column_map['ta']].nunique() if self.column_map['ta'] in self.df.columns else 0,
            "score_range": {
                "min": float(self.df[self.column_map['score']].min()),
                "max": float(self.df[self.column_map['score']].max()),
                "mean": float(self.df[self.column_map['score']].mean())
            } if self.column_map['score'] in self.df.columns else {}
        }
        return self.convert_to_json_serializable(result)
    
    def filter_data(self, grade: Optional[str] = None, school: Optional[str] = None, 
                   ta: Optional[str] = None, min_score: Optional[float] = None, 
                   max_score: Optional[float] = None, class_name: Optional[str] = None) -> Dict:
        """Filter dataset based on specified criteria."""
        filtered_df = self.df.copy()
        filter_description = []
        
        if grade:
            filtered_df = filtered_df[filtered_df[self.column_map['grade']] == grade]
            filter_description.append(f"Grade: {grade}")
            
        if school:
            filtered_df = filtered_df[filtered_df[self.column_map['school']] == school]
            filter_description.append(f"School: {school}")
            
        if ta:
            filtered_df = filtered_df[filtered_df[self.column_map['ta']] == ta]
            filter_description.append(f"TA: {ta}")
            
        if class_name:
            filtered_df = filtered_df[filtered_df[self.column_map['class']] == class_name]
            filter_description.append(f"Class: {class_name}")
            
        if min_score is not None:
            filtered_df = filtered_df[filtered_df[self.column_map['score']] >= min_score]
            filter_description.append(f"Min Score: {min_score}")
            
        if max_score is not None:
            filtered_df = filtered_df[filtered_df[self.column_map['score']] <= max_score]
            filter_description.append(f"Max Score: {max_score}")
        
        result = {
            "filtered_count": len(filtered_df),
            "original_count": self.original_size,
            "filter_applied": "; ".join(filter_description) if filter_description else "No filters",
            "summary_stats": {
                "mean_score": float(filtered_df[self.column_map['score']].mean()) if len(filtered_df) > 0 else 0,
                "median_score": float(filtered_df[self.column_map['score']].median()) if len(filtered_df) > 0 else 0,
                "std_score": float(filtered_df[self.column_map['score']].std()) if len(filtered_df) > 0 else 0
            },
            "data": filtered_df.to_dict('records') if len(filtered_df) <= 100 else "Data too large - use specific queries"
        }
        return self.convert_to_json_serializable(result)
    
    def identify_top_performers(self, group_by: str, metric: str = 'letters_correct', 
                           top_n: int = 5, min_sample_size: int = 5, grade: Optional[str] = None) -> Dict:
        """Identify top performing schools, TAs, or classes."""
        if group_by not in self.column_map:
            return {"error": f"Invalid group_by value: {group_by}"}
            
        group_col = self.column_map[group_by]
        metric_col = self.column_map.get(metric, metric)
        
        # Filter by grade if specified
        df = self.df.copy()
        if grade:
            if self.column_map['grade'] not in df.columns:
                return {"error": f"Grade column '{self.column_map['grade']}' not found in data"}
            df = df[df[self.column_map['grade']] == grade]
            if len(df) == 0:
                return {"error": f"No data found for grade: {grade}"}
        
        # Check if the column exists in the DataFrame
        if group_col not in df.columns:
            return {"error": f"Column '{group_col}' not found in data. Available columns: {list(df.columns)[:10]}..."}
        
        if metric_col not in df.columns:
            # Try alternate column names for letters correct
            alternate_cols = ['letters_correct_a1', 'letters_correct', 'letters_score_a1']
            found_col = None
            for alt_col in alternate_cols:
                if alt_col in df.columns:
                    found_col = alt_col
                    break
            
            if found_col:
                metric_col = found_col
            else:
                return {"error": f"Score column '{metric_col}' not found. Available columns: {list(df.columns)[:10]}..."}
        
        # Calculate performance by group
        performance = df.groupby(group_col).agg({
            metric_col: ['count', 'mean', 'std'],
            self.column_map['student']: 'count'
        }).round(2)
        
        performance.columns = ['assessment_count', 'avg_score', 'score_std', 'student_count']
        
        # Filter for minimum sample size - handle NaN values properly
        performance = performance.dropna()  # Remove any NaN rows first
        performance = performance[performance['student_count'] >= min_sample_size]
        
        # Get top performers
        top_performers = performance.nlargest(top_n, 'avg_score')
        
        # Build result without calling convert_to_json_serializable on the entire dict
        result = {
            "analysis_type": f"Top {top_n} {group_by}s by {metric}" + (f" - {grade}" if grade else ""),
            "grade_filter": grade,
            "min_sample_size": min_sample_size,
            "total_groups_analyzed": len(performance),
            "top_performers": []
        }
        
        # Convert each row individually
        for idx, row in top_performers.iterrows():
            performer = {
                "name": str(idx),
                "avg_score": float(row['avg_score']),
                "student_count": int(row['student_count']),
                "score_std": float(row['score_std']),
                "assessment_count": int(row['assessment_count'])
            }
            result["top_performers"].append(performer)
        
        return result

    def identify_underperformers(self, group_by: str, metric: str = 'letters_correct', 
                                bottom_n: int = 3, min_sample_size: int = 5, grade: Optional[str] = None) -> Dict:
        """Identify underperforming schools, TAs, or classes."""
        if group_by not in self.column_map:
            return {"error": f"Invalid group_by value: {group_by}"}
            
        group_col = self.column_map[group_by]
        metric_col = self.column_map.get(metric, metric)
        
        # Filter by grade if specified
        df = self.df.copy()
        if grade:
            if self.column_map['grade'] not in df.columns:
                return {"error": f"Grade column '{self.column_map['grade']}' not found in data"}
            df = df[df[self.column_map['grade']] == grade]
            if len(df) == 0:
                return {"error": f"No data found for grade: {grade}"}
        
        # Check if the column exists in the DataFrame
        if group_col not in df.columns:
            return {"error": f"Column '{group_col}' not found in data. Available columns: {list(df.columns)[:10]}..."}
        
        if metric_col not in df.columns:
            # Try alternate column names for letters correct
            alternate_cols = ['letters_correct_a1', 'letters_correct', 'letters_score_a1']
            found_col = None
            for alt_col in alternate_cols:
                if alt_col in df.columns:
                    found_col = alt_col
                    break
            
            if found_col:
                metric_col = found_col
            else:
                return {"error": f"Score column '{metric_col}' not found. Available columns: {list(df.columns)[:10]}..."}
        
        # Calculate performance by group
        performance = df.groupby(group_col).agg({
            metric_col: ['count', 'mean', 'std'],
            self.column_map['student']: 'count'
        }).round(2)
        
        performance.columns = ['assessment_count', 'avg_score', 'score_std', 'student_count']
        
        # Filter for minimum sample size - handle NaN values properly
        performance = performance.dropna()  # Remove any NaN rows first
        performance = performance[performance['student_count'] >= min_sample_size]
        
        # Get underperformers
        underperformers = performance.nsmallest(bottom_n, 'avg_score')
        
        # Build result without calling convert_to_json_serializable on the entire dict
        result = {
            "analysis_type": f"Bottom {bottom_n} {group_by}s by {metric}" + (f" - {grade}" if grade else ""),
            "grade_filter": grade,
            "min_sample_size": min_sample_size,
            "total_groups_analyzed": len(performance),
            "underperformers": []
        }
        
        # Convert each row individually
        for idx, row in underperformers.iterrows():
            performer = {
                "name": str(idx),
                "avg_score": float(row['avg_score']),
                "student_count": int(row['student_count']),
                "score_std": float(row['score_std']),
                "assessment_count": int(row['assessment_count'])
            }
            result["underperformers"].append(performer)
        
        return result
    
    def benchmark_analysis(self, group_by: Optional[str] = None, 
                          benchmark_type: str = 'midline') -> Dict:
        """Analyze performance against benchmarks."""
        results = {}
        
        for grade in ['Grade R', 'Grade 1']:
            if grade not in self.df[self.column_map['grade']].values:
                continue
                
            grade_df = self.df[self.df[self.column_map['grade']] == grade]
            benchmark = self.benchmarks[grade][benchmark_type]
            
            if group_by and group_by in self.column_map:
                group_col = self.column_map[group_by]
                group_analysis = []
                
                for group_name in grade_df[group_col].unique():
                    group_data = grade_df[grade_df[group_col] == group_name]
                    above_benchmark = (group_data[self.column_map['score']] >= benchmark).sum()
                    total = len(group_data)
                    
                    group_analysis.append({
                        "name": str(group_name),
                        "total_students": int(total),
                        "above_benchmark": int(above_benchmark),
                        "percentage_above": float(above_benchmark / total * 100) if total > 0 else 0,
                        "avg_score": float(group_data[self.column_map['score']].mean())
                    })
                
                results[grade] = {
                    "benchmark_value": benchmark,
                    "benchmark_type": benchmark_type,
                    "group_analysis": group_analysis
                }
            else:
                above_benchmark = (grade_df[self.column_map['score']] >= benchmark).sum()
                total = len(grade_df)
                
                results[grade] = {
                    "benchmark_value": benchmark,
                    "benchmark_type": benchmark_type,
                    "total_students": int(total),
                    "above_benchmark": int(above_benchmark),
                    "percentage_above": float(above_benchmark / total * 100) if total > 0 else 0,
                    "avg_score": float(grade_df[self.column_map['score']].mean())
                }
        
        result = {
            "analysis_type": f"Benchmark Analysis ({benchmark_type})",
            "benchmarks_used": self.benchmarks,
            "results": results
        }
        return self.convert_to_json_serializable(result)
    
    def variance_analysis(self, group_by: str, metric: str = 'letters_correct', grade: Optional[str] = None) -> Dict:
        """Analyze variance within and between groups."""
        if group_by not in self.column_map:
            return {"error": f"Invalid group_by value: {group_by}"}
            
        group_col = self.column_map[group_by]
        metric_col = self.column_map.get(metric, metric)
        
        # Filter by grade if specified
        df = self.df.copy()
        if grade:
            if self.column_map['grade'] not in df.columns:
                return {"error": f"Grade column '{self.column_map['grade']}' not found in data"}
            df = df[df[self.column_map['grade']] == grade]
            if len(df) == 0:
                return {"error": f"No data found for grade: {grade}"}
        
        # Calculate statistics by group
        group_stats = df.groupby(group_col)[metric_col].agg([
            'count', 'mean', 'std', 'min', 'max', 
            lambda x: x.quantile(0.25),
            lambda x: x.quantile(0.75)
        ]).round(2)
        
        group_stats.columns = ['count', 'mean', 'std', 'min', 'max', 'q25', 'q75']
        
        # Overall statistics
        overall_mean = df[metric_col].mean()
        overall_std = df[metric_col].std()
        
        # Calculate coefficient of variation for each group
        group_stats['cv'] = (group_stats['std'] / group_stats['mean'] * 100).round(2)
        
        result = {
            "analysis_type": f"Variance Analysis: {metric} by {group_by}" + (f" - {grade}" if grade else ""),
            "grade_filter": grade,
            "overall_stats": {
                "mean": float(overall_mean),
                "std": float(overall_std),
                "cv": float(overall_std / overall_mean * 100)
            },
            "group_stats": [
                {
                    "group": str(idx),
                    "count": int(row['count']),
                    "mean": float(row['mean']),
                    "std": float(row['std']),
                    "cv": float(row['cv']),
                    "min": float(row['min']),
                    "max": float(row['max']),
                    "q25": float(row['q25']),
                    "q75": float(row['q75'])
                }
                for idx, row in group_stats.iterrows()
            ],
            "highest_variance_groups": [
                str(idx) for idx in group_stats.nlargest(3, 'cv').index
            ],
            "lowest_variance_groups": [
                str(idx) for idx in group_stats.nsmallest(3, 'cv').index
            ]
        }
        return self.convert_to_json_serializable(result)
    
    def compare_groups(self, group1_filter: Dict, group2_filter: Dict, 
                      metric: str = 'letters_correct') -> Dict:
        """Compare two specific groups of students."""
        metric_col = self.column_map.get(metric, metric)
        
        # Apply filters for each group
        group1_df = self.df.copy()
        group2_df = self.df.copy()
        
        for key, value in group1_filter.items():
            if key in self.column_map:
                group1_df = group1_df[group1_df[self.column_map[key]] == value]
        
        for key, value in group2_filter.items():
            if key in self.column_map:
                group2_df = group2_df[group2_df[self.column_map[key]] == value]
        
        def calculate_stats(df, name):
            if len(df) == 0:
                return {"name": name, "count": 0, "error": "No data found for this group"}
            
            return {
                "name": name,
                "count": len(df),
                "mean": float(df[metric_col].mean()),
                "median": float(df[metric_col].median()),
                "std": float(df[metric_col].std()),
                "min": float(df[metric_col].min()),
                "max": float(df[metric_col].max())
            }
        
        group1_stats = calculate_stats(group1_df, "Group 1")
        group2_stats = calculate_stats(group2_df, "Group 2")
        
        # Calculate difference if both groups have data
        difference = None
        if group1_stats.get("count", 0) > 0 and group2_stats.get("count", 0) > 0:
            difference = {
                "mean_difference": group1_stats["mean"] - group2_stats["mean"],
                "percentage_difference": ((group1_stats["mean"] - group2_stats["mean"]) / group2_stats["mean"] * 100) if group2_stats["mean"] != 0 else 0
            }
        
        result = {
            "analysis_type": f"Group Comparison: {metric}",
            "group1_filter": group1_filter,
            "group2_filter": group2_filter,
            "group1_stats": group1_stats,
            "group2_stats": group2_stats,
            "difference": difference
        }
        return self.convert_to_json_serializable(result)
    
    def get_student_performance_distribution(self, grade: Optional[str] = None) -> Dict:
        """Get distribution of student performance for understanding spread."""
        df = self.df.copy()
        if grade:
            df = df[df[self.column_map['grade']] == grade]
        
        scores = df[self.column_map['score']]
        
        # Create bins for distribution
        bins = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 100]
        distribution = pd.cut(scores, bins=bins, include_lowest=True).value_counts().sort_index()
        
        result = {
            "analysis_type": f"Student Performance Distribution {f'- {grade}' if grade else '- All Grades'}",
            "total_students": len(df),
            "distribution": [
                {
                    "score_range": str(interval),
                    "count": int(count),
                    "percentage": float(count / len(df) * 100)
                }
                for interval, count in distribution.items()
            ],
            "percentiles": {
                "10th": float(scores.quantile(0.1)),
                "25th": float(scores.quantile(0.25)),
                "50th": float(scores.quantile(0.5)),
                "75th": float(scores.quantile(0.75)),
                "90th": float(scores.quantile(0.9))
            }
        }
        return self.convert_to_json_serializable(result)
    
    def identify_at_risk_students(self, grade: Optional[str] = None, 
                                 threshold_percentile: float = 25) -> Dict:
        """Identify students who may need additional support."""
        df = self.df.copy()
        if grade:
            df = df[df[self.column_map['grade']] == grade]
        
        threshold_score = df[self.column_map['score']].quantile(threshold_percentile / 100)
        at_risk = df[df[self.column_map['score']] <= threshold_score]
        
        # Group at-risk students by school and TA
        by_school = at_risk.groupby(self.column_map['school']).size().sort_values(ascending=False)
        by_ta = at_risk.groupby(self.column_map['ta']).size().sort_values(ascending=False)
        
        result = {
            "analysis_type": f"At-Risk Students Analysis {f'- {grade}' if grade else '- All Grades'}",
            "threshold_percentile": threshold_percentile,
            "threshold_score": float(threshold_score),
            "total_at_risk": len(at_risk),
            "percentage_at_risk": float(len(at_risk) / len(df) * 100),
            "by_school": [
                {"school": str(school), "at_risk_count": int(count)}
                for school, count in by_school.head(10).items()
            ],
            "by_ta": [
                {"ta": str(ta), "at_risk_count": int(count)}
                for ta, count in by_ta.head(10).items()
            ]
        }
        return self.convert_to_json_serializable(result)
    
    def prepare_visualization_data(self, chart_type: str, x_column: str, 
                                  y_column: str, group_by: Optional[str] = None,
                                  filter_params: Optional[Dict] = None) -> Dict:
        """Prepare data for creating visualizations."""
        df = self.df.copy()
        
        # Apply filters if provided
        if filter_params:
            for key, value in filter_params.items():
                if key in self.column_map and value is not None:
                    df = df[df[self.column_map[key]] == value]
        
        # Map column names
        x_col = self.column_map.get(x_column, x_column)
        y_col = self.column_map.get(y_column, y_column)
        group_col = self.column_map.get(group_by, group_by) if group_by else None
        
        if chart_type == "bar":
            if group_col:
                grouped_data = df.groupby([x_col, group_col])[y_col].mean().reset_index()
            else:
                grouped_data = df.groupby(x_col)[y_col].mean().reset_index()
            
            result = {
                "chart_type": "bar",
                "data": grouped_data.to_dict('records'),
                "x_column": x_col,
                "y_column": y_col,
                "group_column": group_col
            }
            return self.convert_to_json_serializable(result)
        
        elif chart_type == "scatter":
            scatter_data = df[[x_col, y_col]]
            if group_col:
                scatter_data[group_col] = df[group_col]
            
            result = {
                "chart_type": "scatter", 
                "data": scatter_data.to_dict('records'),
                "x_column": x_col,
                "y_column": y_col,
                "group_column": group_col
            }
            return self.convert_to_json_serializable(result)
        
        return {"error": f"Unsupported chart type: {chart_type}"} 