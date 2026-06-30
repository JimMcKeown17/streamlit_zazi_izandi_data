"""Shared EGRA benchmark helpers. EGRA convention is 'at or above' the threshold (>=)."""
import pandas as pd


def count_at_or_above(series, threshold):
    """Count values >= threshold (the EGRA 'at/above benchmark' convention). NaN-safe."""
    numeric = pd.to_numeric(series, errors="coerce")
    return int((numeric >= threshold).sum())
