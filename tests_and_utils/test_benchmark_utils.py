import unittest
import pandas as pd
from benchmark_utils import count_at_or_above


class CountAtOrAboveTests(unittest.TestCase):
    def test_threshold_value_counts_as_at_or_above(self):
        self.assertEqual(count_at_or_above(pd.Series([39, 40, 41]), 40), 2)

    def test_nan_is_ignored(self):
        self.assertEqual(count_at_or_above(pd.Series([40, None, 50]), 40), 2)

    def test_empty_series(self):
        self.assertEqual(count_at_or_above(pd.Series(dtype="float64"), 40), 0)
