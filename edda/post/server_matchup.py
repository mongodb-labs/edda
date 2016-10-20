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

from copy import deepcopy
from edda.supporting_methods import *

LOGGER = logging.getLogger(__name__)


def address_matchup(db, coll_name, hint):
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
        - find all neighbors of (S) and the addresses
        they mention (their neighbors)
        - Make a list of addresses that ALL neighbors of (S)
        mention, neighbor_neighbors
        - By process of elimination between neighbors_of_s and
        neighbors_neighbors, see if there remains one address
        in neighbors_neighbors that (S) has not
        mentioned in its log entries.  This must be (S)'s address.
        Remove this address from mentioned_names.
    - Else (weaker algorithm):
        - By process of elimination between neighbors_of_s and
        mentioned_names, see if there remains one address in
        mentioned_names that (S) has not mentioned in its log entries.
        This must be (S)'s address.  Remove this address from
        mentioned_names.
    - Repeat this process until mentioned_names is empty trying
    each server round-robin, or until all servers have been unsuccessfully
    tried since the last change was made to mentioned_names.

    This algorithm is only sound when the user provides a
    log file from every server in the network, and complete when
    the network graph was complete, or was a tree (connected and acyclic)
    """

    # find a list of all unnamed servers being talked about
    mentioned_names = []

    servers = db[coll_name + ".servers"]
    entries = db[coll_name + ".entries"]

    all_servers_cursor = entries.distinct("info.server")

    LOGGER.info("Attempting to match up all servers:")
    for doc in servers.find({}):
        LOGGER.info("{0}".format(doc))

    # use hints, if we have them
    if hint:
        # split on commas
        hints = hint.split(",")
        for server_hint in hints:
            names = server_hint.split("/")
            if len(names) != 2:
                LOGGER.warning("Malformed hint, should be <self-name>/<network-name>: {0}"
                               .format(server_hint));
                continue

            # see if we have a server with this self-name
            doc = servers.find_one({"self_name": names[0]})
            if doc:
                if doc["network_name"] == "unknown":
                    LOGGER.info("Applying hint {0} to server {1}"
                                .format(server_hint, doc["self_name"]))
                    doc["network_name"] = names[1]
                    servers.save(doc)
                    continue
                LOGGER.info("Found entry for self-name hint {0}, but it already has a network-name"
                            .format(server_hint))

            # if not, see if we have a server with this network-name
            # TODO: can this actually happen?
            doc = servers.find_one({"network_name": names[1]})
            if doc:
                if doc["self_name"] == "unknown":
                    LOGGER.info("Applying hint {0} to server {1}"
                                .format(server_hint, doc["network_name"]))
                    doc["self_name"] = names[0]
                    servers.save(doc)
                    continue
                LOGGER.info("Found entry for network-name in hint {0}, but it already has a self-name"
                            .format(server_hint))

            # if we didn't find a match for our hint, enter it as a new server
            LOGGER.info("Adding a new server entry for hint {0}".format(server_hint))
            index = get_server_num(names[0], True, servers)
            servers.update({ "server_num" : index }, { "$set" : { "network_name" : names[1] }})

    # weed out servers that we already have names for
    # TODO: this is wildly inefficient
    for addr in all_servers_cursor:
        if addr == "self":
            continue
        # if we have already matched this, continue
        if servers.find_one({"network_name": addr}):
            continue
        # if a server's self and network names are the same, set and continue
        doc = servers.find_one({"self_name": addr})
        if doc:
            doc["network_name"] = addr
            servers.save(doc)
            continue
        # do we have a hint for this server?
        # otherwise, we have an unclaimed network name
        if not addr in mentioned_names:
            mentioned_names.append(addr)

    LOGGER.info("All unclaimed mentioned network names:\n{0}".format(mentioned_names))

    round = 0
    change_this_round = False
    while mentioned_names:
        round += 1

        # ignore mongos and configsvr
        #unknowns = list(servers.find({"network_name": "unknown", "type" : "mongod"}))
        unknowns = list(servers.find({"network_name": "unknown"}))

        if len(unknowns) == 0:
            LOGGER.debug("All servers have matched-up names, breaking")
            break

        for s in unknowns:

            # extract server information
            num = s["server_num"]

            # QUESTION: how could network_name be unknown here? We checked above?
            name = None
            if s["network_name"] != "unknown":
                name = s["network_name"]

            # get neighbors of s into list
            # (these are servers s mentions)
            c = list(entries.find({"origin_server": num})
                     .distinct("info.server"))
            LOGGER.debug("Found {0} neighbors of (S)".format(len(c)))
            neighbors_of_s = []
            for entry in c:
                if entry != "self":
                    neighbors_of_s.append(entry)

            # if possible, make a list of servers who mention s
            # and then, the servers they in turn mention
            # (stronger algorithm)
            if name:
                # TODO: refactor this into a function
                LOGGER.debug("Server (S) is named! Running stronger algorithm")
                LOGGER.debug(
                    "finding neighbors of (S) referring to name {0}".format(name))
                neighbors_neighbors = []
                neighbors = list(entries.find(
                    {"info.server": name}).distinct("origin_server"))

                # for each server that mentions s
                for n_addr in neighbors:
                    LOGGER.debug("Find neighbors of (S)'s neighbor, {0}"
                                 .format(n_addr))
                    n_num, n_self_name, n_net_name = name_me(n_addr, servers)
                    if n_num:
                        n_addrs = list(entries.find(
                            {"origin_server": n_num}).distinct("info.server"))
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
                        LOGGER.debug(
                            "Unable to find server number for server {0}, skipping"
                            .format(n_addr))
                LOGGER.debug(
                    "Examining for match:\n{0}\n{1}"
                    .format(neighbors_of_s, neighbors_neighbors))
                match = eliminate(neighbors_of_s, neighbors_neighbors)
                if not match:
                    # (try weaker algorithm anyway, it catches some cases)
                    LOGGER.debug(
                        "No match found using strong algorith, running weak algorithm")
                    match = eliminate(neighbors_of_s, mentioned_names)
            else:
                # (weaker algorithm)
                # is there one server that is mentioned by all that is NOT mentioned by S?
                LOGGER.debug(
                    "Server {0} is unnamed.  Running weaker algorithm"
                    .format(num))
                LOGGER.debug(
                    "Examining for match:\n{0}\n{1}"
                    .format(neighbors_of_s, mentioned_names))
                match = eliminate(neighbors_of_s, mentioned_names)

            LOGGER.debug("match: {0}".format(match))
            if match:
                change_this_round = True
                mentioned_names.remove(match)
                LOGGER.debug("Network name {0} matched to server {1}"
                             .format(match, num))
                assign_address(num, match, False, servers)
            else:
                LOGGER.debug("No match found for server {0} this round"
                             .format(num))

        # break if we've exhausted algorithm
        if not change_this_round:
            LOGGER.debug("Algorithm exhausted, breaking")
            break;

        break


    LOGGER.info("Servers after address matchup:")
    for doc in servers.find({}):
        LOGGER.info("{0}".format(doc))

    if not mentioned_names:
        # for edda to succeed, it needs to match logs to servers
        # so, all servers must have a network name.
        s = list(servers.find({"network_name": "unknown"}))
        if len(s) == 0:
            LOGGER.debug("Successfully named all unnamed servers!")
            return 1
        LOGGER.critical(
            "Exhausted mentioned_names, but {0} servers remain unnamed"
            .format(len(s)))
        return -1

    LOGGER.critical(
        "Could not match {0} addresses: {1}"
        .format(len(mentioned_names), mentioned_names))
    return -1


def eliminate(small, big):
    """See if, by process of elimination,
    there is exactly one entry in big that
    is not in small.  Return that entry, or None.
    """

    # big list must have exactly one entry more than small list
    if (len(small) + 1) != len(big):
        return None

    if len(big) == 1:
        return big[0]

    # make copies of lists, because they are mutable
    # and changes made here will alter the lists outside
    s = deepcopy(small)
    b = deepcopy(big)

    for addr in s:
        if addr in b:
            b.remove(addr)

    if len(b) == 1:
        return b.pop()

    return None
