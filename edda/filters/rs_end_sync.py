# Copyright 2016 MongoDB, Inc.
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


import logging


logs = [
    "could not find member to sync from",
    "failed to find sync source",
    "Fetcher stopped querying remote oplog",
    "Cannot select sync source which is blacklisted"
]

def criteria(msg):
    """Does the given log line fit the criteria for this filter?
    If so, return an integer code.  Otherwise, return 0.
    """
    for log in logs:
        if msg.find(log) >= 0:
            return 1
    return 0

def process(msg, date):
    """If the given log line fits the criteria for this filter,
    process the line and create a document of the following format:
    document = {
       "date" : date,
       "type" : "end_sync",
       "msg" : msg,
       "info" : {
          "server" : "self"
          }
    }
    """
    messageType = criteria(msg)
    if not messageType:
        return None
    doc = {}
    doc["date"] = date
    doc["type"] = "end_sync"
    doc["info"] = {}
    doc["msg"] = msg

    # populate info
    doc["info"]["server"] = "self"

    logger = logging.getLogger(__name__)
    logger.debug(doc)
    return doc
