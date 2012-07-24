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

import string
import unittest

from datetime import datetime
from edda.filters.rs_reconfig import *


class test_rs_reconfig(unittest.TestCase):
    def test_criteria(self):
        assert not criteria("this should not pass")
        assert criteria("Tue Jul  3 10:20:15 [rsMgr]"
            " replSet replSetReconfig new config saved locally") == 1
        assert not criteria("Tue Jul  3 10:20:15 [rsMgr]"
            " replSet new config saved locally")
        assert not criteria("Tue Jul  3 10:20:15 [rsMgr] replSet info : additive change to configuration")

    def test_process(self):
        date = datetime.now()
        self.check_state("Tue Jul  3 10:20:15 [rsMgr] replSet"
            " replSetReconfig new config saved locally", 0, date, None)
        assert process("This should fail", date) == None

    def check_state(self, message, code, date, server):
        doc = process(message, date)
        assert doc
        assert doc["date"] == date
        assert doc["type"] == "reconfig"
        assert doc["msg"] == message
        assert doc["info"]["server"] == "self"

if __name__ == '__main__':
    unittest.main()
