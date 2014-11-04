import unittest
from mock import Mock, patch, MagicMock, call
import timeclock as tc
from datetime import date, datetime


def _entry(action, date):
    return "%s %s %s" % (action, date.strftime("%s"), date.isoformat())

class clockTests(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @patch('__builtin__.print')
    @patch("__builtin__.open")
    def test_calculate_daily_totals__multiple_entries(self, mockopen,
                                                      mockprint):
        mockopen.return_value = MagicMock()
        handle = mockopen.return_value.__enter__.return_value
        handle.__iter__.return_value = iter([
            _entry("IN", datetime(2013, 10, 1, 1, 0, 0)),
            _entry("OUT", datetime(2013, 10, 1, 2, 14, 0)),
            _entry("IN", datetime(2013, 10, 1, 3, 10, 0)),
            _entry("OUT", datetime(2013, 10, 1, 3, 24, 0)),
            _entry("IN", datetime(2013, 10, 2, 1, 2, 0)),
            _entry("OUT", datetime(2013, 10, 2, 2, 32, 0)),
            _entry("IN", datetime(2013, 10, 2, 5, 9, 0)),
            _entry("OUT", datetime(2013, 10, 2, 6, 39, 0)),
            ])
        start = date(2013, 10, 1)
        end = date(2013, 10, 7)
        tc.calculate_daily_totals(start, end)
        mockopen.assert_called()
        mockprint.assert_has_calls([
            call('2013-10-01 - 1.5 hours'), call('2013-10-02 - 3.0 hours'),
            call('\n4.5 hours total between 2013-10-01 and 2013-10-07')])

    @patch('__builtin__.print')
    @patch("__builtin__.open")
    def test_calculate_daily_totals__date_window(self, mockopen, mockprint):
        mockopen.return_value = MagicMock()
        handle = mockopen.return_value.__enter__.return_value
        handle.__iter__.return_value = iter([
            _entry("IN", datetime(2013, 9, 30, 1, 0, 0)),
            _entry("OUT", datetime(2013, 9, 30, 8, 0, 0)),
            _entry("IN", datetime(2013, 10, 1, 1, 0, 0)),
            _entry("OUT", datetime(2013, 10, 1, 2, 0, 0)),
            _entry("IN", datetime(2013, 10, 2, 1, 0, 0)),
            _entry("OUT", datetime(2013, 10, 2, 2, 0, 0)),
            _entry("IN", datetime(2013, 10, 3, 1, 0, 0)),
            _entry("OUT", datetime(2013, 10, 3, 2, 0, 0)),
            _entry("IN", datetime(2013, 10, 8, 1, 0, 0)),
            _entry("OUT", datetime(2013, 10, 8, 2, 0, 0)),
            ])
        start = date(2013, 10, 1)
        end = date(2013, 10, 7)
        tc.calculate_daily_totals(start, end)
        mockopen.assert_called()
        mockprint.assert_has_calls([
            call('2013-10-01 - 1.0 hours'), call('2013-10-02 - 1.0 hours'),
            call('2013-10-03 - 1.0 hours'),
            call('\n3.0 hours total between 2013-10-01 and 2013-10-07')])


if __name__ == "__main__":
    unittest.main()
