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

from datetime import datetime
from edda.filters.rs_sync import *


class test_rs_sync(unittest.TestCase):
    def test_criteria(self):
        assert (criteria("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017") == 1)
        #should fail, absence of word "syncing": malformed message
        assert not criteria("Tue Jun 12 13:08:47 [rsSync] replSet to: localhost:27017")
        #should fail, absence of [rsSync]: malformed message
        assert not criteria("Tue Jun 12 13:08:47 replSet to: localhost:27017")
        #should pass, it doesn't test to see if there is a valid port number until test_syncingDiff: malformed message to fail at another point
        assert criteria("Tue Jun 12 13:08:47 [rsSync] replSet syncing to:") == 1
        #should pass in this situation, date is irrevealant
        assert criteria("[rsSync] replSet syncing to: localhost:27017") == 1
        #foo bar test from git comment
        assert not criteria("foo bar")
        assert criteria("[rsSync] replSet syncing to:") == 1
        assert criteria("[rsSync] syncing [rsSync]") == 1
        assert not criteria("This should fail!!! [rsSync]")
        return


    def test_process(self):
        date = datetime.now()
        assert process("Mon Jun 11 15:56:16 [rsStart] replSet localhost:27018", date) == None
        assert process("Mon Jun 11 15:56:18 [rsHealthPoll] replSet member localhost:27019 is up", date) == None
        self.check_state("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017", "localhost:27017")
        self.check_state("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: 10.4.3.56:45456", "10.4.3.56:45456")
        self.check_state("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: 10.4.3.56:45456", "10.4.3.56:45456")
        self.check_state("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: 10.4.3.56:45456", "10.4.3.56:45456")
        self.check_state("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: 10.4.3.56:45456", "10.4.3.56:45456")
        self.check_state("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:1234", "localhost:1234")
        self.check_state("[rsSync] syncing to: 10.4.3.56:45456", "10.4.3.56:45456")


    def test_syncing_diff(self):

        currTime = datetime.now()
        test = syncing_diff("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017", process("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017", currTime))
        assert test
        assert test["type"] == 'sync'


    def check_state(self, message, server):
        date = datetime.now()
        doc = process(message, date)
        assert doc["type"] == "sync"
        #print 'Server number is: *{0}*, testing against, *{1}*'.format(doc["info"]["server"], server)
        assert doc["info"]["sync_server"] == server
        assert doc["info"]["server"] == "self"

if __name__ == '__main__':
    unittest.main()
