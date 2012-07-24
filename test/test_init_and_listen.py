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
from edda.filters.init_and_listen import *
from datetime import datetime

class test_init_and_listen(unittest.TestCase):
    def test_criteria(self):
        """Test the criteria() method of this module"""
        # these should not pass
        assert criteria("this should not pass") < 1
        assert criteria("Mon Jun 11 15:56:40 [conn5] end connection "
            "127.0.0.1:55224 (2 connections now open)") == 0
        assert criteria("Mon Jun 11 15:56:16 [initandlisten] ** WARNING: soft "
            "rlimits too low. Number of files is 256, should be at least 1000"
            "") == 0
        assert criteria("init and listen starting") == 0
        assert criteria("[initandlisten]") == 0
        assert criteria("starting") == 0
        assert criteria("connection accepted") == 0
        # these should pass
        assert criteria("Mon Jun 11 15:56:16 [initandlisten] MongoDB starting "
            ": pid=7029 port=27018 dbpath=/data/rs2 64-bit "
            "host=Kaushals-MacBook-Air.local") == 1
        return


    def test_process(self):
        """test the process() method of this module"""
        date = datetime.now()
        # non-valid message
        assert process("this is an invalid message", date) == None
        # these should pass
        doc = process("Mon Jun 11 15:56:16 [initandlisten] MongoDB starting : "
            "pid=7029 port=27018 dbpath=/data/rs2 64-bit host=Kaushals-MacBook-Air"
            ".local", date)
        assert doc
        assert doc["type"] == "init"
        assert doc["info"]["server"] == "self"
        assert doc["info"]["subtype"] == "startup"
        assert doc["info"]["addr"] == "Kaushals-MacBook-Air.local:27018"
        return


    def test_starting_up(self):
        """test the starting_up() method of this module"""
        doc = {}
        doc["type"] = "init"
        doc["info"] = {}
        # non-valid message
        assert not starting_up("this is a nonvalid message", doc)
        assert not starting_up("Mon Jun 11 15:56:16 [initandlisten] MongoDB starting "
            ": 64-bit host=Kaushals-MacBook-Air.local", doc)
        # valid messages
        doc = starting_up("Mon Jun 11 15:56:16 [initandlisten] MongoDB starting : "
            "pid=7029 port=27018 dbpath=/data/rs2 64-bit "
            "host=Kaushals-MacBook-Air.local", doc)
        assert doc
        assert doc["type"] == "init"
        assert doc["info"]["subtype"] == "startup"
        assert doc["info"]["server"] == "self"
        assert doc["info"]["addr"] == "Kaushals-MacBook-Air.local:27018"
        return

if __name__ == '__main__':
    unittest.main()
