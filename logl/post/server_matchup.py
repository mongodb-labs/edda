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
from clock_skew import server_clock_skew
import operator


def address_matching(db, collName):
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

    # find a list of all unnamed servers being talked about
    mentioned_names = []

    servers = db[collName + ".servers"]
    entries = db[collName + ".entries"]

    cursor = entries.find().distinct("info.server")
    for addr in cursor:
        if addr == "self":
            continue
        if servers.find_one({"server_name" : addr}) or servers.find_one({"server_IP" : addr}):
            # concerned that skipping these will make test fail
            continue
        mentioned_names.append(addr)

    last_change = None
    while mentioned_names:
        for s in servers.find({"$or": [{"server_name": "unknown"}, {"server_IP": "unknown"}]}):

            # extract server information
            num = s["server_num"]
            if s["server_name"] != "unknown":
                name = s["server_name"]
            elif s["server_IP"] != "unknown":
                name = s["server_IP"]
            else:
                name = None

            # get neighbors of s into list
            c = entries.find({"origin_server": num}).distinct("info.server")
            neighbors_of_s = []
            for entry in c:
                neighbors_of_s.append(c["info"]["server"])

            # if possible, make a list of neighbors of s
            # (stronger algorithm)
            if name:
                neighbors_neighbors = []
                neighbors = entries.find({"info.server": name}).distinct("origin_server")
                # for each server that mentions s
                for n in neighbors:
                    n_addr = n["origin_server"]
                    n_num, n_name, n_IP = name_me(n_addr, servers)
                    if n_num:
                    # might not be able to find neighbors' lists
                    # only able to if we have an origin_server number for that addr
                        n_addrs = entries.find({"origin_server": n_num}).distinct("info.server")
                    # find all servers they mention
                # find the common addresses among all the neighbors
                # put them in neighbors_neighbors
                match = eliminate(neighbors_of_s, neighbors_neighbors)
            else:
                # (weaker algorithm)
                match = eliminate(neighbors_of_s, mentioned_names)

            if match:
                if is_IP(match):
                    # this code could be reorganized to be much more compact and efficient
                    if s["server_IP"] == "unknown":
                        s["server_IP"] = match
                        servers.save(s)
                        last_change = num
                        mentioned_names.remove(match)
                        logger.debug("IP {0} matched to server {1}".format(match, num))
                    elif: s["server_IP"] == match:
                        logger.debug("duplicate IP found for server {0}".format(match))
                else:
                    if s["server_name"] == "unknown":
                        s["server_name"] = match
                        logger.debug("hostname {0} matched to server {1}".format(match, num))
                        servers.save(s)
                        last_change = num
                        mentioned_names.remove(match)
                    elif s["server_name"] == match:
                        logger.debug("duplicate hostname found for server {0}".format(match, num))
                    else:
                        logger.debug("Server {0}'s stored hostname {1} " +
                                     "is different from match {2}".format(num, name, match))


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
        if doc["server_name"] != "unknown":
            name = doc["server_name"]
        if doc["server_IP"] != "unknown":
            IP = doc["server_IP"]
        num = doc["server_num"]
    return [nun, name, IP]


def eliminate(s_list, n_list):
    """See if, by process of elimination,
    there is exactly one entry in n_list that
    is not in s_list.  Return that entry, or None."""
    # make copies of lists, because they are mutable
    # and changes made here will alter the lists outside
    s = s_list
    n = n_list
    for addr in s:
        if not n:
            return None
        if addr in n:
            n.remove(addr)
    if len(n) == 1:
        return n.pop()
    return None


def server_matchup(db, collName):
    """Given the mongoDB entries generated by logl,
    attempts to resolve any differences in server names
    or missing server names across entries.  Returns
    1 on success, -1 on failure"""
    # check for clock skew in tandem with server name checking
    # --> check if coll.servers has any entries where server_num == server_name
    logger = logging.getLogger(__name__)

    servers = db[collName + ".servers"]
    entries = db[collName + ".entries"]
    clock_skew = db[collName + ".clock_skew"]
    server_count = servers.find().count()

    # no servers
    if server_count == 0:
        return 1

    # no unknown servers
    unknowns = servers.find({"server_name" : "unknown"})
    unknown_count = unknowns.count()
    if unknown_count == 0:
        return 1

    # all servers are unknown
    # this case could probably be handled for cases where server_count > 1
    logger.debug("attempting to name {0} unnamed servers".format(unknown_count))
    if server_count == unknown_count:
        return -1

    # find a list of all unnamed servers being talked about
    unmatched_names = []
    cursor = entries.distinct("info.server")
    for name in cursor:
        if name == "self":
            continue
        if servers.find_one({"server_name" : name}):
            continue
        unmatched_names.append(name)

    # if there are no free names and still unknown servers, failure.
    if len(unmatched_names) == 0:
        return -1

    failures = 0
    candidates = {}

    # match up the names!
    for unknown in unknowns:
        num = str(unknown["server_num"])
        # if we're on the last name, winner!!
        if len(unmatched_names) == 1:
            candidates[iter(unmatched_names).next()] = 1
        else:
            for name in unmatched_names:
                logger.debug("Trying name {0} for server {1}".format(name, num))
                # in the .servers coll, replace server_name for unknown with name
                unknown["server_name"] = name
                servers.save(unknown)
                # in the .entries coll, replace origin_server from unknown["server_num"] to name
                entries.update({"origin_server": num}, {"$set": {"origin_server": name}}, multi=True)
                # run the clock skew algorithm
                clock_skew.remove({"server_num" : num})
                server_clock_skew(db, collName)
                # store name and highest weight clock skew from this round (with first named server)
                doc = clock_skew.find_one({"server_num" : num})
                wt = 0
                for partner in doc["partners"]:
                    for skew in doc["partners"][partner]:
                        if doc["partners"][partner][skew] > wt:
                            wt = doc["partners"][partner][skew]
                candidates[name] = wt
                logger.debug("storing candidate {0} with weight {1}".format(name, wt))
                # set the entries back to the original server_num
                entries.update({"origin_server": name}, {"$set": {"origin_server": num}}, multi=True)
        # select candidate with highest weight!
        wt = 0
        winner = ""
        for name in candidates.iterkeys():
            if candidates[name] >= wt:
                wt = candidates[name]
                winner = name
        # update db entries accordingly with winning name
        unknown["server_name"] = winner
        servers.save(unknown)
        entries.update({"origin_server" : num}, {"$set" : {"origin_server" : winner}}, multi=True)
        # run clock skew algorithm anew
        server_clock_skew(db, collName)
        logger.info("Naming this server {0}, removing {0} from list".format(winner, winner))
        unmatched_names.remove(winner)
        candidates = {}

    if failures > 0:
        logger.info("Unable to match names for {0} of {1} unnamed servers".format(failures, unknown_count))
        return -1
    logger.info("Successfully named {0} of {0} unnamed servers".format(unknown_count))
    return 1

