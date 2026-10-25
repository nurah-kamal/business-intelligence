import json
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import make_data  # noqa: E402

DATA = ROOT / "data"


def read(name):
    return pd.read_csv(DATA / name, keep_default_na=False)


class Data(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = make_data.make_employees()

    def test_committed_files_match_the_script(self):
        pd.testing.assert_frame_equal(read("employees.csv"), self.df.astype({"salary": "int64"}), check_dtype=False)
        pd.testing.assert_frame_equal(read("job.csv"), make_data.make_jobs(), check_dtype=False)
        pd.testing.assert_frame_equal(read("department.csv"), make_data.make_departments(), check_dtype=False)
        pd.testing.assert_frame_equal(read("calendar.csv"), make_data.make_calendar(), check_dtype=False)
        self.assertEqual(json.loads((DATA / "expected.json").read_text()), make_data.expected(self.df))

    def test_people_and_dates_make_sense(self):
        df = self.df
        self.assertTrue(df["employee_id"].is_unique)
        hire = pd.to_datetime(df["hire_date"])
        leave = pd.to_datetime(df["leave_date"].replace("", None))
        left = leave.notna()
        self.assertTrue((leave[left] > hire[left]).all())
        self.assertTrue((leave[left] <= make_data.AS_OF).all())
        self.assertTrue((hire <= make_data.AS_OF).all())
        self.assertTrue((df.loc[left, "leave_reason"] != "").all())
        self.assertTrue((df.loc[~left, "leave_reason"] == "").all())

    def test_no_names_in_the_data(self):
        self.assertFalse({"first_name", "last_name", "name"} & set(self.df.columns))

    # The three planted patterns (make_data.PLANTED). If these fail, the report no longer finds them.
    def test_call_centre_attrition_jumps_after_mid_2025(self):
        e = make_data.expected(self.df)["call_centre_agent_attrition_12m"]
        self.assertGreater(e["to_2026-06-30"], 2 * e["to_2025-06-30"])

    def test_women_in_it_resign_more_often(self):
        it = self.df[self.df["department"] == "IT"]
        rate = {}
        for g in ("Female", "Male"):
            x = it[it["gender"] == g]
            end = pd.to_datetime(x["leave_date"].replace("", None)).fillna(make_data.AS_OF)
            years = (end - pd.to_datetime(x["hire_date"])).dt.days.sum() / 365.25
            rate[g] = (x["leave_reason"] == "Resigned").sum() / years
        self.assertGreater(rate["Female"], 1.4 * rate["Male"])

    def test_designated_groups_are_under_represented_at_the_top(self):
        e = make_data.expected(self.df)["designated_share_pct"]
        self.assertLess(e["top_and_senior_current"], e["all_current"] / 2)


if __name__ == "__main__":
    unittest.main()
