import importlib
import unittest

import pandas as pd

helpers = importlib.import_module("new_pages.2026.ecd_midline_helpers_2026")


def _row(
    response_id,
    assessment_type,
    letters,
    response_date="2026-06-01 09:00:00",
    participant_id="",
    program_name="Green Apple ECD",
    collected_by="EA One",
    grade="PreR",
):
    return {
        "response_id": response_id,
        "participant_id": participant_id,
        "assessment_type": assessment_type,
        "response_date": response_date,
        "grade": grade,
        "program_name": program_name,
        "collected_by": collected_by,
        "letters_total_correct": letters,
    }


class NormalizeTests(unittest.TestCase):
    def test_normalize_drops_null_grades_and_unknown_phases(self):
        data = pd.DataFrame(
            [
                _row("b1", "baseline", 5),
                _row("b2", "baseline", 3, grade="null"),
                _row("x1", "endline", 9),
                _row("m1", "Midline ", 12),
            ]
        )
        normalized = helpers.normalize_ecd_assessments(data)
        self.assertEqual(set(normalized["response_id"]), {"b1", "m1"})
        self.assertEqual(set(normalized["assessment_type"]), {"baseline", "midline"})
        self.assertTrue(pd.api.types.is_datetime64_any_dtype(normalized["response_date"]))
        self.assertTrue(pd.api.types.is_numeric_dtype(normalized["letters_total_correct"]))

    def test_normalize_empty_safe(self):
        self.assertTrue(helpers.normalize_ecd_assessments(pd.DataFrame()).empty)
        self.assertTrue(helpers.normalize_ecd_assessments(None).empty)


class PhaseSummaryTests(unittest.TestCase):
    def test_build_phase_letter_summary_counts_raw_rows_per_phase(self):
        data = pd.DataFrame(
            [
                _row("b1", "baseline", 0, program_name=""),
                _row("b2", "baseline", 4, program_name=""),
                _row("b3", "baseline", 8, program_name=""),
                _row("m1", "midline", 10, participant_id="100"),
                _row("m2", "midline", 20, participant_id="101", program_name="Koester Day Care"),
            ]
        )
        summary = helpers.build_phase_letter_summary(data)
        baseline = summary[summary["Phase"] == "Baseline"].iloc[0]
        midline = summary[summary["Phase"] == "Midline"].iloc[0]
        self.assertEqual(baseline["Assessments"], 3)
        self.assertEqual(baseline["Centers"], 0)  # baseline rows have no program_name
        self.assertEqual(baseline["Mean Letters"], 4.0)
        self.assertEqual(baseline["Median Letters"], 4.0)
        self.assertEqual(midline["Assessments"], 2)
        self.assertEqual(midline["Centers"], 2)
        self.assertEqual(midline["Mean Letters"], 15.0)

    def test_empty_safe(self):
        self.assertTrue(helpers.build_phase_letter_summary(pd.DataFrame()).empty)


class ZeroLetterTests(unittest.TestCase):
    def test_zero_letter_summary_percent_per_phase(self):
        data = pd.DataFrame(
            [
                _row("b1", "baseline", 0),
                _row("b2", "baseline", 0),
                _row("b3", "baseline", 6),
                _row("b4", "baseline", 9),
                _row("m1", "midline", 0),
                _row("m2", "midline", 15),
                _row("m3", "midline", 22),
                _row("m4", "midline", 31),
            ]
        )
        summary = helpers.zero_letter_summary(data)
        baseline = summary[summary["Phase"] == "Baseline"].iloc[0]
        midline = summary[summary["Phase"] == "Midline"].iloc[0]
        self.assertEqual(baseline["Assessments"], 4)
        self.assertEqual(baseline["Zero Letters"], 2)
        self.assertEqual(baseline["Percent"], 50.0)
        self.assertEqual(midline["Zero Letters"], 1)
        self.assertEqual(midline["Percent"], 25.0)


