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


import re
import string
import logging

# Mon Jul  2 10:00:11 [conn2] CMD fsync: sync:1 lock:1
# Mon Jul  2 10:00:04 [conn2] command: unlock requested
# Mon Jul  2 10:00:10 [conn2] db is now locked for snapshotting, no writes
    # allowed. db.fsyncUnlock() to unlock


def criteria(msg):
    """Does the given log line fit the criteria for this filter?
    return an integer code if yes, -1 if not."""
    if string.find(msg, 'too stale to catch up') >= 0:
        return 0
    return -1


def process(msg, date):
    """if the given log line fits the criteria for this filter,
    processes the line and creates a document for it.
    document = {
       "date" : date,
       "type" : "conn",
       "info" : {
          "state_code" : messagetype
          "state" : "STALE"
          "server" : host:port
       }
       "oritinal_message" : msg
    }"""
    message_type = criteria(msg)
    if message_type < 0:
        return None

    doc = {}
    doc["date"] = date
    doc["type"] = "stale"
    doc["info"] = {}
    doc["info"]["state_code"] = message_type
    doc["original_message"] = msg

    ip = True
    if message_type == 0:
        doc["info"]["state"] = "STALE"
        logger = logging.getLogger(__name__)

        # this very long regex recognizes legal IP addresses
        pattern = re.compile("(([0|1]?[0-9]{1,2})|(2[0-4][0-9])|"
            "(25[0-5]))(\.([0|1]?[0-9]{1,2})|(2[0-4][0-9])|(25[0-5])){3}")
        m = pattern.search(msg)
        if (m == None):
            logger.debug("malformed new_conn message: no IP address found")
            ip = False
        if ip:
            host = m.group(0)

            # isolate port number
            pattern = re.compile(":[0-9]{1,5}")
            n = pattern.search(msg[21:])
            if n is None:
                deb = "malformed new_conn message: no port number found"
                logger.debug(deb)
                ip = False
            port = n.group(0)[1:]
        if ip:
            doc["info"]["server"] = host + ":" + port
        else:
            doc["info"]["server"] = None
    return doc
