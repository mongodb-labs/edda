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

# This module tracks requests from the server to lock or unlock its self from
    # writes.

import string

# Mon Jul  2 10:00:11 [conn2] CMD fsync: sync:1 lock:1
# Mon Jul  2 10:00:04 [conn2] command: unlock requested
# Mon Jul  2 10:00:10 [conn2] db is now locked for snapshotting, no writes allo
    # wed. db.fsyncUnlock() to unlock

def criteria(msg):
    """Does the given log line fit the criteria for this filter?
    return an integer code if yes, -1 if not."""
    if (string.find(msg, 'db is now locked') >= 0):
        return 0
    elif (string.find(msg, 'command: unlock requested') >= 0):
        return 1
    elif (string.find(msg, 'CMD fsync: sync:1 lock:1') >= 0):
        return 2
    return -1


def process(msg, date):
    """if the given log line fits the criteria for this filter,
    processes the line and creates a document for it.
    document = {
       "date" : date,
       "type" : "fsync",
       "info" : {
          "state"  : state
          "server" : "self"
       }
       "oritinal_message" : msg
    }"""
    message_type = criteria(msg)
    if message_type < 0:
        return None

    doc = {}
    doc["date"] = date
    doc["type"] = "fsync"
    doc["info"] = {}
    doc["original_message"] = msg

    if message_type == 0:
        doc["info"]["state"] = "LOCKED"
    elif message_type == 1:
        doc["info"]["state"] = "UNLOCKED"
    else:
        doc["info"]["state"] = "FSYNC"
    doc["info"]["server"] = "self"
    return doc
