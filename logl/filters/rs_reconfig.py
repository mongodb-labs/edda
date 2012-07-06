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


# Example messages:

# Tue Jul  3 10:20:15 [rsMgr] replset msgReceivedNewConfig version: version: 4
# Tue Jul  3 10:20:15 [rsMgr] replSet info saving a newer config version to loc
    # al.system.replset
# Tue Jul  3 10:20:15 [rsMgr] replSet saveConfigLocally done
# Tue Jul  3 10:20:15 [rsMgr] replSet info : additive change to configuration
# Tue Jul  3 10:20:15 [rsMgr] replSet replSetReconfig new config saved locally


import string


def criteria(msg):

    """Does the given log line fit the criteria for this filter?
    return an integer code if yes, -1 if not."""
    if string.find(msg, 'replSetReconfig') >= 0:
        return 0
    return -1


def process(msg, date):
    """if the given log line fits the criteria for this filter,
    processes the line and creates a document for it.
    document = {
       "date" : date,
       "type" : "reconfig",
       "info" : {
          "state_code" : messagetype
       }
       "oritinal_message" : msg
    }"""
    message_type = criteria(msg)
    if message_type < 0:
        return None

    doc = {}
    doc["date"] = date
    doc["type"] = "re_sync"
    doc["info"] = {}
    doc["original_message"] = msg

    return doc
