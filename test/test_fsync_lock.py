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
from edda.filters.fsync_lock import *
from datetime import datetime


# Mon Jul  2 10:00:11 [conn2] CMD fsync: sync:1 lock:1
# Mon Jul  2 10:00:04 [conn2] command: unlock requested
# Mon Jul  2 10:00:10 [conn2] db is now locked for snapshotting, no writes allowed. db.fsyncUnlock() to unlock


class test_fsync_lock(unittest.TestCase):
    def test_criteria(self):
        assert criteria("this should not pass") == -1
        assert criteria("Mon Jul  2 10:00:10 [conn2] db is now locked for "
            "snapshotting, no writes allowed. db.fsyncUnlock() to unlock") == 3
        assert criteria("Mon Jul  2 10:00:04 [conn2] command: "
            "unlock requested") == 1
        assert criteria("Mon Jul  2 10:00:11 [conn2] "
            "CMD fsync: sync:1 lock:1") == 2
        assert criteria("Thu Jun 14 11:25:18 [conn2] replSet RECOVERING") == -1

    def test_process(self):
        date = datetime.now()
        self.check_state("Mon Jul  2 10:00:10 [conn2] db is now locked for snapshotting"
            ", no writes allowed. db.fsyncUnlock() to unlock", "LOCKED", date, 0, 0)
        self.check_state("Mon Jul  2 10:00:04 [conn2] command: unlock requested"
            "", "UNLOCKED", date, 0, 0)
        self.check_state("Mon Jul  2 10:00:11 [conn2] CMD fsync: sync:1 lock:1"
            "", "FSYNC", date, 1, 1)

        # All of the following should return None
        assert process("Thu Jun 14 11:25:18 [conn2] replSet RECOVERING", date) == None
        assert process("This should fail", date) == None
        assert process("Thu Jun 14 11:26:05 [conn7] replSet info voting yea for localhost:27019 (2)\n", date) == None
        assert process("Thu Jun 14 11:26:10 [rsHealthPoll] couldn't connect to localhost:27017: couldn't connect to server localhost:27017\n", date) == None
        assert process("Thu Jun 14 11:28:57 [websvr] admin web console waiting for connections on port 28020\n", date) == None

    def check_state(self, message, code, date, sync, lock):
        doc = process(message, date)
        assert doc
        assert doc["type"] == "fsync"
        assert doc["original_message"] == message
        assert doc["info"]["server"] == "self"
        #if sync != 0:
        #	print "Sync Num: {}".format(doc["info"]["sync_num"])
        # 	assert doc["info"]["sync_num"] == sync
        #	assert doc["info"]["lock_num"] == lock

        #print 'Server number is: *{0}*, testing against, *{1}*'.format(doc["info"]["server"], server)
if __name__ == '__main__':
    unittest.main()