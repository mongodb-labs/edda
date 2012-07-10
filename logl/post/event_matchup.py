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
import re
from datetime import timedelta


# put this somewhere else!!
def is_IP(s):
    """Returns true if s is an IP address, false otherwise"""
    pattern = re.compile("(([0|1]?[0-9]{1,2})|(2[0-4][0-9])|(25[0-5]))(\.([0|1]?[0-9]{1,2})|(2[0-4][0-9])|(25[0-5])){3}")
    m = pattern.search(s)
    if (m == None):
        return False
    return True

# put this somewhere else, too!!
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


def event_matchup(db, collName):
    """This method sorts through the db's entries to
    find discrete events that happen across servers.  It will
    organize these entries into a list of "events", which are
    each a dictionary built as follows:
    event = {
        "type"       = type of event, see list below
        "date"       = datetime, as string
        "target"     = affected server
        "witnesses"  = servers who agree on this event
        "dissenters" = servers who did not see this event
                       (not for connection or sync messages)
        "summary"    = a mnemonic summary of the event
    (event-specific additional fields:)
        "sync_to"    = for sync type messages
        "conn_addr"    = for new_conn or end_conn messages
        "conn_num"   = for new_conn or end_conn messages
        "state"      = for status type messages (label, not code)
        }

    possible event types include:
    "new_conn" : new user connections
    "end_conn" : end a user connection
    "status"   : a status change for a server
    "sync"     : a new sync pattern for a server
    "stale"    : a secondary is going stale
    "exit"     : a replica set is exiting
    "lock"     : a server requests to lock itself from writes
    "unlock"   : a server requests to unlock itself from writes
    "reconfig" : new config information was received

    This module assumes that normal network delay can account
    for up to 4 seconds of lag between server logs.  Beyond this
    margin, module assumes that servers are no longer in sync.
    """
    # put events in ordered lists by date, one per origin_server
    # last communication with the db!
    entries = organize_servers(db, collName)
    events = []

    server_coll = db[collName + ".servers"]
    server_nums = server_coll.distinct("server_num")

    # make events
    while(True):
        event = next_event(server_nums, entries, db, collName)
        if not event:
            break
        events.append(event)

    # attempt to resolve any undetected skew in events
    events = resolve_dissenters(events)
    return events


def next_event(servers, server_entries, db, collName):
    """Given lists of entries from servers ordered by date,
    and a list of server numbers, finds a new event
    and returns it.  Returns None if out of entries"""
    # NOTE: this method makes no attempt to adjust for clock skew,
    # only normal network delay.
    # find the first entry from any server
    delay = timedelta(seconds=2)
    event = {}
    event["witnesses"] = []
    event["dissenters"] = []
    logger = logging.getLogger(__name__)

    # be careful about datetimes stored as strings!

    logger.debug("looking for a good first")
    first = None
    for s in servers:
        if not server_entries[s]:
            logger.debug("No server_entries list for this server, skipping")
            continue
        if first and server_entries[s][0]["date"] > first["date"]:
            continue
        first = server_entries[s].pop(0)
    if not first:
        return None

    logger.debug("found first from server {0}".format(first["origin_server"]))

    servers_coll = db[collName + ".servers"]
    # define event fields
    if first["info"]["server"] == "self":
        event["target"] = str(first["origin_server"]) # meh
    else:
        # there is definitely a better way to write this
        # feel like we might have a better method somewhere to handle this?
        # get the server number
        num = None
        if is_IP(first["info"]["server"]):
            num = servers_coll.find_one({"server_IP": first["info"]["server"]})
        # or, if one does not exist for this server,
        else:
            num = servers_coll.find_one({"server_addr": first["info"]["server"]})
        if not num:
            # make sure that we do not overwrite an existing server
            for i in range(1, 50):
                if not servers_coll.find_one({"server_num":i}):
                    assign_address(str(i), first["info"]["server"], servers_coll)
                    num = i
                    break
        event["target"] = str(num)
    event["type"] = first["type"]
    event["date"] = first["date"]
    if event["type"] == "status":
        event["state"] = first["info"]["state"]
    event["witnesses"].append(first["origin_server"])


    # some kinds of messages won't have any corresponding messages:
    if first["type"] == "conn":
        logger.debug("handling a connection message")
        event["type"] = first["info"]["subtype"]
        event["witnesses"].append(first["origin_server"])
        event["conn_addr"] = first["info"]["conn_addr"]
        event["target"] = first["origin_server"]
        print first["info"]
        event["conn_number"] = first["info"]["conn_number"]
        event["summary"] = generate_summary(event)
        return event

    # fsync locking/unlocking messages only come from
    # a server talking about itself
    if first["type"] == "fsync":
        pass

    # sync messages, also
    if first["type"] == "sync":
        event["sync_to"] = first["info"]["sync_server"]
        pass

    # find corresponding messages
    for s in servers:
        logger.debug("checking server {0}'s entries".format(s))
        if s == first["origin_server"]:
            logger.debug("this is the same server, skipping")
            continue
        for entry in server_entries[s]:
            if abs(entry["date"] - first["date"]) > delay:
                logger.debug("entry is outside range of network delay, breaking")
                break
            target = target_server_match(entry, first, db[collName + ".servers"])
            if not target:
                logger.debug("entries' target servers do not agree, skipping")
                continue
            event["target"] = target
            if not type_check(first, entry):
                logger.debug("specific type checking failed, skipping")
                continue
            # passed all checks! must match.
            logger.debug("Found a match!  Adding to event's witnesses")
            server_entries[s].remove(entry)
            event["witnesses"].append(s)
            # organize me better please...
        if s not in event["witnesses"]:
            logger.debug("No matches found for server {0}, adding to dissenters".format(s))
            event["dissenters"].append(s)

    logger.debug("Done searching for corresponding events")
    event["summary"] = generate_summary(event)
    return event


