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
import re

# global regex
PORT_NUMBER = re.compile("port=[0-9]{1,5}")
# global logger
LOGGER = logging.getLogger(__name__)


def criteria(msg):
    """ Does the given log line fit the criteria for this filter?
        If yes, return an integer code.  If not, return 0.
    """
    if '[initandlisten] MongoDB starting' in msg:
        return 1
    if 'db version' in msg:
        return 2
    return 0


def process(msg, date):
    """If the given log line fits the criteria for
    this filter, processes the line and creates
    a document of the following format:
    doc = {
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
    }Wed Jul 18 14:48:19 [initandlisten] db version
    """

    result = criteria(msg)
    if not result:
        return None
    doc = {}
    doc["info"] = {}


    # is it this server starting up?
    if result == 1:
        doc["date"] = date
        doc["type"] = "init"
        doc["msg"] = msg
        return starting_up(msg, doc)
    if result == 2:
        doc["type"] = "version"
        start = msg.find("**")
        doc["version"] = msg[47:53]
        doc["date"] = date
        doc["info"]["server"] = "self"
        return doc


def starting_up(msg, doc):
    """Generate a document for a server startup event."""
    doc["info"]["subtype"] = "startup"

    # isolate port number
    m = PORT_NUMBER.search(msg)
    if m is None:
        LOGGER.debug("malformed starting_up message: no port number found")
        return None
    port = m.group(0)[5:]

    # isolate host address
    start = msg.find('host=')
    host = msg[start + 5:len(msg)]

    doc["info"]["server"] = "self"
    addr = host + ":" + port
    addr = addr.replace('\n', "")
    addr = addr.replace(" ", "")
    doc["info"]["addr"] = addr
    deb = "Returning new doc for a message of type: initandlisten: starting_up"
    LOGGER.debug(deb)
    return doc
