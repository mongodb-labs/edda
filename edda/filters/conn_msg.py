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

import logging
import re
from edda.supporting_methods import capture_address

# module-level regex
START_CONN_NUMBER = re.compile("#[0-9]+")
END_CONN_NUMBER = re.compile("\[conn[0-9]+\]")
ANY_NUMBER = re.compile("[0-9]+")


def criteria(msg):
    """Determing if the given message is an instance
    of a connection type message
    """
    if 'connection accepted' in msg:
        return 1
    if 'end connection' in msg:
        return 2
    return 0


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
    }
    """

    result = criteria(msg)
    if not result:
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
    logger = logging.getLogger(__name__)
    """Generate a document for a new connection event."""
    doc["info"]["subtype"] = "new_conn"

    addr = capture_address(msg)
    if not addr:
        logger.warning("No hostname or IP found for this server")
        return None
    doc["info"]["server"] = "self"
    doc["info"]["conn_addr"] = addr

    # isolate connection number
    m = START_CONN_NUMBER.search(msg)
    if not m:
        logger.debug("malformed new_conn message: no connection number found")
        return None
    doc["info"]["conn_number"] = m.group(0)[1:]

    debug = "Returning new doc for a message of type: initandlisten: new_conn"
    logger.debug(debug)
    return doc


def ended(msg, doc):
    logger = logging.getLogger(__name__)
    """Generate a document for an end-of-connection event."""
    doc["info"]["subtype"] = "end_conn"

    addr = capture_address(msg)
    if not addr:
        logger.warning("No hostname or IP found for this server")
        return None
    doc["info"]["server"] = "self"
    doc["info"]["conn_addr"] = addr

    # isolate connection number
    m = END_CONN_NUMBER.search(msg)
    if not m:
        logger.warning("malformed new_conn message: no connection number found")
        return None
    # do a second search for the actual number
    n = ANY_NUMBER.search(m.group(0))
    doc["info"]["conn_number"] = n.group(0)

    debug = "Returning new doc for a message of type: initandlisten: end_conn"
    logger.debug(debug)

    return doc
