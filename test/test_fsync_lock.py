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

from logl.filters.fsync_lock import *
from datetime import datetime


# Mon Jul  2 10:00:11 [conn2] CMD fsync: sync:1 lock:1
# Mon Jul  2 10:00:04 [conn2] command: unlock requested
# Mon Jul  2 10:00:10 [conn2] db is now locked for snapshotting, no writes allowed. db.fsyncUnlock() to unlock
def test_criteria():
    assert criteria("this should not pass") == -1
    assert criteria("Mon Jul  2 10:00:10 [conn2] db is now locked for snapshotting, no writes allowed. db.fsyncUnlock() to unlock") == 0
    assert criteria("Mon Jul  2 10:00:04 [conn2] command: unlock requested") == 1
    assert criteria("Mon Jul  2 10:00:11 [conn2] CMD fsync: sync:1 lock:1") == 2


def test_process():
    date = datetime.now()
    check_state("Mon Jul  2 10:00:10 [conn2] db is now locked for snapshotting, no writes allowed. db.fsyncUnlock() to unlock", 0, date, 0, 0)
    check_state("Mon Jul  2 10:00:04 [conn2] command: unlock requested", 1, date, 0, 0)
    check_state("Mon Jul  2 10:00:11 [conn2] CMD fsync: sync:1 lock:1", 2, date, 1, 1)
    assert process("This should fail", date) == None


def check_state(message, code, date, sync, lock):
    doc = process(message, date)
    assert doc
    assert doc["type"] == "conn"
    assert doc["original_message"] == message
    assert doc["info"]["state_code"] == code
    if sync != 0:
    	print "Sync Num: {}".format(doc["info"]["sync_num"])
    	assert doc["info"]["sync_num"] == sync
    	assert doc["info"]["lock_num"] == lock

    #print 'Server number is: *{0}*, testing against, *{1}*'.format(doc["info"]["server"], server)
