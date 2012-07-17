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
from copy import deepcopy
from .clock_skew import server_clock_skew
from supporting_methods import *
import operator
import re


def address_matchup(db, collName):
    """Runs an algorithm to match servers with their
    corresponding hostnames/IP addresses.  The algorithm works as follows,
    using replica set status messages from the logs to find addresses:

    - Make a list, mentioned_names of all the IPs being talked about;
    these must be all the servers in the network.
    - For each server (S) in the collName.servers collection, if it
    already has been matched to an IP address and hostname, remove
    these addresses from mentioned_names.  Move to next server.
    - Else, make a list of the addresses (S) mentions, neighbors_of_s
    - If (S) has a known IP address or hostname:
        (stronger algorithm)
        - find all neighbors of (S) and the addresses they mention (their neighbors)
        - Make a list of addresses that ALL neighbors of (S) mention, neighbor_neighbors
        - By process of elimination between neighbors_of_s and neighbors_neighbors, see if
    there remains one address in neighbors_neighbors that (S) has not
    mentioned in its log entries.  This must be (S)'s address.  Remove this
    address from mentioned_names.
    - Else (weaker algorithm):
        - By process of elimination between neighbors_of_s and mentioned_names,
    see if there remains one address in mentioned_names that (S) has not
    mentioned in its log entries.  This must be (S)'s address.  Remove this
    address from mentioned_names.
    - Repeat this process until mentioned_names is empty trying each server
    round-robin, or until all servers have been unsuccessfully tried since the last
    change was made to mentioned_names.

    This algorithm is only sound when the user provides a
    log file from every server in the network, and complete when
    the network graph was complete, or was a tree (connected and acyclic)"""

    logger = logging.getLogger(__name__)

    # find a list of all unnamed servers being talked about
    mentioned_names = []

    servers = db[collName + ".servers"]
    entries = db[collName + ".entries"]

    all_servers_cursor = entries.find().distinct("info.server")
    for addr in all_servers_cursor:
        if addr == "self":
            continue
        if servers.find_one({"$or": [{"server_name" : addr}, {"server_IP": addr}]}):
            continue
        if not addr in mentioned_names:
            mentioned_names.append(addr)

    last_change = -1
    round = 0
    while mentioned_names:
        round += 1
        unknowns = list(servers.find({"$or": [{"server_name": "unknown"}, {"server_IP": "unknown"}]}))

        if len(unknowns) == 0:
            logger.debug("No unknowns, breaking")
            break
        for s in unknowns:

            # extract server information
            num = s["server_num"]
            if s["server_name"] != "unknown":
                name = s["server_name"]
            elif s["server_IP"] != "unknown":
                name = s["server_IP"]
            else:
                name = None

            # break if we've exhausted algorithm
            if last_change == num:
                logger.debug("Algorithm exhausted, breaking")
                break
            if last_change == -1:
                last_change = num

            # get neighbors of s into list
            # (these are servers s mentions)
            c = list(entries.find({"origin_server": num}).distinct("info.server"))
            logger.debug("Found {0} neighbors of (S)".format(len(c)))
            neighbors_of_s = []
            for entry in c:
                if entry != "self":
                    neighbors_of_s.append(entry)

            # if possible, make a list of servers who mention s
            # and then, the servers they in turn mention
            # (stronger algorithm)
            if name:
                logger.debug("Server (S) is named! Running stronger algorithm")
                logger.debug("finding neighbors of (S) referring to name {0}".format(name))
                neighbors_neighbors = []
                neighbors = entries.find({"info.server": name}).distinct("origin_server")
                # for each server that mentions s
                for n_addr in neighbors:
                    logger.debug("Find neighbors of (S)'s neighbor, {0}".format(n_addr))
                    n_num, n_name, n_IP = name_me(n_addr, servers)
                    if n_num:
                        logger.debug("Succesfully found server number for server {0}".format(n_addr))
                        n_addrs = entries.find({"origin_server": n_num}).distinct("info.server")
                        if not neighbors_neighbors:
                            # n_addr: the server name
                            # n_addrs: the names that n_addr mentions
                            for addr in n_addrs:
                                if addr != "self":
                                    neighbors_neighbors.append(addr)
                        else:
                            n_n_copy = deepcopy(neighbors_neighbors)
                            neighbors_neighbors = []
                            for addr in n_addrs:
                                if addr in n_n_copy:
                                    neighbors_neighbors.append(addr)
                    else:
                        logger.debug("Unable to find server number for server {0}, skipping".format(n_addr))
                logger.debug("Examining for match:\n{0}\n{1}".format(neighbors_of_s, neighbors_neighbors))
                match = eliminate(neighbors_of_s, neighbors_neighbors)
                if not match:
                    # (try weaker algorithm anyway, it catches some cases)
                    logger.debug("No match found using strong algorith, running weak algorithm")
                    match = eliminate(neighbors_of_s, mentioned_names)
            else:
                # (weaker algorithm)
                logger.debug("Server {0} is unnamed.  Running weaker algorithm".format(num))
                logger.debug("Examining for match:\n{0}\n{1}".format(neighbors_of_s, mentioned_names))
                match = eliminate(neighbors_of_s, mentioned_names)

            if match:
                if is_IP(match):
                    # entries will ALWAYS be labeled with the server_num
                    if s["server_IP"] == "unknown":
                        last_change = num
                        mentioned_names.remove(match)
                        logger.debug("IP {0} matched to server {1}".format(match, num))
                else:
                    if s["server_name"] == "unknown":
                        logger.debug("hostname {0} matched to server {1}".format(match, num))
                        last_change = num
                        mentioned_names.remove(match)
                assign_address(num, match, servers)
            else:
                logger.debug("No match found for server {0} this round".format(num))
        else:
            continue
        break

    if not mentioned_names:
        # for logl to succeed, it needs to match logs to servers
        # so, it would really just need mentioned_names to be empty,
        # and for ever server to have either a hostname or IP
        # (the idea being that any log lines could be matched to some server)
        s = list(servers.find({"$and": [{"server_name": "unknown"}, {"server_IP": "unknown"}]}))
        if len(s) == 0:
            logger.debug("Successfully named all unnamed servers!")
            return 1
        logger.debug("Exhausted mentioned_names, but {0} servers remain unnamed".format(len(s)))
        return -1
    logger.debug("Could not match {0} addresses: {1}".format(len(mentioned_names), mentioned_names))
    return -1


def name_me(s, servers):
    """Given a string s (which can be a server_num,
    server_name, or server_IP), method returns all info known
    about the server in a tuple [server_num, server_name, server_IP]"""
    name = None
    IP = None
    num = None
    docs = []
    docs.append(servers.find_one({"server_num": s}))
    docs.append(servers.find_one({"server_name": s}))
    docs.append(servers.find_one({"server_IP": s}))
    for doc in docs:
        if not doc:
            continue
        if doc["server_name"] != "unknown":
            name = doc["server_name"]
            name = name.replace('\n', "")
        if doc["server_IP"] != "unknown":
            IP = doc["server_IP"]
        num = doc["server_num"]
    return [num, name, IP]


def eliminate(small, big):
    """See if, by process of elimination,
    there is exactly one entry in big that
    is not in small.  Return that entry, or None."""
    # make copies of lists, because they are mutable
    # and changes made here will alter the lists outside
    if not big:
        return None
    s = deepcopy(small)
    b = deepcopy(big)
    for addr in s:
        if not b:
            return None
        if addr in b:
            b.remove(addr)
    if len(b) == 1:
        return b.pop()
    return None
