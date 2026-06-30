import unittest
import pandas as pd
import zz_data_processing as zz

LETTERS = ['a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p', 's', 'h', 'z', 'n', 'd', 'y', 'f', 'w', 'v', 'x', 'g', 't', 'q', 'r', 'c', 'j']


def _letter_row(known_letters):
    row = {c: None for c in LETTERS}
    for c in LETTERS[:known_letters]:
        row[c] = 1
    return row


class ProcessMidlineLetterConsistencyTests(unittest.TestCase):
    def test_midline_letters_known_equals_baseline_plus_learned(self):
        # Midline source column ("Midline Letters Known": 5) deliberately disagrees with the
        # 20 letters actually marked, to expose the single-source-of-truth bug.
        midline = pd.DataFrame([{**_letter_row(20), "Mcode": "M1", "Captured": True, "Grade": "Grade 1",
                                 "Midline Assessment Score": 50, "Midline Letters Known": 5}])
        baseline = pd.DataFrame([{**_letter_row(8), "Mcode": "M1", "Captured": True,
                                  "Baseline\nAssessment Score": 30, "Baseline Letters Known": 8}])
        sessions = pd.DataFrame([{"Mcode": "M1", "Total Sessions": 12}])
        out, _ = zz.process_zz_data_midline(baseline, midline, sessions)
        r = out.iloc[0]
        self.assertEqual(r["Midline Letters Known"], 20)
        self.assertEqual(r["Midline Letters Known"], r["Baseline Letters Known"] + r["Letters Learned"])
