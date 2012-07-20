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
import pymongo
import re

from datetime import timedelta
from operator import itemgetter
from supporting_methods import *

LOGGER = logging.getLogger(__name__)

def event_matchup(db, coll_name):
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
    entries = organize_servers(db, coll_name)
    events = []

    server_coll = db[coll_name + ".servers"]
    server_nums = server_coll.distinct("server_num")

    # make events
    while(True):
        event = next_event(server_nums, entries, db, coll_name)
        if not event:
            break
        events.append(event)

    # attempt to resolve any undetected skew in events
    events = resolve_dissenters(events)
    return events


def next_event(servers, server_entries, db, coll_name):
    """Given lists of entries from servers ordered by date,
    and a list of server numbers, finds a new event
    and returns it.  Returns None if out of entries"""
    # NOTE: this method makes no attempt to adjust for clock skew,
    # only normal network delay.
    # find the first entry from any server

    # these are messages that do not involve
    # corresponding messages across servers
    loners = ["conn", "fsync", "sync", "stale"]

    first_server = None
    for s in servers:
        if not server_entries[s]:
            continue
        if (first_server and
            server_entries[s][0]["date"] > server_entries[first_server][0]["date"]):
            continue
        first_server = s
    if not first_server:
        LOGGER.debug("No more entries in queue, returning")
        return None

    first = server_entries[first_server].pop(0)

    servers_coll = db[coll_name + ".servers"]
    event = {}
    event["witnesses"] = []
    event["dissenters"] = []

    # get and use server number for the target
    if first["info"]["server"] == "self":
        event["target"] = str(first["origin_server"])
    else:
        event["target"] = get_server_num(first["info"]["server"],
                                         servers_coll)
    # define other event fields
    event["type"] = first["type"]
    event["date"] = first["date"]

    LOGGER.debug("Handling event of type {0} with"
                 "target {1}".format(event["type"], event["target"]))

    # some messages need specific fields set:
    # status events
    if event["type"] == "status":
        event["state"] = first["info"]["state"]

    # exit messages
    if event["type"] == "exit":
        event["state"] = "DOWN"

    # locking messages
    if event["type"] == "fsync":
        event["type"] = first["info"]["state"]

    # sync events
    if event["type"] == "sync":
        # must have a server number for this server
        num = get_server_num(first["info"]["sync_server"], servers_coll)
        event["sync_to"] = num

    # conn messages
    if first["type"] == "conn":
        event["type"] = first["info"]["subtype"]
        event["conn_addr"] = first["info"]["conn_addr"]
        event["conn_number"] = first["info"]["conn_number"]

    # get a hostname
    label = ""
    num, name, IP = name_me(event["target"], servers_coll)
    if name:
        label = name
    elif IP:
        label = IP
    else:
        label = event["target"]

    event["summary"] = generate_summary(event, label)

    # handle corresponding messages
    event["witnesses"].append(first["origin_server"])
    if not first["type"] in loners:
        event = get_corresponding_events(servers, server_entries,
                                         event, first, servers_coll)
    return event


def get_corresponding_events(servers, server_entries,
                             event, first, servers_coll):
    """Given a list of server names and entries
    organized by server, find all events that correspond to
    this one and combine them"""
    delay = timedelta(seconds=2)

    # find corresponding messages
    for s in servers:
        add = False
        add_entry = None
        if s == first["origin_server"]:
            continue
        for entry in server_entries[s]:
            if abs(entry["date"] - event["date"]) > delay:
                break
            if not target_server_match(entry, first, servers_coll):
                continue
            type = type_check(first, entry)
            if not type:
                continue
            # match found!
            event["type"] = type
            add = True
            add_entry = entry
        if add:
            server_entries[s].remove(add_entry)
            event["witnesses"].append(s)
        if not add:
            LOGGER.debug("No matches found for server {0}, adding to dissenters".format(s))
            event["dissenters"].append(s)
    return event


def type_check(entry_a, entry_b):
    """Given two .entries documents, perform checks specific to
    their type to see if they refer to corresponding events"""

    if entry_a["type"] == entry_b["type"]:
        return entry_a["type"]

    # handle exit messages carefully
    # if exit and down messages, save as "exit" type
    if entry_a["type"] == "exit" and entry_b["type"] == "status":
        if entry_b["info"]["state"] == "DOWN":
            return "exit"
    elif entry_b["type"] == "exit" and entry_a["type"] == "status":
        if entry_a["info"]["state"] == "DOWN":
            return "exit"
    return None


