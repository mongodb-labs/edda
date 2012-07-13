# Copyright 2009-2012 10gen, Inc.
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
from operator import itemgetter
from datetime import datetime
from copy import deepcopy
import pymongo
import logging
import string

# The documents this module
# generates will include the following information:

# date : (string)
# summary : (string)
# witnesses : (list of server_nums)
# dissenters : (list of server_nums)
# flag : (something conflicted about this view of the world? boolean)
# servers: {
       # server : (state as string)...
# }
# links: {
       # server : [ list of servers ]
# }
# broken_links: {
       # server : [ list of servers ]
# }
# syncs: {
       # server : [ list of servers ]
# }
# users: {
       # server : [ list of users ]
# }


def generate_frames(unsorted_events, db, collName):
    """Given a list of events, generates and returns a list of frames
    to be passed to JavaScript client to be animated"""
    # for now, program will assume that all servers
    # view the world in the same way.  If it detects something
    # amiss between two or more servers, it will set the 'flag'
    # to true, but will do nothing further.
    logger = logging.getLogger(__name__)

    frames = {}
    last_frame = None
    i = 0

    # sort events by date
    events = sorted(unsorted_events, key=itemgetter("date"))

    # get all servers
    servers = list(db[collName + ".servers"].distinct("server_num"))

    for e in events:
        f = new_frame(servers)
        # fill in various fields
        f["date"] = str(e["date"])
        f["summary"] = e["summary"]
        # see what data we can glean from the last frame
        if last_frame:
            f["servers"] = deepcopy(last_frame["servers"])
            f["links"] = deepcopy(last_frame["links"])
            f["broken_links"] = deepcopy(last_frame["broken_links"])
            f["users"] = deepcopy(last_frame["users"])
            f["syncs"] = deepcopy(last_frame["syncs"])
        f = witnesses_dissenters(f, e)
        f = info_by_type(f, e)
        last_frame = f
        frames[str(i)] = f
        i += 1
    return frames


def new_frame(server_nums):
    """Given a list of servers, generates an empty frame
    with no links, syncs, users, or broken_links, and
    all servers set to UNDISCOVERED.  Does not
    generate 'summary' or 'date' field"""
    f = {}
    f["server_count"] = len(server_nums)
    f["flag"] = False
    f["links"] = {}
    f["broken_links"] = {}
    f["syncs"] = {}
    f["users"] = {}
    f["servers"] = {}
    for s in server_nums:
        # ensure servers are given as strings
        s = str(s)
        f["servers"][s] = "UNDISCOVERED"
        f["links"][s] = []
        f["broken_links"][s] = []
        f["users"][s] = []
        f["syncs"][s] = []
    return f


def witnesses_dissenters(f, e):
    """Using the witnesses and dissenters
    lists in event e, determine links that should
    exist in frame, and if this frame should be flagged"""
    f["witnesses"] = e["witnesses"]
    f["dissenters"] = e["dissenters"]
    if e["witnesses"] <= e["dissenters"]:
        f["flag"] = True
    # a witness means a new link
    # links are always added to the TARGET's queue.
    for w in e["witnesses"]:
        if w == e["target"]:
            continue
        if (not e["target"] in f["links"][w] and
            not w in f["links"][e["target"]]):
            f["links"][e["target"]].append(w)
        # fix any broken links
        if w in f["broken_links"][e["target"]]:
            f["broken_links"][e["target"]].remove(w)
        if e["target"] in f["broken_links"][w]:
            f["broken_links"][w].remove(e["target"])
    # a dissenter means that link should be removed
    # add broken link only if link existed
    for d in e["dissenters"]:
        if e["target"] in f["links"][d]:
            f["links"][d].remove(e["target"])
            f["broken_links"][e["target"]].append(d)
        if d in f["links"][e["target"]]:
            f["links"][e["target"]].remove(d)
            f["broken_links"][e["target"]].append(d)
    return f


def break_links(me, f):
    # find my links and make them broken links
    for link in f["links"][me]:
        f["broken_links"][me].append(link)
        f["links"][me].remove(link)
    for sync in f["syncs"][me]:
        if not sync in f["broken_links"][me]:
            f["broken_links"][me].append(sync)
        f["syncs"][me].remove(sync)
    # find links that reference me and make them broken links
    for s in f["servers"].keys():
        if s == me:
            continue
        # remove links that reference me
        for link in f["links"][s]:
            if link == me:
                f["links"][s].remove(link)
                f["broken_links"][s].append(link)
        # remove syncs that reference me
        for sync in f["syncs"][s]:
            if sync == me:
                f["syncs"][s].remove(sync)
                if not sync in f["broken_links"][s]:
                    f["broken_links"][s].append(sync)
    # remove all of my user connections
    f["users"][me] = []
    return f


def info_by_type(f, e):
    # add in information from this event
    # by type:
    # make sure it is a string!
    s = str(e["target"])
    if e["type"] == "status":
        f["servers"][s] = e["state"]
        # if server went down, change links and syncs
        if (e["state"] == "DOWN" or
            e["state"] == "REMOVED" or
            e["state"] == "FATAL"):
            f = break_links(s, f)

    elif e["type"] == "reconfig":
        # nothing to do for a reconfig?
        pass

    # connections
    elif e["type"] == "new_conn":
        if not e["conn_addr"] in f["users"][s]:
            f["users"][s].append(e["conn_addr"])
    elif e["type"] == "end_conn":
        if e["conn_addr"] in f["users"][s]:
            f["users"][s].remove(e["conn_addr"])

    # syncs
    elif e["type"] == "sync":
        s_to = e["sync_to"]
        s_from = s
        # do not allow more than one sync per server
        if not s_to in f["syncs"][s_from]:
            f["syncs"][s_from] = []
            f["syncs"][s_from].append(s_to)
        # if links do not exist, add
        if (not s_to in f["links"][s_from] or
            not s_from in f["links"][s_to]):
            f["links"][s_from].append(s_to)
        # remove broken links
        if s_to in f["broken_links"][s_from]:
            f["broken_links"][s_from].remove(s_to)
        if s_from in f["broken_links"][s_to]:
            f["broken_links"][s_to].remove(s_from)

    # exits
    elif e["type"] == "exit":
        f["servers"][s] == "DOWN"
        f = break_links(s, f)

    # fsync and locking
    elif e["type"] == "LOCKED":
        f["servers"][s] += ".LOCKED"
    elif e["type"] == "UNLOCKED":
        n = string.find(f["servers"][s], ".LOCKED")
        f["servers"][s] = f["servers"][s[:n]]
    elif e["type"] == "FSYNC":
        # nothing to do for fsync?
        # render a lock?
        f["servers"][s] += ".LOCKED"
    return f
