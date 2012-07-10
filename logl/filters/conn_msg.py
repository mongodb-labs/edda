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


import re
import string
import logging


def criteria(msg):
    """Determing if the given message is an instance
    of a connection type message"""
    if string.find(msg, 'connection accepted') >= 0:
        return 1
    if string.find(msg, 'end connection') >= 0:
        return 2
    return -1


def process(msg, date):
    """Turn this message into a properly formatted
    connection type document:
    doc = {
       "type" : "conn"
       "date" : datetime
       "msg"  : msg
       "info" : {
              "subtype"   : "new_conn" or "end_conn"
              "conn_addr" : "addr:port"
              "conn_num"  : int
              "server"    : "self"
              }
    }"""
    result = criteria(msg)
    if result < 0:
        return None
    doc = {}
    doc["date"] = date
    doc["type"] = "conn"
    doc["info"] = {}
    doc["msg"] = msg

    if result == 1:
        new_conn(msg, doc)
    if result == 2:
        ended(msg, doc)
    return doc


def new_conn(msg, doc):
    """this server has accepted a new connection."""
    doc["info"]["subtype"] = "new_conn"
    logger = logging.getLogger(__name__)

    # this very long regex recognizes legal IP addresses
    pattern = re.compile("""
        (([0|1]?[0-9]{1,2})|(2[0-4][0-9])|(25[0-5])) # first part
        (\.([0|1]?[0-9]{1,2})|(2[0-4][0-9])|(25[0-5])){3} # second part
    """, re.WHITESPACE)
    m = pattern.search(msg)
    if (m == None):
        logger.debug("malformed new_conn message: no IP address found")
        return None
    host = m.group(0)

    # isolate port number
    pattern = re.compile(":[0-9]{1,5}")
    n = pattern.search(msg[21:])
    if n is None:
        logger.debug("malformed new_conn message: no port number found")
        return None
    port = n.group(0)[1:]
    doc["info"]["server"] = host + ":" + port

    # isolate connection number
    pattern2 = re.compile("#[0-9]+")
    m = pattern2.search(msg)
    if m is None:
        logger.debug("malformed new_conn message: no connection number found")
        return None
    doc["info"]["conn_number"] = m.group(0)[1:]

    debug = "Returning new doc for a message of type: initandlisten: new_conn"
    logger.debug(debug)
    return doc


def ended(msg, doc):
    """this server is ending a connections."""
    doc["info"]["subtype"] = "end_conn"
    logger = logging.getLogger(__name__)

    # This very long regex recognizes legal IP addresses
    pattern = re.compile("(([0|1]?[0-9]{1,2})|(2[0-4][0-9])|(25[0-5]))(\.([0|1]?[0-9]{1,2})|(2[0-4][0-9])|(25[0-5])){3}")
    m = pattern.search(msg)
    if (m == None):
        logger.debug("malformed new_conn message: no IP address found")
        return None
    host = m.group(0)

    # isolate port number
    pattern = re.compile(":[0-9]{1,5}")
    n = pattern.search(msg[21:])
    if n is None:
        logger.debug("malformed new_conn message: no port number found")
        return None
    port = n.group(0)[1:]
    doc["info"]["server"] = host + ":" + port

    # isolate connection number
    pattern2 = re.compile("#[0-9]+")
    m = pattern2.search(msg)
    if m is None:
        logger.debug("malformed new_conn message: no connection number found")
        return None
    doc["info"]["conn_number"] = m.group(0)[1:]

    debug = "Returning new doc for a message of type: initandlisten: new_conn"
    logger.debug(debug)

    return doc
