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

from datetime import datetime

# global variables
ADDRESS = re.compile("\S+:[0-9]{1,5}")
IP_PATTERN = re.compile("(0|(1?[0-9]{1,2})|(2[0-4][0-9])"
                        "|(25[0-5]))(\.(0|(1?[0-9]{1,2})"
                        "|(2[0-4][0-9])|(25[0-5]))){3}")
MONTH_DICT = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
    'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
    'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
DAY_DICT = {
    'Mon': 1, 'Tue': 2, 'Wed': 3, 'Thu': 4, 'Fri': 5, "Sat": 6, 'Sun': 7
}


def capture_address(msg):
    """Given a message, extracts and returns the address,
    be it a hostname or an IP address, in the form
    'address:port#'
    """
    # capture the address, be it hostname or IP
    m = ADDRESS.search(msg[20:])  # skip date field
    if not m:
        return None
    return m.group(0)


def is_IP(s):
    """Returns true if s contains an IP address, false otherwise.
    """
    # note: this message will return True for strings that
    # have more than 4 dotted groups of numbers (like 1.2.3.4.5)
    return not (IP_PATTERN.search(s) == None)


def get_server_num(addr, self_name, servers):
    """Gets and returns a server_num for an
    existing .servers entry with 'addr', or creates a new .servers
    entry and returns the new server_num, as a string.  If
    'addr' is 'unknown', assume this is a new server and return
    a new number.
    """
    logger = logging.getLogger(__name__)
    num = None
    addr = addr.replace('\n', "")
    addr = addr.replace(" ", "")

    if addr != "unknown":
        if self_name:
            num = servers.find_one({"self_name": addr})
        if not num:
            num = servers.find_one({"network_name": addr})
        if num:
            logger.debug("Found server number {0} for address {1}"
                         .format(num["server_num"], addr))
            return str(num["server_num"])

    # no .servers entry found for this target, make a new one
    # make sure that we do not overwrite an existing server's index
    for i in range(1, 50):
        if not servers.find_one({"server_num": str(i)}):
            logger.info("No server entry found for target server {0}".format(addr))
            logger.info("Adding {0} to the .servers collection with server_num {1}"
                        .format(addr, i))
            assign_address(str(i), addr, self_name, servers)
            return str(i)
    logger.critical("Ran out of server numbers!")


def update_mongo_version(version, server_num, servers):
    doc = []
    doc = servers.find_one({"server_num": server_num})
    if doc["version"] != version or doc["version"] == "unknown":
        doc["version"] = version
    servers.save(doc)


def name_me(s, servers):
    """Given a string s (which can be a server_num,
    server_name, or server_IP), method returns all info known
    about the server in a tuple [server_num, self_name, network_name]
    """
    s = str(s)
    s = s.replace('\n', "")
    s = s.replace(" ", "")
    self_name = None
    network_name = None
    num = None
    docs = []
    docs.append(servers.find_one({"server_num": s}))
    docs.append(servers.find_one({"self_name": s}))
    docs.append(servers.find_one({"network_name": s}))
    for doc in docs:
        if not doc:
            continue
        if doc["self_name"] != "unknown":
            self_name = doc["self_name"]
        if doc["network_name"] != "unknown":
            network_name = doc["network_name"]
        num = doc["server_num"]
    return [num, self_name, network_name]


def assign_address(num, addr, self_name, servers):
    """Given this num and addr, sees if there exists a document
    in the .servers collection for that server.  If so, adds addr, if
    not already present, to the document.  If not, creates a new doc
    for this server and saves to the db.  'self_name' is either True
    or False, and indicates whether addr is a self_name or a
    network_name.
    """
    # in the case that two different addresses are found for the
    # same server, this chooses to log a warning and ignore
    # all but the first address found
    # store all fields as strings, including server_num
    # server doc = {
    #    "server_num" : int, as string
    #    "self_name" : what I call myself
    #    "network_name" : the name other servers use for me
    #    }
    logger = logging.getLogger(__name__)

    # if "self" is the address, ignore
    if addr == "self":
        return

    num = str(num)
    addr = str(addr)
    addr = addr.replace('\n', "")
    doc = servers.find_one({"server_num": num})
    if not doc:
        if addr != "unknown":
            if self_name:
                doc = servers.find_one({"self_name": addr})
            if not doc:
                doc = servers.find_one({"network_name": addr})
            if doc:
                logger.debug("Entry already exists for server {0}".format(addr))
                return
        logger.debug("No doc found for this server, making one")
        doc = {}
        doc["server_num"] = num
        doc["self_name"] = "unknown"
        doc["network_name"] = "unknown"
        doc["version"] = "unknown"
    else:
        logger.debug("Fetching existing doc for server {0}".format(num))
    # NOTE: case insensitive!
    if self_name:
        if (doc["self_name"] != "unknown" and
            doc["self_name"].lower() != addr.lower()):
            logger.warning("conflicting self_names found for server {0}:".format(num))
            logger.warning("\n{0}\n{1}".format(repr(addr), repr(doc["self_name"])))
        else:
            doc["self_name"] = addr
    else:
        if (doc["network_name"] != "unknown" and
            doc["network_name"].lower() != addr.lower()):
            logger.warning("conflicting network names found for server {0}:".format(num))
            logger.warning("\n{0}\n{1}".format(repr(addr), repr(doc["network_name"])))
        else:
            doc["network_name"] = addr
    logger.debug("I am saving {0} to the .servers collection".format(doc))
    servers.save(doc)


def date_parser(message):
    """extracts the date information from the given line.  If
    line contains incomplete or no date information, skip
    and return None."""
    try:
        newMessage = str(MONTH_DICT[message[4:7]]) + message[7:19]
        return make_datetime_obj(message)
        return datetime.strptime(newMessage, "%m %d %H:%M:%S") 
    except (KeyError, ValueError):
        return None


def make_datetime_obj(message):
    date = datetime(2012, MONTH_DICT[message[4:7]], DAY_DICT[message[0:3]],
        int(message[11:13]), int(message[14:16]), int(message[17:19]))

    return date
