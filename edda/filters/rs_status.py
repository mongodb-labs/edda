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

from edda.supporting_methods import capture_address


def criteria(msg):
    """Does the given log line fit the criteria for this filter?
    If yes, return an integer code.  Otherwise, return -1.
    """
    # state STARTUP1
    if '[rsStart] replSet I am' in msg:
        return 0
    # state PRIMARY
    if 'PRIMARY' in msg:
        return 1
    # state SECONDARY
    if 'SECONDARY' in msg:
        return 2
    # state RECOVERING
    if 'RECOVERING' in msg:
        return 3
    # state FATAL ERROR
    if 'FATAL' in msg:
        return 4
    # state STARTUP2
    if 'STARTUP2' in msg:
        return 5
    # state UNKNOWN
    if 'UNKNOWN' in msg:
        return 6
    # state ARBITER
    if 'ARBITER' in msg:
        return 7
    # state DOWN
    if 'DOWN' in msg:
        return 8
    # state ROLLBACK
    if 'ROLLBACK' in msg:
        return 9
    # state REMOVED
    if 'REMOVED' in msg:
        return 10


def process(msg, date):

    """If the given log line fits the critera for this filter,
    process it and create a document of the following format:
    doc = {
       "date" : date,
       "type" : "status",
       "msg" : msg,
       "origin_server" : name,
       "info" : {
          "state" : state,
          "state_code" : int,
          "server" : "host:port",
          }
    }
    """
    result = criteria(msg)
    if result < 0:
        return None
    labels = ["STARTUP1", "PRIMARY", "SECONDARY",
              "RECOVERING", "FATAL", "STARTUP2",
              "UNKNOWN", "ARBITER", "DOWN", "ROLLBACK",
              "REMOVED"]
    doc = {}
    doc["date"] = date
    doc["type"] = "status"
    doc["info"] = {}
    doc["msg"] = msg
    doc["info"]["state_code"] = result
    doc["info"]["state"] = labels[result]

    # if this is a startup message, and includes server address, do something special!!!
    # add an extra field to capture the IP
    n = capture_address(msg[20:])
    if n:
        if result == 0:
            doc["info"]["server"] = "self"
            doc["info"]["addr"] = n
        else:
            doc["info"]["server"] = n
    else:
        # if no server found, assume self is target
        doc["info"]["server"] = "self"
    return doc
