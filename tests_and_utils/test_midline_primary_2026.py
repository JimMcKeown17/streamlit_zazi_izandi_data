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


class CohortClassificationTests(unittest.TestCase):
    def test_normalize_school_name_strips_collapses_uppercases(self):
        self.assertEqual(
            helpers.normalize_school_name("  Abraham   Levy  Primary School "),
            "ABRAHAM LEVY PRIMARY SCHOOL",
        )

    def test_classify_cohort_maps_known_schools(self):
        self.assertEqual(helpers.classify_cohort("Abraham Levy Primary School"), "treatment")
        self.assertEqual(helpers.classify_cohort("Kwanoxolo Primary School"), "sef")
        self.assertEqual(helpers.classify_cohort("Pendla Primary School"), "control")

    def test_classify_cohort_sapphire_road_is_sef_not_control(self):
        self.assertEqual(helpers.classify_cohort("Sapphire Road Primary School"), "sef")

    def test_classify_cohort_unknown_blank_and_none_are_other(self):
        self.assertEqual(helpers.classify_cohort("Nonexistent Primary School"), "other")
        self.assertEqual(helpers.classify_cohort(""), "other")
        self.assertEqual(helpers.classify_cohort(None), "other")

    def test_classify_cohort_handles_whitespace_variations(self):
        self.assertEqual(helpers.classify_cohort("  abraham   levy primary school "), "treatment")

    def test_add_cohort_column_classifies_each_row(self):
        df = pd.DataFrame(
            {
                "program_name": [
                    "Abraham Levy Primary School",
                    "Kwanoxolo Primary School",
                    "Pendla Primary School",
                    "Some Random School",
                ]
            }
        )
        out = helpers.add_cohort_column(df)
        self.assertEqual(list(out["cohort"]), ["treatment", "sef", "control", "other"])

    def test_cohort_counts_returns_post_precedence_list_sizes(self):
        counts = helpers.cohort_counts()
        self.assertEqual(counts["treatment"], 51)
        self.assertEqual(counts["sef"], 10)
        self.assertEqual(counts["control"], 53)

    def test_cohort_column_survives_masking_while_program_name_is_aliased(self):
        from data_privacy import mask_dataframe

        df = pd.DataFrame(
            {
                "program_name": ["Abraham Levy Primary School", "Kwanoxolo Primary School"],
                "participant_id": ["100", "101"],
            }
        )
        df = helpers.add_cohort_column(df)
        masked = mask_dataframe(df, dataset_key="assessments_2026", authenticated=False)
        self.assertEqual(list(masked["cohort"]), ["treatment", "sef"])
        self.assertTrue(all(str(value).startswith("School ") for value in masked["program_name"]))
        self.assertNotIn("Abraham Levy Primary School", list(masked["program_name"]))


def _row(pid, phase, school, grade, letters, date, gender="", language="English"):
    return {
        "response_id": f"{pid}-{phase}-{school}",
        "participant_id": pid,
        "assessment_type": phase,
        "response_date": date,
        "language": language,
        "grade": grade,
        "program_name": school,
        "class_name": f"{grade} - {school}",
        "collected_by": "EA One",
        "gender": gender,
        "letters_total_correct": letters,
        "nonwords_total_correct": 0,
        "words_total_correct": 0,
    }


class MatchedPairCohortTests(unittest.TestCase):
    def test_matched_pairs_carry_baseline_cohort_and_gender(self):
        data = pd.DataFrame(
            [
                _row("T1", "baseline", "Abraham Levy Primary School", "Grade 1", 10, "2026-02-01", gender="M"),
                _row("T1", "midline", "Abraham Levy Primary School", "Grade 1", 30, "2026-05-01", gender="M"),
            ]
        )
        matched = build_matched_assessment_pairs(helpers.add_cohort_column(data))
        self.assertIn("baseline_cohort", matched.columns)
        self.assertIn("midline_cohort", matched.columns)
        self.assertIn("gender", matched.columns)
        self.assertEqual(matched.iloc[0]["baseline_cohort"], "treatment")
        self.assertEqual(matched.iloc[0]["gender"], "M")

    def test_matched_pairs_anchor_uses_baseline_cohort_for_movers(self):
        # Learner baselined at a treatment school, midline at a control school
        data = pd.DataFrame(
            [
                _row("M1", "baseline", "Abraham Levy Primary School", "Grade 1", 10, "2026-02-01"),
                _row("M1", "midline", "Pendla Primary School", "Grade 1", 25, "2026-05-01"),
            ]
        )
        matched = build_matched_assessment_pairs(helpers.add_cohort_column(data))
        self.assertEqual(matched.iloc[0]["baseline_cohort"], "treatment")
        self.assertEqual(matched.iloc[0]["midline_cohort"], "control")


