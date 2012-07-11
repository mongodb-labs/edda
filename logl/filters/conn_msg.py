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
from supporting_methods import capture_address

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
    doc["info"] = {}
    doc["msg"] = msg
    doc["type"] = "conn"

    if result == 1:
        new_conn(msg, doc)
    if result == 2:
        ended(msg, doc)
    return doc


def new_conn(msg, doc):
    """this server has accepted a new connection."""
    doc["info"]["subtype"] = "new_conn"
    logger = logging.getLogger(__name__)

    addr = capture_address(msg)
    if not addr:
        logger.warning("No hostname or IP found for this server")
        return None
    doc["info"]["server"] = "self"
    doc["info"]["conn_addr"] = addr

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

    addr = capture_address(msg)
    if not addr:
        logger.warning("No hostname or IP found for this server")
        return None
    doc["info"]["server"] = "self"
    doc["info"]["conn_addr"] = addr

    # isolate connection number
    pattern = re.compile("\[conn[0-9]+\]")
    m = pattern.search(msg)
    if m is None:
        logger.warning("malformed new_conn message: no connection number found")
        return None
    # do a second search for the actual number
    pattern = re.compile("[0-9]+")
    n = pattern.search(m.group(0))
    doc["info"]["conn_number"] = n.group(0)

    debug = "Returning new doc for a message of type: initandlisten: new_conn"
    logger.debug(debug)

    return doc
