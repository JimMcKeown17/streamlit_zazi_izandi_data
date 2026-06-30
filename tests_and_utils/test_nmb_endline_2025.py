import unittest
import importlib
import pandas as pd

helpers = importlib.import_module("new_pages.2025.nmb_endline_helpers")
match_baseline_to_endline = helpers.match_baseline_to_endline
merge_baseline_onto_endline_left = helpers.merge_baseline_onto_endline_left
apply_outlier_exclusions = helpers.apply_outlier_exclusions
build_grade_comparison_rows = helpers.build_grade_comparison_rows
build_baseline_endline_chart_rows = helpers.build_baseline_endline_chart_rows
dedupe_latest_per_learner = helpers.dedupe_latest_per_learner


def _baseline(rows):
    return pd.DataFrame(rows)


def _end(pid, date, name, grade, prog, score, eas="EA"):
    return {"participant_id": pid, "Response Date": date, "Participant Name": name, "Grade": grade,
            "Program Name": prog, "Total cells correct - EGRA Letters": score, "Collected By": eas}


class MatchInnerTests(unittest.TestCase):
    def test_duplicate_baseline_key_does_not_fan_out(self):
        baseline = _baseline([
            {"Learner First Name": "Amahle", "Learner Surname": "Nkosi", "Grade": "Grade 1",
             "Program Name": "Alpha", "Total cells correct - EGRA Letters": 10, "Learner EMIS": "E1"},
            {"Learner First Name": "Amahle", "Learner Surname": "Nkosi", "Grade": "Grade 1",
             "Program Name": "Alpha", "Total cells correct - EGRA Letters": 14, "Learner EMIS": "E2"},
        ])
        endline = pd.DataFrame([_end("P1", "2025-10-01", "Amahle Nkosi", "Grade 1", "Alpha", 30)])
        self.assertEqual(len(match_baseline_to_endline(baseline, endline)), 1)

    def test_duplicate_endline_participant_collapses_to_latest(self):
        baseline = _baseline([
            {"Learner First Name": "Bongani", "Learner Surname": "Dube", "Grade": "Grade 2",
             "Program Name": "Beta", "Total cells correct - EGRA Letters": 20, "Learner EMIS": "E3"}])
        endline = pd.DataFrame([
            _end("P9", "2025-10-01", "Bongani Dube", "Grade 2", "Beta", 31),
            _end("P9", "2025-10-20", "Bongani Dube", "Grade 2", "Beta", 35)])  # later
        m = match_baseline_to_endline(baseline, endline)
        self.assertEqual(len(m), 1)
        self.assertEqual(m["Endline Score"].iloc[0], 35)
        self.assertEqual(m["Improvement"].iloc[0], 15)

    def test_idempotent_on_already_merged_endline(self):
        # Mirrors the _exclude branch-1 case: endline already carries Baseline Score/has_baseline_match.
        baseline = _baseline([
            {"Learner First Name": "Cebo", "Learner Surname": "K", "Grade": "Grade 2",
             "Program Name": "Gamma", "Total cells correct - EGRA Letters": 30, "Learner EMIS": "E9"}])
        endline = pd.DataFrame([{**_end("P5", "2025-10-01", "Cebo K", "Grade 2", "Gamma", 15),
                                 "Baseline Score": 99, "Improvement": -1, "has_baseline_match": True}])
        m = match_baseline_to_endline(baseline, endline)
        self.assertEqual(len(m), 1)
        self.assertEqual(m["Baseline Score"].iloc[0], 30)     # fresh, not the stale 99
        self.assertEqual(m["Improvement"].iloc[0], -15)

    def test_empty_safe(self):
        self.assertTrue(match_baseline_to_endline(pd.DataFrame(), pd.DataFrame()).empty)

    def test_match_output_carries_learner_full_name(self):
        baseline = _baseline([
            {"Learner First Name": "Dali", "Learner Surname": "Zungu", "Grade": "Grade 1",
             "Program Name": "Alpha", "Total cells correct - EGRA Letters": 12, "Learner EMIS": "E7"}])
        endline = pd.DataFrame([_end("P7", "2025-10-01", "Dali Zungu", "Grade 1", "Alpha", 22)])
        m = match_baseline_to_endline(baseline, endline)
        self.assertIn("Learner Full Name", m.columns)
        self.assertEqual(m["Learner Full Name"].iloc[0], "Dali Zungu")


