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

# one file for methods that are called on as helper methods
# from many different modules within logl

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
    """Returns true if s is an IP address, false otherwise"""
    s = "(([0|1]?[0-9]{1,2})|(2[0-4][0-9])"
    s += "|(25[0-5]))(\.([0|1]?[0-9]{1,2})"
    s += "|(2[0-4][0-9])|(25[0-5])){3}"
    pattern = re.compile(s)
    m = pattern.search(s)
    if (m == None):
        return False
    return True


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
    #    "server_num" : int
    #    "server_name" : hostname
    #    "server_IP" : IP
    #    }
    logger = logging.getLogger(__name__)
    num = str(num)
    addr = str(addr)
    doc = servers.find_one({"server_num": num})
    if not doc:
        if addr != "unknown":
            # couldn't find with server_num, try using addr as IP
            doc = servers.find_one({"server_IP": addr})
            if not doc:
                # couldn't find with server_IP, try using addr as hostname
                doc = servers.find_one({"server_name": addr})
            if doc:
                # nothing to do, return
                logger.debug("Entry already exists for server {0}".format(addr))
                return
        logger.debug("No doc found for this server, making one")
        doc = {}
        doc["server_num"] = num
        doc["server_name"] = "unknown"
        doc["server_IP"] = "unknown"
    else:
        logger.debug("Doc already exists for server {0}".format(num))
    if addr == num:
        pass
    elif is_IP(addr):
        if doc["server_IP"] != "unknown" and doc["server_IP"] != addr:
            logger.warning("conflicting IPs found for server {0}:".format(num))
            logger.warning("\n{0}\n{1}".format(addr, doc["server_IP"]))
        else:
            doc["server_IP"] = addr
    else:
        if doc["server_name"] != "unknown" and doc["server_name"] != addr:
            logger.warning("conflicting hostnames found for server {0}:".format(num))
            logger.warning("\n{0}\n{1}".format(addr, doc["server_name"]))
        else:
            doc["server_name"] = addr
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


def parse_month(month):
    """tries to match the string to a month code, and returns
that month's integer equivalent.  If no month is found,
return 0."""
    return{
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12,
        }.get(month, 0)