class OutstandingTrackerTests(unittest.TestCase):
    def _data(self):
        return pd.DataFrame(
            [
                # Abraham Levy (treatment), Grade 1
                _row("A", "baseline", "Abraham Levy Primary School", "Grade 1", 10, "2026-02-01"),
                _row("A", "midline", "Abraham Levy Primary School", "Grade 1", 30, "2026-05-01"),
                _row("B", "baseline", "Abraham Levy Primary School", "Grade 1", 12, "2026-02-01"),  # outstanding
                _row("C", "baseline", "Abraham Levy Primary School", "Grade 1", 8, "2026-02-01"),
                _row("C", "midline", "Pendla Primary School", "Grade 1", 20, "2026-05-01"),  # mover -> NOT outstanding
                # Pendla (control) baseline-only learner -> must NOT appear (treatment-only tracker)
                _row("D", "baseline", "Pendla Primary School", "Grade 1", 9, "2026-02-01"),
            ]
        )

    def test_outstanding_by_school_grade_counts(self):
        summary = helpers.outstanding_midline_by_school_grade(helpers.add_cohort_column(self._data()))
        row = summary[
            (summary["program_name"] == "Abraham Levy Primary School") & (summary["grade"] == "Grade 1")
        ].iloc[0]
        self.assertEqual(row["baseline_learners"], 3)   # A, B, C
        self.assertEqual(row["midline_learners"], 2)    # A, C (C did midline elsewhere)
        self.assertEqual(row["outstanding"], 1)         # B only
        self.assertAlmostEqual(row["percent_complete"], 66.7, places=1)

    def test_outstanding_excludes_control_schools(self):
        summary = helpers.outstanding_midline_by_school_grade(helpers.add_cohort_column(self._data()))
        self.assertNotIn("Pendla Primary School", set(summary["program_name"]))

    def test_outstanding_baseline_learners_lists_only_b(self):
        learners = helpers.outstanding_baseline_learners(helpers.add_cohort_column(self._data()))
        self.assertEqual(set(learners["participant_id"]), {"B"})


class CohortComparisonTests(unittest.TestCase):
    def _matched(self):
        data = pd.DataFrame(
            [
                _row("T1", "baseline", "Abraham Levy Primary School", "Grade 1", 10, "2026-02-01"),
                _row("T1", "midline", "Abraham Levy Primary School", "Grade 1", 30, "2026-05-01"),
                _row("T2", "baseline", "Abraham Levy Primary School", "Grade 1", 20, "2026-02-01"),
                _row("T2", "midline", "Abraham Levy Primary School", "Grade 1", 30, "2026-05-01"),
                _row("C1", "baseline", "Pendla Primary School", "Grade 1", 10, "2026-02-01"),
                _row("C1", "midline", "Pendla Primary School", "Grade 1", 15, "2026-05-01"),
            ]
        )
        return build_matched_assessment_pairs(helpers.add_cohort_column(data))

    def test_cohort_gain_summary_means_and_counts(self):
        summary = helpers.build_cohort_gain_summary(self._matched())
        treat = summary[(summary["cohort"] == "treatment") & (summary["grade"] == "Grade 1")].iloc[0]
        ctrl = summary[(summary["cohort"] == "control") & (summary["grade"] == "Grade 1")].iloc[0]
        self.assertEqual(treat["matched_learners"], 2)
        self.assertAlmostEqual(treat["letters_change"], 15.0, places=1)  # (20 + 10) / 2
        self.assertEqual(ctrl["matched_learners"], 1)
        self.assertAlmostEqual(ctrl["letters_change"], 5.0, places=1)

    def test_benchmark_by_cohort_matched_uses_same_learners_both_phases(self):
        summary = helpers.benchmark_by_cohort_matched(self._matched(), "Grade 1", 25)
        treat_mid = summary[(summary["cohort"] == "treatment") & (summary["Phase"] == "Midline")].iloc[0]
        treat_base = summary[(summary["cohort"] == "treatment") & (summary["Phase"] == "Baseline")].iloc[0]
        self.assertEqual(treat_mid["Learners"], 2)
        self.assertAlmostEqual(treat_mid["Percent"], 100.0, places=1)  # both 30 >= 25
        self.assertAlmostEqual(treat_base["Percent"], 0.0, places=1)   # 10, 20 < 25


