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


import pymongo
import logging
from datetime import datetime
import re


def capture_address(msg):
    """Given a message, extracts and returns the address,
    be it a hostname or an IP address, in the form
    'address:port#'"""
    # capture the address, be it hostname or IP
    pattern = re.compile("\S+:[0-9]{1,5}")
    m = pattern.search(msg[20:]) # skip date field
    if not m:
        return None
    return m.group(0)


def is_IP(s):
    """Returns true if s contains an IP address, false otherwise"""
    # note: this message will return True for strings that
    # have more than 4 dotted groups of numbers (like 1.2.3.4.5)
    a = "(0|(1?[0-9]{1,2})|(2[0-4][0-9])|(25[0-5]))"
    a += "(\.(0|(1?[0-9]{1,2})|(2[0-4][0-9])|(25[0-5]))){3}"
    pattern = re.compile(a)
    m = pattern.search(s)
    if (m == None):
        return False
    return True


def get_server_num(addr, servers):
    """Gets and returns a server_num for an
    existing .servers entry with 'addr', or creates a new .servers
    entry and returns the new server_num, as a string.  If
    'addr' is 'unknown', assume this is a new server and return
    a new number"""
    logger = logging.getLogger(__name__)
    num = None
    addr = addr.replace('\n', "")
    addr = addr.replace(" ", "")

    # if addr is 'self', ignore
    if addr != "unknown":
        if is_IP(addr):
            num = servers.find_one({"server_IP": addr})
        else:
            num = servers.find_one({"server_name": addr})
        if num:
            logger.debug("Found server number {0} for address {1}".format(num["server_num"], addr))
            return str(num["server_num"])

    # no .servers entry found for this target, make a new one
    # make sure that we do not overwrite an existing server's index
    for i in range(1, 50):
        if not servers.find_one({"server_num" : str(i)}):
            logger.info("No server entry found for target server {0}".format(addr))
            logger.info("Adding {0} to the .servers collection with server_num {1}".format(addr, i))
            assign_address(str(i), addr, servers)
            return str(i)
    logger.critical("Ran out of server numbers!")


def assign_address(num, addr, servers):
    """Given this num and addr, sees if there exists a document
    in the .servers collection for that server.  If so, adds addr, if
    not already present, to the document.  If not, creates a new doc
    for this server and saves to the db."""
    # in the case that two different addresses are found for the
    # same server, this chooses to log a warning and ignore
    # all but the first address found
    # store all fields as strings, including server_num
    # server doc = {
    #    "server_num" : int, as string
    #    "server_name" : hostname
    #    "server_IP" : IP
    #    }
    logger = logging.getLogger(__name__)
    num = str(num)
    addr = str(addr)
    addr = addr.replace('\n', "")
    doc = servers.find_one({"server_num": num})
    if not doc:
        if addr != "unknown":
            doc = servers.find_one({"server_IP": addr})
            if not doc:
                doc = servers.find_one({"server_name": addr})
            if doc:
                logger.debug("Entry already exists for server {0}".format(addr))
                return
        logger.debug("No doc found for this server, making one")
        doc = {}
        doc["server_num"] = num
        doc["server_name"] = "unknown"
        doc["server_IP"] = "unknown"
    else:
        logger.debug("Fetching existing doc for server {0}".format(num))
    if is_IP(addr):
        if doc["server_IP"] != "unknown" and doc["server_IP"] != addr:
            logger.warning("conflicting IPs found for server {0}:".format(num))
            logger.warning("\n{0}\n{1}".format(repr(addr), repr(doc["server_IP"])))
        else:
            doc["server_IP"] = addr
    else:
        # NOTE: case insensitive!
        if doc["server_name"] != "unknown" and doc["server_name"].lower() != addr.lower():
            logger.warning("conflicting hostnames found for server {0}:".format(num))
            logger.warning("\n{0}\n{1}".format(repr(addr), repr(doc["server_name"])))
        else:
            doc["server_name"] = addr
    logger.debug("I am saving {0} to the .servers collection".format(doc))
    servers.save(doc)


def date_parser(message):
    """extracts the date information from the given line.  If
    line contains incomplete or no date information, skip
    and return None."""
    try:
        newMessage = str(parse_month(message[4:7])) + message[7:19]
        time = datetime.strptime(newMessage, "%m %d %H:%M:%S")
        return time
    except ValueError:
        return None
