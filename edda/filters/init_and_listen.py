# Copyright 2014 MongoDB, Inc.
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

PORT_NUMBER = re.compile("port=[0-9]{1,5}")
LOGGER = logging.getLogger(__name__)

def criteria(msg):
    """ Does the given log line fit the criteria for this filter?
        If yes, return an integer code.  If not, return 0.
    """
    if ('[initandlisten] MongoDB starting' in msg or
        '[mongosMain] MongoS' in msg or
        '[mongosMain] mongos' in msg):
        return 1
    if 'db version' in msg:
        return 2
    if 'options:' in msg:
        return 3
    if 'build info:' in msg:
        return 4
    return 0

def process(msg, date):
    """If the given log line fits the criteria for
    this filter, processes the line and creates
    a document of the following format:

    "init" type documents:
    doc = {
       "date" : date,
       "type" : "init",
       "msg" : msg,
       "origin_server" : name --> this field is added in the main file
       "info" field structure varies with subtype:
       (startup) "info" : {
          "subtype" : "startup",
          "addr" : "hostaddr:port",
          "type" : mongos, mongod, config
       }
       (new_conn) "info" : {
          "subtype" : "new_conn",
          "server" : "hostaddr:port",
          "conn_number" : int,
       }
    }

    "version" type documents:
    doc = {
       "date" : date,
       "type" : "version",
       "msg" : msg,
       "version" : version number,
       "info" : {
          "server" : "self"
       }
    }

    "startup_options" documents:
    doc = {
       "date" : date,
       "type" : "startup_options",
       "msg" : msg,
       "info" : {
          "replSet" : replica set name (if there is one),
          "options" : all options, as a string
       }
    }

    "build_info" documents:
    doc = {
       "date" : date,
       "type" : "build_info",
       "msg" : msg,
       "info" : {
          "build_info" : string
       }
    }
    """

    result = criteria(msg)
    if not result:
        return None
    doc = {}
    doc["date"] = date
    doc["info"] = {}
    doc["info"]["server"] = "self"

    # initial startup message
    if result == 1:
        doc["type"] = "init"
        doc["msg"] = msg
        return starting_up(msg, doc)

    # db version
    if result == 2:
        doc["type"] = "version"
        m = msg.find("db version v")
        # ick, but supports older-style log messages
        doc["version"] = msg[m + 12:].split()[0].split(',')[0]
        return doc

    # startup options
    if result == 3:
        doc["type"] = "startup_options"
        m = msg.find("replSet:")
        if m > -1:
            doc["info"]["replSet"] = msg[m:].split("\"")[1]
        doc["info"]["options"] = msg[msg.find("options:") + 9:]
        return doc

    # build info
    if result == 4:
        doc["type"] = "build_info"
        m = msg.find("build info:")
        doc["info"]["build_info"] = msg[m + 12:]
        return doc

def starting_up(msg, doc):
    """Generate a document for a server startup event."""
    doc["info"]["subtype"] = "startup"

    # what type of server is this?
    if ('MongoS' in msg) or ('mongos' in msg):
        doc["info"]["type"] = "mongos"
        # mongos startup does not provide an address
        doc["info"]["addr"] = "unknown"
        LOGGER.debug("Returning mongos startup doc")
        return doc
    elif msg.find("MongoDB") > -1:
        doc["info"]["type"] = "mongod"

    # isolate port number
    m = PORT_NUMBER.search(msg)
    if m is None:
        LOGGER.debug("malformed starting_up message: no port number found")
        return None

    port = m.group(0)[5:]
    host = msg[msg.find("host=") + 5:].split()[0]

    addr = host + ":" + port
    addr = addr.replace('\n', "")
    addr = addr.replace(" ", "")
    doc["info"]["addr"] = addr
    deb = "Returning new doc for a message of type: initandlisten: starting_up"
    LOGGER.debug(deb)
    return doc
