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
import pymongo
import logging

# The documents this module
# generates will include the following information:

# date : (string)
# server_count : (int)
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
    servers = list(db[collName + ".servers"].find())
    s_count = len(servers)

    for e in events:
        frame = {}
        # fill in various fields
        frame["server_count"] = s_count
        frame["date"] = str(e["date"])
        frame["summary"] = e["summary"]
        # see what data we can glean from the last frame
        if last_frame:
            frame["servers"] = last_frame["servers"]
            frame["links"] = last_frame["links"]
            frame["users"] = last_frame["users"]
            frame["syncs"] = last_frame["syncs"]
        else:
            for server in servers:
                frame["servers"][server] = "UNDISCOVERED"
                frame["links"] = {}
                frame["syncs"] = {}
                frame["users"] = {}
                frame["servers"] = {}
        frame = info_by_type(frame, event)
        frame = witnesses_dissenters(frame, event)
        last_frame = frame
        frames[str(i)] = frame
        i += 1
    return frames


def witnesses_dissenters(frame, e):
    """Using the witnesses and dissenters
    lists in event e, determine links that should
    exist in frame, and if this frame should be flagged"""
    frame["witnesses"] = e["witnesses"]
    frame["dissenters"] = e["dissenters"]
    if e["witnesses"] <= e["dissenters"]:
        frame["flag"] = True
    # a witness means a new link
    for w in e["witnesses"]:
        frame["links"][w] = e["target"]
    # a dissenter means that link should be removed
    for d in e["dissenters"]:
        frame["links"][d] = []
    return frame



def info_by_type(f, e):
    # add in information from this event
    # by type:
    if e["type"] == "status":
        f["servers"][e["target"]] = e["state"]
        # if server went down, change links and syncs
        if (e["state"] == "DOWN" or
            e["state"] == "REMOVED" or
            e["state"] == "FATAL"):
            f = break_links(e["target"], f)

    elif e["type"] == "reconfig":
        # nothing to do for a reconfig?
        pass
    elif e["type"] == "new_conn":
        if not e["conn_IP"] in f["users"][e["target"]]:
            f["users"][e["target"]].append(e["conn_IP"])
    elif e["type"] == "end_conn":
        if e["conn_IP"] in f["users"][e["target"]]:
            f["users"][e["target"]].remove(e["conn_IP"])
    elif e["type"] == "sync":
        if not e["sync_to"] in f["syncs"][e["target"]]:
            f["syncs"][e["target"]].append(e["sync_to"])
    elif e["type"] == "exit":
        f["servers"][e["target"]] == "DOWN"
        f = break_links(e["target"], f)
    elif e["type"] == "lock":
        f["servers"][e["target"]] += ".LOCKED"
    elif e["type"] == "unlock":
        s = string.find(f["servers"][e["target"]], ".LOCKED")
        f["servers"][e["target"]] = f["servers"][e["target"][:s]]
    return f
