import unittest

from fairyex.darksol import _get_period_type, _get_sample_name


class TestDarkSolUtils(unittest.TestCase):

    def test_get_period_type(self):
        for period_type, user_period_types in {
            "Interval": ["Interval", "interval", "i"],
            "FiscalYear": ["FiscalYear", "Fiscal Year", "fiscalyear", "Year", "yearly", "y"],
        }.items():
            for user_period_type in user_period_types:
                self.assertEqual(_get_period_type(user_period_type), period_type)

    def test_get_sample_name(self):
        for sample_id, sample_name in {
            "-666": "Statistic 666",
            "-4": "Statistic 4",
            "-3": "Max",
            "-2": "Min",
            "-1": "Std",
            "0": "Mean",
            "1": "Sample 1",
            "42": "Sample 42",
        }.items():
            self.assertEqual(_get_sample_name(sample_id), sample_name)
