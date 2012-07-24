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
from edda.filters.rs_status import *
from datetime import datetime


class test_rs_status(unittest.TestCase):
    def test_criteria(self):
        """test the criteria() method of this module"""
        # invalid messages
        assert criteria("this is an invalid message") < 0
        assert criteria("I am the primary") < 0
        assert criteria("I am the secondary") < 0
        assert criteria("the server is down") < 0
        assert criteria("the server is back up") < 0
        # check for proper return codes
        assert criteria(
            "Mon Jun 11 15:56:16 [rsStart] replSet I am localhost:27018") == 0
        assert criteria("Mon Jun 11 15:57:04 [rsMgr] replSet PRIMARY") == 1
        assert criteria("Mon Jun 11 15:56:16 [rsSync] replSet SECONDARY") == 2
        assert criteria("replSet RECOVERING") == 3
        assert criteria("replSet encountered a FATAL ERROR") == 4
        assert criteria("Mon Jun 11 15:56:16 [rsStart] replSet STARTUP2") == 5
        assert criteria("replSet member is now in state UNKNOWN") == 6
        assert criteria("Mon Jun 11 15:56:18 [rsHealthPoll] "
            "replSet member localhost:27019 is now in state ARBITER") == 7
        assert criteria("Mon Jun 11 15:56:58 [rsHealthPoll] "
            "replSet member localhost:27017 is now in state DOWN") == 8
        assert criteria("replSet member is now in state ROLLBACK") == 9
        assert criteria("replSet member is now in state REMOVED") == 10
        return

    def test_process(self):
        """test the process() method of this module"""
        date = datetime.now()
        # invalid lines
        assert process("Mon Jun 11 15:56:16 "
            "[rsStart] replSet localhost:27018", date) == None
        assert process("Mon Jun 11 15:56:18 "
            "[rsHealthPoll] replSet member localhost:27019 is up", date) == None
        # valid lines
        self.check_state("Mon Jun 11 15:56:16 "
            "[rsStart] replSet I am", "STARTUP1", 0, "self")
        self.check_state("[rsMgr] replSet PRIMARY", "PRIMARY", 1, "self")
        self.check_state("[rsSync] replSet SECONDARY", "SECONDARY", 2, "self")
        self.check_state("[rsSync] replSet is RECOVERING", "RECOVERING", 3, "self")
        self.check_state("[rsSync] replSet member "
            "encountered FATAL ERROR", "FATAL", 4, "self")
        self.check_state("[rsStart] replSet STARTUP2", "STARTUP2", 5, "self")
        self.check_state(
            "Mon Jul 11 11:56:32 [rsSync] replSet member"
            " 10.4.3.56:45456 is now in state UNKNOWN",
            "UNKNOWN", 6, "10.4.3.56:45456")
        self.check_state("Mon Jul 11 11:56:32"
                         " [rsHealthPoll] replSet member localhost:27019"
                         " is now in state ARBITER", "ARBITER", 7, "localhost:27019")
        self.check_state("Mon Jul 11 11:56:32"
                         " [rsHealthPoll] replSet member "
                         "localhost:27017 is now in state DOWN", "DOWN", 8, "localhost:27017")
        self.check_state("Mon Jul 11 11:56:32"
                         " [rsSync] replSet member example@domain.com:22234"
            " is now in state ROLLBACK", "ROLLBACK", 9, "example@domain.com:22234")
        self.check_state("Mon Jul 11 11:56:32"
                         " [rsSync] replSet member my-MacBook-pro:43429 has been REMOVED"
            "", "REMOVED", 10, "my-MacBook-pro:43429")


    def test_startup_with_network_name(self):
        """Test programs's ability to capture IP address from
        a STARTUP message"""
        self.check_state_with_addr("Mon Jun 11 15:56:16 [rsStart]"
            " replSet I am 10.4.65.7:27018", "STARTUP1", 0, "10.4.65.7:27018")


    def test_startup_with_hostname(self):
        """Test that program captures hostnames from
        STARTUP messages as well as IP addresses"""
        self.check_state_with_addr("Mon Jun 11 15:56:16 [rsStart]"
            " replSet I am sam@10gen.com:27018", "STARTUP1", 0, "sam@10gen.com:27018")


    def check_state_with_addr(self, msg, state, code, server):
        date = datetime.now()
        doc = process(msg, date)
        assert doc
        assert doc["type"] == "status"
        assert doc["info"]["state_code"] == code
        assert doc["info"]["state"] == state
        assert doc["info"]["server"] == "self"
        assert doc["info"]["addr"] == server


    def check_state(self, msg, state, code, server):
        """Helper method to test documents generated by rs_status.process()"""
        date = datetime.now()
        doc = process(msg, date)
        assert doc
        assert doc["type"] == "status"
        assert doc["info"]["state_code"] == code
        assert doc["info"]["state"] == state
        assert doc["info"]["server"] == server

if __name__ == '__main__':
    unittest.main()