class BenchmarkTests(unittest.TestCase):
    def test_benchmark_summary_threshold(self):
        data = pd.DataFrame(
            [
                _row("b1", "baseline", 0),
                _row("b2", "baseline", 12),
                _row("m1", "midline", 9),
                _row("m2", "midline", 10),
                _row("m3", "midline", 26),
            ]
        )
        summary = helpers.benchmark_summary(data, threshold=10)
        baseline = summary[summary["Phase"] == "Baseline"].iloc[0]
        midline = summary[summary["Phase"] == "Midline"].iloc[0]
        self.assertEqual(baseline["At/Above Benchmark"], 1)
        self.assertEqual(baseline["Percent"], 50.0)
        self.assertEqual(midline["At/Above Benchmark"], 2)
        self.assertEqual(round(midline["Percent"], 1), 66.7)


class MidlineDimensionSummaryTests(unittest.TestCase):
    def test_summary_counts_midline_only_with_unique_learners(self):
        data = pd.DataFrame(
            [
                # Baseline rows must NEVER count, even when they carry participant_ids —
                # mask_dataframe back-fills baseline participant_id from learner names
                # for public users, so phase is the only safe gate.
                _row("b1", "baseline", 2, participant_id="hash-a", program_name="Green Apple ECD"),
                _row("m1", "midline", 10, participant_id="100", collected_by="EA One"),
                _row("m2", "midline", 20, participant_id="100", collected_by="EA One"),
                _row("m3", "midline", 30, participant_id="101", collected_by="EA One"),
                _row("m4", "midline", 0, participant_id="102", collected_by="EA Two",
                     program_name="Koester Day Care"),
            ]
        )
        by_center = helpers.build_midline_dimension_summary(data, "program_name", threshold=10)
        green = by_center[by_center["program_name"] == "Green Apple ECD"].iloc[0]
        self.assertEqual(green["assessments"], 3)
        self.assertEqual(green["unique_learners"], 2)
        self.assertEqual(green["mean_letters"], 20.0)
        self.assertEqual(green["at_or_above"], 3)
        self.assertEqual(green["percent"], 100.0)
        koester = by_center[by_center["program_name"] == "Koester Day Care"].iloc[0]
        self.assertEqual(koester["assessments"], 1)
        self.assertEqual(koester["percent"], 0.0)

        by_ea = helpers.build_midline_dimension_summary(data, "collected_by")
        ea_one = by_ea[by_ea["collected_by"] == "EA One"].iloc[0]
        self.assertEqual(ea_one["assessments"], 3)
        self.assertEqual(ea_one["unique_learners"], 2)
        self.assertNotIn("percent", by_ea.columns)

    def test_blank_dimension_becomes_unknown(self):
        data = pd.DataFrame([_row("m1", "midline", 10, participant_id="100", program_name="")])
        summary = helpers.build_midline_dimension_summary(data, "program_name")
        self.assertEqual(summary.iloc[0]["program_name"], "(unknown)")

    def test_empty_safe(self):
        self.assertTrue(helpers.build_midline_dimension_summary(pd.DataFrame(), "program_name").empty)


class DailyCountTests(unittest.TestCase):
    def test_build_daily_assessment_counts_counts_raw_rows(self):
        data = pd.DataFrame(
            [
                _row("b1", "baseline", 1, response_date="2026-01-22 09:00:00"),
                _row("b2", "baseline", 2, response_date="2026-01-22 11:00:00"),
                _row("m1", "midline", 9, response_date="2026-06-01 10:00:00"),
                _row("m2", "midline", 9, response_date=None),
            ]
        )
        daily = helpers.build_daily_assessment_counts(data)
        self.assertEqual(len(daily), 2)
        self.assertEqual(daily["assessments"].sum(), 3)
        baseline_day = daily[daily["Phase"] == "Baseline"].iloc[0]
        self.assertEqual(baseline_day["date"], pd.Timestamp("2026-01-22"))
        self.assertEqual(baseline_day["assessments"], 2)

    def test_empty_safe(self):
        self.assertTrue(helpers.build_daily_assessment_counts(pd.DataFrame()).empty)


if __name__ == "__main__":
    unittest.main()
