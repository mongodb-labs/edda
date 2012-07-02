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

# This module tracks requests from the server to lock or unlock its self from writes. 


def criteria(msg):
    """Does the given log line fit the criteria for this filter?
    return an integer code if yes, -1 if not."""
    if string.find(msg, 'conn2') >= 0:
        if (string.find(msg, 'locked') >= 0):
            return 0
        elif (string.find(msg, 'unlock') >= 0):
            return 1
    return -1


def process(msg, date):
    message_type = criteria
    if message_type < 0:
        return None

    doc = {}
    doc["date"] = date
    doc["type"] = "conn2"
    doc["info"] = {}
    doc["info"]["subtype"] = message_type
    if message_type == 0:
        doc["info"]["state"] = "LOCKED"
    else:
        doc["info"]["state"] = "UNLOCKED"
    doc["original_message"] = msg
