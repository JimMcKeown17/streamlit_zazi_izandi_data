"""
Utility functions for tools
"""
import pandas as pd
import numpy as np


def clean_nan_values(data):
    """
    Recursively clean NaN values from data structures for JSON serialization.
    Converts NaN to None, inf to None, and ensures all numeric values are JSON compliant.
    """
    if isinstance(data, dict):
        return {k: clean_nan_values(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_nan_values(item) for item in data]
    elif isinstance(data, (np.ndarray, pd.Series)):
        return clean_nan_values(data.tolist())
    elif pd.isna(data) or (isinstance(data, (int, float)) and np.isinf(data)):
        return None
    elif isinstance(data, np.integer):
        return int(data)
    elif isinstance(data, np.floating):
        return float(data) if not (pd.isna(data) or np.isinf(data)) else None
    else:
        return data

