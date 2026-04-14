import unittest
from pathlib import Path
import sys
import warnings

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data_privacy import mask_dataframe


class DataPrivacyTests(unittest.TestCase):
    def test_masks_child_and_school_variants(self):
        df = pd.DataFrame(
            {
                "School": ["Emzomncane", "Emzomncane"],
                "Name": ["Devane", "Akahlulwa"],
                "Surname": ["Oliphant", "Classen"],
                "Full names": ["Oliphant Devane", "Classen Akahlulwa"],
                "Notes": ["Oliphant Devane attends Emzomncane.", "Classen Akahlulwa attends Emzomncane."],
            }
        )

        masked = mask_dataframe(df, authenticated=False)

        self.assertTrue(masked["School"].str.startswith("School ").all())
        self.assertTrue(masked["Full names"].str.startswith("Child ").all())
        self.assertEqual(masked.loc[0, "School"], masked.loc[1, "School"])
        self.assertEqual(masked.loc[0, "Notes"], "Masked text")
        self.assertNotIn("Emzomncane", masked.loc[0, "Notes"])
        self.assertNotIn("Oliphant Devane", masked.loc[0, "Notes"])

    def test_masks_ta_variants_and_derived_text(self):
        df = pd.DataFrame(
            {
                "name_first_ta": ["Andy"],
                "name_second_ta": ["Andrews"],
                "name_ta": ["Andy Andrews"],
                "school_rep": ["Test City"],
                "instance_name": ["EGRA form: Test City - Andy Andrews"],
            }
        )

        masked = mask_dataframe(df, authenticated=False)

        self.assertEqual(masked.loc[0, "name_first_ta"], "TA")
        self.assertTrue(masked.loc[0, "name_ta"].startswith("TA "))
        self.assertTrue(masked.loc[0, "school_rep"].startswith("School "))
        self.assertEqual(masked.loc[0, "instance_name"], "Masked instance")

    def test_masks_mentor_visit_columns(self):
        df = pd.DataFrame(
            {
                "Mentor Name": ["Ayabonga Hoboshe"],
                "School Name": ["Cebelihle Primary School"],
                "EA Name": ["Zethu Beya"],
                "Any additional commentary?": [
                    "Ayabonga Hoboshe visited Cebelihle Primary School and coached Zethu Beya."
                ],
            }
        )

        masked = mask_dataframe(df, dataset_key="mentor_visits_2025", authenticated=False)

        self.assertTrue(masked.loc[0, "Mentor Name"].startswith("Mentor "))
        self.assertTrue(masked.loc[0, "School Name"].startswith("School "))
        self.assertTrue(masked.loc[0, "EA Name"].startswith("TA "))
        self.assertEqual(masked.loc[0, "Any additional commentary?"], "Masked text")

    def test_masks_team_pact_child_columns(self):
        df = pd.DataFrame(
            {
                "program_name": ["David Vuku Primary School"],
                "class_name": ["1 A-Group 4-David Vuku"],
                "first_name": ["Sinentlantla"],
                "last_name": ["Jomose"],
                "user_name": ["Alinda Turwana"],
            }
        )

        masked = mask_dataframe(df, authenticated=False)

        self.assertTrue(masked.loc[0, "program_name"].startswith("School "))
        self.assertTrue(masked.loc[0, "class_name"].startswith("Class "))
        self.assertEqual(masked.loc[0, "first_name"], "Child")
        self.assertEqual(masked.loc[0, "user_name"].split(" ")[0], "TA")

    def test_authenticated_returns_original_data(self):
        df = pd.DataFrame({"School": ["Real School"], "Name": ["Real"]})
        masked = mask_dataframe(df, authenticated=True)
        self.assertEqual(masked.loc[0, "School"], "Real School")
        self.assertEqual(masked.loc[0, "Name"], "Real")

    def test_masks_numeric_group_column_without_dtype_warning(self):
        df = pd.DataFrame(
            {
                "group": [1, 1, 2],
                "school_rep": ["School A", "School A", "School B"],
            }
        )

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("error", FutureWarning)
            masked = mask_dataframe(df, authenticated=False)

        self.assertEqual(len(caught), 0)
        self.assertTrue(masked["group"].str.startswith("Group ").all())


if __name__ == "__main__":
    unittest.main()