def type_check(entry_a, entry_b):
    """Given two .entries documents, perform checks specific to
    their type to see if they refer to corresponding events"""
    # handle exit messages carefully
    if entry_a["type"] != entry_b["type"]:
        return False
    type = entry_a["type"]
    if type == "status":
        if entry_a["info"]["state_code"] != entry_b["info"]["state_code"]:
            return False
    elif type == "stale":
        pass
    return True


def target_server_match(entry_a, entry_b, servers):
    """Given two .entries documents, are they talking about the
    same sever?  Return target server if yes, None if no"""
    logger = logging.getLogger(__name__)

    a = entry_a["info"]["server"]
    b = entry_b["info"]["server"]

    if a == "self" and b == "self":
        return None
    if a == b:
        return a

    a_doc = servers.find_one({"server_num": entry_a["origin_server"]})
    b_doc = servers.find_one({"server_num": entry_b["origin_server"]})

    # address is known
    if a == "self":
        if (b == a_doc["server_name"] or
            b == a_doc["server_IP"]):
            return b
    if b == "self":
        if (a == b_doc["server_name"] or
            a == b_doc["server_IP"]):
            return a

    # address not known
    # in this case, we will assume that the address does belong
    # to the unnamed server and name it.
    if a == "self":
        if is_IP(b):
            if a_doc["server_IP"] == "unknown":
                logger.debug("Assigning IP {0} to server {1}".format(b, a))
                a_doc["server_IP"] == b
                servers.save(a_doc)
                return b
            return None
        else:
            if a_doc["server_name"] == "unknown":
                logger.debug("Assigning hostname {0} to server {1}".format(b, a))
                a_doc["server_name"] == b
                servers.save(a_doc)
                return b
            return None

    # why, yes, it is rather silly to code this here twice.
    # clean me up please!!
    if b == "self":
        if is_IP(a):
            if b_doc["server_IP"] == "unknown":
                logger.debug("Assigning IP {0} to server {1}".format(a, b))
                b_doc["server_IP"] == a
                servers.save(b_doc)
                return a
            return None
        else:
            if b_doc["server_name"] == "unknown":
                logger.debug("Assigning hostname {0} to server {1}".format(a, b))
                b_doc["server_name"] == a
                servers.save(b_doc)
                return a
            return None


def resolve_dissenters(events):
    """Goes over the list of events and for each event where
    the number of dissenters > the number of witnesses,
    attempts to match that event to another corresponding
    event outside the margin of allowable network delay"""
    # useful for cases with undetected clock skew
    events_b = events[:]
    logger = logging.getLogger(__name__)
    i = 0
    for a in events:
        logger.debug("Checking event {0}".format(i))
        if len(a["dissenters"]) >= len(a["witnesses"]):
            logger.debug("this event has more dissenters than witnesses")
            logger.debug("Attempting to find corresponding event")
            for b in events_b:
                if a["summary"] == b["summary"]:
                    logger.debug("Summary match found! Checking witnesses")
                    for wit_a in a["witnesses"]:
                        if wit_a in b["witnesses"]:
                            logger.debug("Overlapping witness found, no match")
                            break
                    # concerned about this loop breaking thing
                    # also, concerned about mutability of lists?
                    # check that removing something from b also removes it from a!
                    else:
                        logger.debug("match found, merging events")
                        logger.debug("skew is {0}".format(a["date"] - b["date"]))
                        events.remove(a)
                        # resolve witnesses and dissenters lists
                        for wit_a in a["witnesses"]:
                            b["witnesses"].append(wit_a)
                            if wit_a in b["dissenters"]:
                                logger.debug("Removing {0} from b's dissenters".format(wit_a))
                                b["dissenters"].remove(wit_a)
                        # we've already found a match, stop looking
                        break
                    logger.debug("match not found with this event")
                    continue
        i += 1
    return events


def generate_summary(event):
    """Given an event, generates and returns a one-line,
    mnemonic summary for that event"""
    summary = ""

    # for reconfig messages
    if event["type"] == "reconfig":
        return "All servers received a reconfig message"

    summary += "Server " + event["target"]

    # for status messages
    if event["type"] == "status":
        summary += " is now " + event["state"]

    # for connection messages
    if (event["type"].find("conn") >= 0):
        if event["type"] == "new_conn":
            summary += " opened connection #"
        elif event["type"] == "end_conn":
            summary += " closed connection #"
        summary += event["conn_number"] + " to user " + event["conn_addr"]

    # for exit messages
    if event["type"] == "exit":
        summary += " is now exiting"

    # for locking messages
    if event["type"] == "unlock":
        summary += " is unlocking itself"
    if event["type"] == "lock":
        summary += " is locking itself"

    # for stale messages
    if event["type"] == "stale":
        summary += " is going stale"

    # for syncing messages
    if event["type"] == "sync":
        summary += " is syncing to " + event["sync_to"]

    return summary


def organize_servers(db, collName):
    """Organizes entries from .entries collection into lists
    sorted by date, one per origin server, as follows:
    { "server1" : [doc1, doc2, doc3...]}
    { "server2" : [doc1, doc2, doc3...]} and
    returns these lists in one larger list, with the server-
    specific lists indexed by server_num"""
    servers_list = {}

    entries = db[collName + ".entries"]
    servers = db[collName + ".servers"]

    for server in servers.find():
        num = server["server_num"]
        servers_list[num] = []
        cursor = entries.find({"origin_server": num})
        cursor.sort("date")
        for doc in cursor:
            servers_list[num].append(doc)
    return servers_list
