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

#!/usr/bin/env python


def criteria(msg):
    """Does the given log line fit the criteria for this filter?
    If yes, return an integer code.  If not, return 0.
    """
    if 'dbexit: really exiting now' in msg:
        return 1
    return 0


def process(msg, date):
    """if the given log line fits the criteria for this filter,
    processes the line and creates a document for it.
    document = {
       "date" : date,
       "type" : "exit",
       "info" : {
          "server": "self"
       }
       "msg" : msg
    }
    """

    messagetype = criteria(msg)
    if not messagetype:
        return None

    doc = {}
    doc["date"] = date
    doc["type"] = "exit"
    doc["info"] = {}
    doc["msg"] = msg
    doc["info"]["server"] = "self"
    return doc
