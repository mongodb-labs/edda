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
        "conn_IP"    = for new_conn or end_conn messages
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

    server_nums = db[collName + ".servers"].distinct({"server_num"})

    # make events
    while(True):
        event = next_event(server_nums, entries)
        if not event:
            break
        events.append(event)

    # attempt to resolve any undetected skew in events
    events = resolve_dissenters(events)
    return events


def next_event(servers, server_entries):
    """Given lists of entries from servers ordered by date,
    separates out a new entry and returns it.  Returns None
    if out of entries"""
    # NOTE: this method makes no attempt to adjust for clock skew,
    # only normal network delay.
    # find the first entry from any server
    delay = timedelta(seconds=2)

    # be careful about datetimes stored as strings!

    first = None
    for s in servers:
        if not server_entries[s]:
            continue
        if first and server_entries[s].pop(0)["date"] > first:
            continue
        first = server_entries[s].pop(0)

    # some kinds of messages won't have any corresponding messages:
    # like user connections
    # redundant code... rewrite me please!!
    if first["type"] == "conn":
        event["type"] = first["info"]["subtype"]
        event["date"] = first["date"]
        event["dissenters"] = []
        event["witnesses"] = first["origin_server"]
        event["conn_IP"] = first["info"]["server"]
        event["conn_number"] = first["info"]["conn_number"]
        event["summary"] = generate_summary(event)
        return event

    matches = []
    for s in servers:
        if s == first["origin_server"]:
            continue
        for entry in server_entries[s]:
            # if we are outside of network margin, break
            if entry["date"] - first["date"] > delay:
                break
            if entry["type"] != first["type"]:
                continue
            if not target_server_match(entry, first, db[collName + ".servers"]):
                continue
    event = {}
    event["summary"] = generate_summary(event)
    return event


def target_server_match(entry_a, entry_b, servers):
    """Given two .entries documents, are they talking about the
    same sever?"""
    logger = logging.getLogger(__name__)

    a = entry_a["info"]["server"]
    b = entry_b["info"]["server"]

    if a == "self" and b == "self":
        return False
    if a == b:
        return True

    a_doc = servers.find_one({"server_num": entry_a["origin_server"]})
    b_doc = servers.find_one({"server_num": entry_b["origin_server"]})

    # one says "self", other uses address, address is known
    if a == "self":
        if (b == a_doc["server_name"] or
            b == a_doc["server_IP"]):
            return True
    if b == "self":
        if (a == b_doc["server_name"] or
            a == b_doc["server_IP"]):
            return True

    # one says "self", other uses address, address not known
    # in this case, we will assume that the address does belong
    # to the unnamed server and name it.
    if a == "self":
        if is_IP(b):
            if a_doc["server_IP"] == "unknown":
                logger.debug("Assigning IP {0} to server {1}".format(b, a))
                a_doc["server_IP"] == b
                servers.save(a_doc)
                return True
            return False
        else:
            if a_doc["server_name"] == "unknown":
                logger.debug("Assigning hostname {0} to server {1}".format(b, a))
                a_doc["server_name"] == b
                servers.save(a_doc)
                return True
            return False

    # why, yes, it is rather silly to code this here twice.
    # clean me up please!!
    if b == "self":
        if is_IP(a):
            if b_doc["server_IP"] == "unknown":
                logger.debug("Assigning IP {0} to server {1}".format(a, b))
                b_doc["server_IP"] == a
                servers.save(b_doc)
                return True
            return False
        else:
            if b_doc["server_name"] == "unknown":
                logger.debug("Assigning hostname {0} to server {1}".format(a, b))
                b_doc["server_name"] == a
                servers.save(b_doc)
                return True
            return False


def resolve_dissenters(events):
    """Goes over the list of events and for each event where
    the number of dissenters > the number of witnesses,
    attempts to match that event to another corresponding
    event outside the margin of allowable network delay"""
    # useful for cases with undetected clock skew
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
        else if event["type"] == "end_conn":
            summary += " closed connection #"
        summary += event["conn_number"] + " to user " + event["conn_IP"]

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
        summary += " is syncing to " += event["sync_to"]

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
