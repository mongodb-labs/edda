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


import logging


def criteria(msg):
    """Does the given log line fit the criteria for this filter?
    If so, return an integer code.  Otherwise, return 0.
    """
    if ('[rsSync]' in msg and
        'syncing' in msg):
        return 1
    return 0


def process(msg, date):

    """If the given log line fits the criteria for this filter,
    process the line and create a document of the following format:
    document = {
       "date" : date,
       "type" : "sync",
       "msg" : msg,
       "info" : {
          "sync_server" : "host:port"
          "server" : "self
          }
    }
    """
    messageType = criteria(msg)
    if not messageType:
        return None
    doc = {}
    doc["date"] = date
    doc["type"] = "sync"
    doc["info"] = {}
    doc["msg"] = msg

    #Has the member begun syncing to a different place
    if(messageType == 1):
        return syncing_diff(msg, doc)


def syncing_diff(msg, doc):
    """Generate and return a document for replica sets
    that are syncing to a new server.
    """
    start = msg.find("to: ")
    if (start < 0):
        return None
    doc["info"]["sync_server"] = msg[start + 4: len(msg)]
    doc["info"]["server"] = "self"
    logger = logging.getLogger(__name__)
    logger.debug(doc)
    return doc