class MergeLeftTests(unittest.TestCase):
    def test_left_join_keeps_all_rows_no_fanout(self):
        baseline = _baseline([
            {"Learner First Name": "Amahle", "Learner Surname": "Nkosi", "Grade": "Grade 1",
             "Program Name": "Alpha", "Total cells correct - EGRA Letters": 10, "Learner EMIS": "E1"},
            {"Learner First Name": "Amahle", "Learner Surname": "Nkosi", "Grade": "Grade 1",
             "Program Name": "Alpha", "Total cells correct - EGRA Letters": 14, "Learner EMIS": "E2"}])  # dup key
        endline = pd.DataFrame([
            _end("P1", "2025-10-01", "Amahle Nkosi", "Grade 1", "Alpha", 5, "EA One"),
            _end("P2", "2025-10-01", "Nobody Here", "Grade 2", "Beta", 22, "EA Two")])
        merged = merge_baseline_onto_endline_left(baseline, endline)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[merged["Participant Name"] == "Amahle Nkosi"].iloc[0]["Improvement"], -5)
        self.assertFalse(merged[merged["Participant Name"] == "Nobody Here"].iloc[0]["has_baseline_match"])


class ExcludeDeclineFilterTests(unittest.TestCase):
    def test_matched_decline_is_flagged(self):
        baseline = _baseline([
            {"Learner First Name": "Cebo", "Learner Surname": "Khumalo", "Grade": "Grade 2",
             "Program Name": "Gamma", "Total cells correct - EGRA Letters": 30, "Learner EMIS": "E9"}])
        endline = pd.DataFrame([_end("P5", "2025-10-01", "Cebo Khumalo", "Grade 2", "Gamma", 15, "EA Three")])
        flagged = apply_outlier_exclusions(merge_baseline_onto_endline_left(baseline, endline))
        self.assertTrue(bool(flagged["exclude_score_decline"].iloc[0]))


class GradeComparisonRowsTests(unittest.TestCase):
    def test_skips_grade_absent_from_endline(self):
        rows = build_grade_comparison_rows({"Grade R": 2, "Grade 1": 15, "Grade 2": 37},
                                           {"Grade 1": 25}, ["Grade R", "Grade 1", "Grade 2"])
        self.assertEqual([r["grade"] for r in rows], ["Grade 1"])

    def test_missing_baseline_grade_does_not_crash(self):
        rows = build_grade_comparison_rows({"Grade 1": 15}, {"Grade 1": 25, "Grade 2": 40},
                                           ["Grade 1", "Grade 2"])
        self.assertEqual({r["grade"] for r in rows}, {"Grade 1"})

    def test_negative_improvement_keeps_sign(self):
        rows = build_grade_comparison_rows({"Grade 1": 30}, {"Grade 1": 27}, ["Grade 1"])
        self.assertEqual(rows[0]["improvement"], -3)
        self.assertAlmostEqual(rows[0]["pct_improvement"], -10.0)

    def test_chart_rows_emit_no_fabricated_grades(self):
        rows = build_grade_comparison_rows({"Grade R": 2, "Grade 1": 15, "Grade 2": 37},
                                           {"Grade 1": 25}, ["Grade R", "Grade 1", "Grade 2"])
        chart_rows = build_baseline_endline_chart_rows(rows, "Baseline (August)", "Endline (Oct)")
        self.assertEqual({r["Grade"] for r in chart_rows}, {"Grade 1"})
        self.assertEqual({r["Period"] for r in chart_rows}, {"Baseline (August)", "Endline (Oct)"})


class DedupeLatestPerLearnerTests(unittest.TestCase):
    def test_keeps_latest_response_per_learner(self):
        df = pd.DataFrame([
            {"participant_id": "P1", "Response Date": "2025-10-01", "Grade": "Grade 1", "Total cells correct - EGRA Letters": 10},
            {"participant_id": "P1", "Response Date": "2025-10-20", "Grade": "Grade 1", "Total cells correct - EGRA Letters": 18},
            {"participant_id": "P2", "Response Date": "2025-10-05", "Grade": "Grade 1", "Total cells correct - EGRA Letters": 7},
        ])
        out = dedupe_latest_per_learner(df)
        self.assertEqual(len(out), 2)
        self.assertEqual(out[out["participant_id"] == "P1"]["Total cells correct - EGRA Letters"].iloc[0], 18)

    def test_missing_participant_id_returns_unchanged(self):
        df = pd.DataFrame([{"Grade": "Grade 1", "Total cells correct - EGRA Letters": 5}])
        self.assertEqual(len(dedupe_latest_per_learner(df)), 1)
