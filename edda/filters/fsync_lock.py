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


def criteria(msg):
    """Does the given log line fit the criteria for this filter?
    If yes, return an integer code if yes.  Otherwise, return 0.
    """
    if 'command: unlock requested' in msg:
        return 1
    elif 'CMD fsync: sync:1 lock:1' in msg:
        return 2
    elif 'db is now locked' in msg:
        return 3
    return -1


def process(msg, date):
    """If the given log line fits the criteria
    for this filter, processes the line and creates
    a document of the following format:
    doc = {
       "date" : date,
       "type" : "fsync",
       "info" : {
          "state"  : state
          "server" : "self"
       }
       "msg" : msg
    }
    """
    message_type = criteria(msg)
    if message_type <= 0:
        return None

    doc = {}
    doc["date"] = date
    doc["type"] = "fsync"
    doc["info"] = {}
    doc["original_message"] = msg

    if message_type == 1:
        doc["info"]["state"] = "UNLOCKED"
    elif message_type == 2:
        doc["info"]["state"] = "FSYNC"
    else:
        doc["info"]["state"] = "LOCKED"

    doc["info"]["server"] = "self"
    return doc
