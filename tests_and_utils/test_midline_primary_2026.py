import unittest
import importlib

import pandas as pd

helpers = importlib.import_module("new_pages.2026.midline_primary_helpers_2026")
build_matched_assessment_pairs = helpers.build_matched_assessment_pairs
build_midline_completion_summary = helpers.build_midline_completion_summary
build_phase_score_summary = helpers.build_phase_score_summary


class MidlinePrimary2026HelperTests(unittest.TestCase):
    def test_build_matched_pairs_uses_latest_response_per_participant_and_phase(self):
        data = pd.DataFrame(
            [
                {
                    "response_id": "old-baseline",
                    "participant_id": "100",
                    "assessment_type": "baseline",
                    "response_date": "2026-02-01",
                    "language": "English",
                    "grade": "Grade 1",
                    "program_name": "Alpha Primary",
                    "class_name": "Grade 1 - Alpha",
                    "letters_total_correct": 10,
                    "nonwords_total_correct": 1,
                    "words_total_correct": 2,
                },
                {
                    "response_id": "new-baseline",
                    "participant_id": "100",
                    "assessment_type": "baseline",
                    "response_date": "2026-02-05",
                    "language": "English",
                    "grade": "Grade 1",
                    "program_name": "Alpha Primary",
                    "class_name": "Grade 1 - Alpha",
                    "letters_total_correct": 12,
                    "nonwords_total_correct": 2,
                    "words_total_correct": 3,
                },
                {
                    "response_id": "midline",
                    "participant_id": "100",
                    "assessment_type": "midline",
                    "response_date": "2026-05-25",
                    "language": "English",
                    "grade": "Grade 1",
                    "program_name": "Alpha Primary",
                    "class_name": "Grade 1 - Alpha",
                    "letters_total_correct": 30,
                    "nonwords_total_correct": 9,
                    "words_total_correct": 11,
                },
                {
                    "response_id": "unmatched-midline",
                    "participant_id": "200",
                    "assessment_type": "midline",
                    "response_date": "2026-05-25",
                    "language": "English",
                    "grade": "Grade 1",
                    "program_name": "Alpha Primary",
                    "class_name": "Grade 1 - Alpha",
                    "letters_total_correct": 22,
                    "nonwords_total_correct": 5,
                    "words_total_correct": 7,
                },
            ]
        )

        matched = build_matched_assessment_pairs(data)

        self.assertEqual(len(matched), 1)
        self.assertEqual(matched.iloc[0]["participant_id"], "100")
        self.assertEqual(matched.iloc[0]["baseline_letters_total_correct"], 12)
        self.assertEqual(matched.iloc[0]["midline_letters_total_correct"], 30)
        self.assertEqual(matched.iloc[0]["letters_change"], 18)
        self.assertEqual(matched.iloc[0]["nonwords_change"], 7)
        self.assertEqual(matched.iloc[0]["words_change"], 8)

    def test_build_phase_score_summary_returns_baseline_midline_and_change(self):
        data = pd.DataFrame(
            [
                {
                    "participant_id": "100",
                    "assessment_type": "baseline",
                    "response_date": "2026-02-01",
                    "grade": "Grade R",
                    "letters_total_correct": 5,
                },
                {
                    "participant_id": "101",
                    "assessment_type": "baseline",
                    "response_date": "2026-02-01",
                    "grade": "Grade R",
                    "letters_total_correct": 7,
                },
                {
                    "participant_id": "100",
                    "assessment_type": "midline",
                    "response_date": "2026-05-01",
                    "grade": "Grade R",
                    "letters_total_correct": 15,
                },
                {
                    "participant_id": "101",
                    "assessment_type": "midline",
                    "response_date": "2026-05-01",
                    "grade": "Grade R",
                    "letters_total_correct": 17,
                },
            ]
        )

        summary = build_phase_score_summary(data, ["grade"], "letters_total_correct")

        self.assertEqual(len(summary), 1)
        self.assertEqual(summary.iloc[0]["grade"], "Grade R")
        self.assertEqual(summary.iloc[0]["Baseline"], 6)
        self.assertEqual(summary.iloc[0]["Midline"], 16)
        self.assertEqual(summary.iloc[0]["Change"], 10)

    def test_build_midline_completion_summary_counts_responses_and_unique_learners(self):
        data = pd.DataFrame(
            [
                {
                    "response_id": "baseline-1",
                    "participant_id": "100",
                    "assessment_type": "baseline",
                    "response_date": "2026-02-01",
                    "language": "English",
                    "program_name": "Alpha Primary",
                    "collected_by": "EA One",
                },
                {
                    "response_id": "midline-1",
                    "participant_id": "100",
                    "assessment_type": "midline",
                    "assessment_complete": "0",
                    "response_date": "2026-05-01",
                    "language": "English",
                    "program_name": "Alpha Primary",
                    "collected_by": "EA One",
                },
                {
                    "response_id": "midline-2",
                    "participant_id": "100",
                    "assessment_type": "midline",
                    "assessment_complete": "1",
                    "response_date": "2026-05-02",
                    "language": "English",
                    "program_name": "Alpha Primary",
                    "collected_by": "EA One",
                },
                {
                    "response_id": "midline-3",
                    "participant_id": "101",
                    "assessment_type": "midline",
                    "assessment_complete": "0",
                    "response_date": "2026-05-03",
                    "language": "isiXhosa",
                    "program_name": "Beta Primary",
                    "collected_by": "EA Two",
                },
            ]
        )

        school_summary = build_midline_completion_summary(data, "program_name")
        ea_summary = build_midline_completion_summary(data, "collected_by")

        alpha = school_summary[school_summary["program_name"] == "Alpha Primary"].iloc[0]
        self.assertEqual(alpha["assessments_completed"], 2)
        self.assertEqual(alpha["unique_learners"], 1)
        self.assertEqual(alpha["eas"], 1)

        ea_one = ea_summary[ea_summary["collected_by"] == "EA One"].iloc[0]
        self.assertEqual(ea_one["assessments_completed"], 2)
        self.assertEqual(ea_one["unique_learners"], 1)
        self.assertEqual(ea_one["schools"], 1)


if __name__ == "__main__":
    unittest.main()
