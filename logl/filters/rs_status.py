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
"""This filter processes RS STATUS CHANGE types of log lines."""

import string
import re


def criteria(msg):
    """does the given log line fit the criteria for this filter?
    return an integer code if yes, -1 if no"""
    # state STARTUP1
    if (string.find(msg, '[rsStart] replSet I am') >= 0):
        return 0
    # state PRIMARY
    if (string.find(msg, 'PRIMARY') >= 0):
        return 1
    # state SECONDARY
    if (string.find(msg, 'SECONDARY') >= 0):
        return 2
    # state RECOVERING
    if (string.find(msg, 'RECOVERING') >= 0):
        return 3
    # state FATAL ERROR
    if (string.find(msg, 'FATAL') >= 0):
        return 4
    # state STARTUP2
    if (string.find(msg, 'STARTUP2') >= 0):
        return 5
    # state UNKNOWN
    if (string.find(msg, 'UNKNOWN') >= 0):
        return 6
    # state ARBITER
    if (string.find(msg, 'ARBITER') >= 0):
        return 7
    # state DOWN
    if (string.find(msg, 'DOWN') >= 0):
        return 8
    # state ROLLBACK
    if (string.find(msg, 'ROLLBACK') >= 0):
        return 9
    # state REMOVED
    if (string.find(msg, 'REMOVED') >= 0):
        return 10


def process(msg, date):
    """if the given log line fits the critera for this filter,
    processes the line and creates a document for it.
    document = {
       "date" : date,
       "type" : "status",
       "msg" : msg,
       "origin_server" : name,
       "info" : {
          "subtype" : None,
          "state" : state,
          "state_code" : int,
          "server" : "host:port",
          }
    }"""
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
    pattern = re.compile("\S+:[0-9]{1,5}")
    n = pattern.search(msg[20:])
    if n:
        if result == 0:
            doc["info"]["server"] = "self"
            doc["info"]["addr"] = n.group(0)
        else:
            doc["info"]["server"] = n.group(0)
    else:
        # if no server found, assume self is target
        doc["info"]["server"] = "self"
    return doc
