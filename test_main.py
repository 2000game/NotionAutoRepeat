import unittest
from datetime import datetime
from main import update_date_from_frequency

class TestUpdateDateFromFrequency(unittest.TestCase):
    def test_update_date_from_frequency_monthly(self):
        frequency = "Monthly"
        date = datetime.strptime("2023-03-07", "%Y-%m-%d")
        new_date = datetime.strptime("2023-04-07", "%Y-%m-%d")
        new_date = datetime.strftime(new_date, "%Y-%m-%d")
        self.assertEqual(update_date_from_frequency(date, frequency), new_date)


if __name__ == '__main__':
    unittest.main()