class DescriptiveChartHelperTests(unittest.TestCase):
    def test_zero_letter_summary_per_phase(self):
        data = pd.DataFrame(
            [
                _row("z1", "baseline", "Abraham Levy Primary School", "Grade 1", 0, "2026-02-01"),
                _row("z2", "baseline", "Abraham Levy Primary School", "Grade 1", 5, "2026-02-01"),
                _row("z1", "midline", "Abraham Levy Primary School", "Grade 1", 3, "2026-05-01"),
                _row("z2", "midline", "Abraham Levy Primary School", "Grade 1", 8, "2026-05-01"),
            ]
        )
        summary = helpers.zero_letter_summary(data, "Grade 1")
        base = summary[summary["Phase"] == "Baseline"].iloc[0]
        mid = summary[summary["Phase"] == "Midline"].iloc[0]
        self.assertEqual(base["Zero Letters"], 1)
        self.assertAlmostEqual(base["Percent"], 50.0, places=1)
        self.assertEqual(mid["Zero Letters"], 0)

    def test_benchmark_by_school_summary_percent(self):
        data = pd.DataFrame(
            [
                _row("s1", "midline", "Abraham Levy Primary School", "Grade 1", 3, "2026-05-01"),
                _row("s2", "midline", "Abraham Levy Primary School", "Grade 1", 8, "2026-05-01"),
            ]
        )
        summary = helpers.benchmark_by_school_summary(data, "Grade 1", 5, phase="midline")
        row = summary[summary["program_name"] == "Abraham Levy Primary School"].iloc[0]
        self.assertEqual(row["learners"], 2)
        self.assertEqual(row["at_or_above"], 1)
        self.assertAlmostEqual(row["percent"], 50.0, places=1)

    def test_ea_gain_summary_respects_min_learners(self):
        data = pd.DataFrame(
            [
                _row("T1", "baseline", "Abraham Levy Primary School", "Grade 1", 10, "2026-02-01"),
                _row("T1", "midline", "Abraham Levy Primary School", "Grade 1", 30, "2026-05-01"),
                _row("T2", "baseline", "Abraham Levy Primary School", "Grade 1", 20, "2026-02-01"),
                _row("T2", "midline", "Abraham Levy Primary School", "Grade 1", 30, "2026-05-01"),
            ]
        )
        matched = build_matched_assessment_pairs(helpers.add_cohort_column(data))
        included = helpers.build_ea_gain_summary(matched, min_learners=1)
        self.assertAlmostEqual(included.iloc[0]["letters_change"], 15.0, places=1)
        self.assertEqual(included.iloc[0]["matched_learners"], 2)
        self.assertTrue(helpers.build_ea_gain_summary(matched, min_learners=5).empty)

    def test_gender_gain_summary_and_empty_degradation(self):
        data = pd.DataFrame(
            [
                _row("T1", "baseline", "Abraham Levy Primary School", "Grade 1", 10, "2026-02-01", gender="M"),
                _row("T1", "midline", "Abraham Levy Primary School", "Grade 1", 30, "2026-05-01", gender="M"),
                _row("T2", "baseline", "Abraham Levy Primary School", "Grade 1", 20, "2026-02-01", gender="F"),
                _row("T2", "midline", "Abraham Levy Primary School", "Grade 1", 30, "2026-05-01", gender="F"),
            ]
        )
        matched = build_matched_assessment_pairs(helpers.add_cohort_column(data))
        summary = helpers.build_gender_gain_summary(matched)
        self.assertEqual(set(summary["gender"]), {"M", "F"})

        no_gender = build_matched_assessment_pairs(
            helpers.add_cohort_column(
                pd.DataFrame(
                    [
                        _row("N1", "baseline", "Abraham Levy Primary School", "Grade 1", 10, "2026-02-01"),
                        _row("N1", "midline", "Abraham Levy Primary School", "Grade 1", 30, "2026-05-01"),
                    ]
                )
            )
        )
        self.assertTrue(helpers.build_gender_gain_summary(no_gender).empty)


if __name__ == "__main__":
    unittest.main()
