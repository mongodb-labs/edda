# Copyright 2012 10gen, Inc.
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

from edda.filters.rs_exit import *
from datetime import datetime


class test_rs_exit(unittest.TestCase):
    def test_criteria(self):
        assert not criteria("this should not pass")
        assert criteria("Thu Jun 14 11:43:28 dbexit: really exiting now") == 1
        assert not criteria("Foo bar")


    def test_process(self):
        date = datetime.now()
        self.check_state("Thu Jun 14 11:43:28 dbexit: really exiting now", 2, date)
        self.check_state("Thu Jun 14 11:43:28 dbexit: really exiting now", 2, date)
        assert not process("This should fail", date)


    def check_state(self, message, code, date):
        doc = process(message, date)
        print doc
        assert doc
        assert doc["type"] == "exit"
        assert doc["msg"] == message
        assert doc["info"]["server"] == "self"
        #print 'Server number is: *{0}*, testing against, *{1}*'.format(doc["info"]["server"], server)

if __name__ == '__main__':
    unittest.main()