def target_server_match(entry_a, entry_b, servers):
    """Given two .entries documents, are they talking about the
    same sever?  (these should never be from the same
    origin_server) Return True or False"""

    a = entry_a["info"]["server"]
    b = entry_b["info"]["server"]

    if a == "self" and b == "self":
        return False
    if a == b:
        return True
    a_doc = servers.find_one({"server_num": entry_a["origin_server"]})
    b_doc = servers.find_one({"server_num": entry_b["origin_server"]})

    # address is known
    if a == "self":
        if (b == a_doc["server_name"] or
            b == a_doc["server_IP"]):
            return True
    if b == "self":
        if (a == b_doc["server_name"] or
            a == b_doc["server_IP"]):
            return True

    # address not known
    # in this case, we will assume that the address does belong
    # to the unnamed server and name it.
    if a == "self":
        if is_IP(b):
            if a_doc["server_IP"] == "unknown":
                LOGGER.info("Assigning IP {0} to server {1}".format(b, a))
                a_doc["server_IP"] == b
                servers.save(a_doc)
                return True
            return False
        else:
            if a_doc["server_name"] == "unknown":
                LOGGER.info("Assigning hostname {0} to server {1}".format(b, a))
                a_doc["server_name"] == b
                servers.save(a_doc)
                return True
            return False

    # why, yes, it is rather silly to code this here twice.
    # clean me up please!!
    if b == "self":
        if is_IP(a):
            if b_doc["server_IP"] == "unknown":
                LOGGER.info("Assigning IP {0} to server {1}".format(a, b))
                b_doc["server_IP"] == a
                servers.save(b_doc)
                return True
            return False
        else:
            if b_doc["server_name"] == "unknown":
                LOGGER.info("Assigning hostname {0} to server {1}".format(a, b))
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
    LOGGER.info("------------------"
                "Attempting to resolve dissenters"
                "--------------------")
    for a in events[:]:
        if len(a["dissenters"]) >= len(a["witnesses"]):
            events_b = events[:]
            for b in events_b:
                if a["summary"] == b["summary"]:
                    for wit_a in a["witnesses"]:
                        if wit_a in b["witnesses"]:
                            break
                    else:
                        LOGGER.debug("Corresponding, "
                                     "clock-skewed events found, merging events")
                        LOGGER.debug("skew is {0}".format(a["date"] - b["date"]))
                        events.remove(a)
                        # resolve witnesses and dissenters lists
                        for wit_a in a["witnesses"]:
                            b["witnesses"].append(wit_a)
                            if wit_a in b["dissenters"]:
                                b["dissenters"].remove(wit_a)
                        # we've already found a match, stop looking
                        break
                    LOGGER.debug("Match not found for this event")
                    continue
    return events


def generate_summary(event, hostname):
    """Given an event, generates and returns a one-line,
    mnemonic summary for that event
    """
    # for reconfig messages
    if event["type"] == "reconfig":
        return "All servers received a reconfig message"

    summary = hostname

    # for status messages
    if event["type"] == "status":
        summary += " is now " + event["state"]
        #if event["state"] == "ARBITER":

    # for connection messages
    elif (event["type"].find("conn") >= 0):
        if event["type"] == "new_conn":
            summary += " opened connection #"
        elif event["type"] == "end_conn":
            summary += " closed connection #"
        summary += event["conn_number"] + " to user " + event["conn_addr"]

    # for exit messages
    elif event["type"] == "exit":
        summary += " is now exiting"

    # for locking messages
    elif event["type"] == "UNLOCKED":
        summary += " is unlocking itself"
    elif event["type"] == "LOCKED":
        summary += " is locking itself"
    elif event["type"] == "FSYNC":
        summary += " is in FSYNC"

    # for stale messages
    elif event["type"] == "stale":
        summary += " is going stale"

    # for syncing messages
    elif event["type"] == "sync":
        summary += " is syncing to " + event["sync_to"]

    # for any uncaught messages
    else:
        summary += " is reporting status " + event["type"]

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
        servers_list[num] = sorted(list(entries.find({"origin_server": num})), key=itemgetter("date"))

    return servers_list
