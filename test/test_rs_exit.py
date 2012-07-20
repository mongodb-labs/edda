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
from logl.filters.rs_exit import *
from datetime import datetime


class test_rs_exit(unittest.TestCase):
    def test_criteria(self):
        assert criteria("this should not pass") == -1

        assert criteria("Thu Jun 14 11:43:28 dbexit: really exiting now") == 2
        
        assert criteria("Foo bar") == -1

    def test_process(self):
        date = datetime.now()
        self.check_state("Thu Jun 14 11:43:28 dbexit: really exiting now", 2, date)
        
        self.check_state("Thu Jun 14 11:43:28 dbexit: really exiting now", 2, date)
        assert process("This should fail", date) == None

    def check_state(self, message, code, date):
        doc = process(message, date)
        print doc
        assert doc
        assert doc["type"] == "exit"
        assert doc["original_message"] == message
        assert doc["info"]["server"] == "self"
        #print 'Server number is: *{0}*, testing against, *{1}*'.format(doc["info"]["server"], server)

if __name__ == '__main__':
    unittest.main()
