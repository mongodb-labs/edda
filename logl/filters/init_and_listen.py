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
"""This filter processes INITANDLISTEN log lines."""

import re
import string
import logging


def criteria(msg):
    """does the given log line fit the criteria for this filter?
    return an integer code if yes, -1 if no."""
    if (string.find(msg, '[initandlisten] MongoDB starting') >= 0):
        return 1
    return -1


def process(msg, date):
    """If the given log line fits the criteria for this filter,
    processes the line and creates a document for it.
    document = {
       "date" : date,
       "type" : "init",
       "msg" : msg,
       "origin_server" : name --> this field is added in the main file
       "info" field structure varies with subtype:
       (startup) "info" : {
          "subtype" : "startup"
          "server" : "hostaddr:port"
       }
       (new_conn) "info" : {
          "subtype" : "new_conn",
          "server" : "hostaddr:port",
          "conn_number" : int,
       }
    }"""
    result = criteria(msg)
    if result < 0:
        return None
    doc = {}
    doc["date"] = date
    doc["type"] = "init"
    doc["info"] = {}
    doc["msg"] = msg

    # is it this server starting up?
    if result == 1:
        return starting_up(msg, doc)


def starting_up(msg, doc):
    """this server is starting up.  Capture host information."""
    logger = logging.getLogger(__name__)
    doc["info"]["subtype"] = "startup"

    # isolate port number
    pattern = re.compile("port=[0-9]{1,5}")
    m = pattern.search(msg)
    if m is None:
        logger.debug("malformed starting_up message: no port number found")
        return None
    port = m.group(0)[5:]

    # isolate host address
    start = string.find(msg, 'host=')
    host = msg[start + 5:len(msg)]

    doc["info"]["server"] = "self"
    addr = host + ":" + port
    addr = addr.replace('\n', "")
    addr = addr.replace(" ", "")
    doc["info"]["addr"] = addr
    deb = "Returning new doc for a message of type: initandlisten: starting_up"
    logger.debug(deb)
    return doc
