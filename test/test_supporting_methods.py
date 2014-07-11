# Copyright 2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import unittest
from datetime import datetime
from edda.supporting_methods import *

# Some months for testing
JUL = 7
MAY = 5

# Some weekdays for testing
MON = 0
TUE = 1
WED = 2
THU = 3
FRI = 4
SAT = 5
SUN = 6

class test_supporting_methods(unittest.TestCase):

    #--------------------------------
    # test date-related functionality
    #--------------------------------

    def test_has_same_weekday(self):
        # The equivalent weekday in different years
        assert has_same_weekday(15, JUL, WED, 2009)
        assert has_same_weekday(14, JUL, WED, 2010)
        assert has_same_weekday(13, JUL, WED, 2011)
        assert has_same_weekday(18, JUL, WED, 2012)
        assert has_same_weekday(17, JUL, WED, 2013)
        assert has_same_weekday(16, JUL, WED, 2014)

        # The same date in multiple years
        assert has_same_weekday(31, MAY, SUN, 2009)
        assert has_same_weekday(31, MAY, MON, 2010)
        assert has_same_weekday(31, MAY, TUE, 2011)
        assert has_same_weekday(31, MAY, THU, 2012)
        assert has_same_weekday(31, MAY, FRI, 2013)
        assert has_same_weekday(31, MAY, SAT, 2014)

        # Wrong things
        assert not has_same_weekday(31, MAY, SAT, 2009)
        assert not has_same_weekday(31, MAY, SUN, 2008)
        assert not has_same_weekday(30, MAY, MON, 2010)
        assert not has_same_weekday(30, MAY, THU, 2011)
        assert not has_same_weekday(30, MAY, FRI, 2013)
        assert not has_same_weekday(30, MAY, SAT, 2014)

    def test_guess_log_year(self):
        assert guess_log_year(15, JUL, WED) == 2009
        assert guess_log_year(14, JUL, WED) == 2010
        assert guess_log_year(13, JUL, WED) == 2011
        assert guess_log_year(18, JUL, WED) == 2012
        assert guess_log_year(17, JUL, WED) == 2013
        assert guess_log_year(16, JUL, WED) == 2014

        assert not guess_log_year(16, JUL, WED) == 2009
        assert not guess_log_year(16, JUL, WED) == 2010
        assert not guess_log_year(16, JUL, WED) == 2011
        assert not guess_log_year(16, JUL, WED) == 2012
        assert not guess_log_year(16, JUL, WED) == 2013

        # July 16 was on a Wednesday in 2008, but 2014 precedes.
        assert not guess_log_year(16, JUL, WED) == 2008

    def test_date_parser_old_logs(self):
        parsed_date = date_parser("Wed Jul 18 13:14:15")
        assert parsed_date.day == 18
        assert parsed_date.year == 2012
        assert parsed_date.month == 7
        assert parsed_date.hour == 13
        assert parsed_date.minute == 14
        assert parsed_date.second == 15

    def test_date_parser_new_logs(self):
        # 2.6 and beyond
        parsed_date = date_parser("2014-04-10T16:20:59.271-0400")
        assert parsed_date.year == 2014
        assert parsed_date.month == 4
        assert parsed_date.day == 10
        assert parsed_date.hour == 16
        assert parsed_date.minute == 20

if __name__ == '__main__':
    unittest.main()
