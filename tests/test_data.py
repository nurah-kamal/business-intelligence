import json
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import make_data  # noqa: E402

DATA = ROOT / "data"


class Data(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.y, cls.index = make_data.load_cpi()
        cls.forecasts, cls.tests = make_data.backtest(cls.y, cls.index)

    def test_committed_files_match_the_script(self):
        pd.testing.assert_frame_equal(pd.read_csv(DATA / "forecasts.csv"), self.forecasts, check_dtype=False)
        pd.testing.assert_frame_equal(pd.read_csv(DATA / "tests.csv"), self.tests, check_dtype=False)
        self.assertEqual(json.loads((DATA / "expected.json").read_text()), make_data.expected(self.forecasts, self.tests))

    def test_calendar_covers_every_month_once(self):
        cal = pd.read_csv(DATA / "calendar.csv")
        months = pd.to_datetime(cal["month"])
        self.assertTrue(months.is_unique)
        self.assertEqual(len(cal), (months.max().year - months.min().year) * 12 + months.max().month - months.min().month + 1)
        used = set(self.forecasts["origin"]) | set(self.forecasts["target_month"])
        self.assertTrue(used <= set(cal["month"]))

    def test_no_forecast_saw_its_outcome(self):
        f = self.forecasts
        self.assertTrue((pd.to_datetime(f["target_month"]) > pd.to_datetime(f["origin"])).all())
        gap = (pd.to_datetime(f["target_month"]).dt.to_period("M") - pd.to_datetime(f["origin"]).dt.to_period("M")).apply(lambda d: d.n)
        self.assertTrue((gap == f["horizon"]).all())

    # Published in statistical-modelling/cpi-inflation-forecast (run_output.txt).
    def test_errors_match_the_published_backtest(self):
        e = make_data.expected(self.forecasts, self.tests)["mae"]
        published = {
            "1": (0.293, 0.296, 0.776),
            "3": (0.662, 0.597, 0.949),
            "6": (0.892, 0.870, 1.133),
            "12": (1.110, 1.277, 1.356),
        }
        for h, values in published.items():
            got = tuple(e[h][m] for m, _, _ in make_data.METHODS)
            self.assertEqual(got, values, h)


if __name__ == "__main__":
    unittest.main()
