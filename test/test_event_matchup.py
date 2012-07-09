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

# testing file for logl/post/event_matchup.py

import logging
from pymongo import Connection
from logl.logl import assign_address
from logl.post.event_matchup import *
import pymongo
from datetime import datetime
from datetime import timedelta

def db_setup():
    """Set up necessary server connections"""
    c = Connection()
    logging.basicConfig(level=logging.DEBUG)
    db = c["test_event_matchup"]
    servers = db["AdventureTime.servers"]
    entries = db["AdventureTime.entries"]
    db.drop_collection(servers)
    db.drop_collection(entries)
    return [servers, entries, db]


def db_setup_n_servers(n):
    """Set up necessary server connection, and
    add n servers to the .servers collection.  Set
    the server_num to an int i < n, set the IP
    field to i.i.i.i, and the hostname to i@10gen.com"""
    servers, entries, db = db_setup()
    for i in range(1,n):
        ip = str(i) + "." + str(i) + "." + str(i) + "." + str(i)
        hostname = str(i) + "@10gen.com"
        assign_address(i, ip, servers)
        assign_address(i, hostname, servers)
    return [servers, entries, db]


def generate_entries(x, y):
    """Generate two entries with server fields x and y"""
    a, b = {}, {}
    a["info"], b["info"] = {}, {}
    a["info"]["server"], b["info"]["server"] = x, y
    return [a, b]


def one_entry(type, o_s, date, info):
    """Generate an entry with the specified type and origin_server"""
    e = {}
    e["type"] = type
    e["origin_server"] = o_s
    e["date"] = date
    e["info"] = info
    return e


def test_event_matchup_empty():
    """Test event_matchup on an empty database"""
    pass


# -----------------------------
# test the next_event() method
# -----------------------------


def test_next_event_one_server_state_msg():
    """Test next_event() on lists from just one server"""
    servers, entries, db = db_setup_n_servers(1)
    server_nums = {"1"}
    server_entries = {}
    server_entries["1"] = []
    info = {}
    info["state"] = "ARBITER"
    info["state_code"] = 7
    info["server"] = "34@10gen.com:34343"
    date = datetime.now()
    e1 = one_entry("status", "1", date, info)
    server_entries["1"].append(e1)
    event = next_event(server_nums, server_entries, db, "AdventureTime")
    assert event
    assert event["witnesses"]
    assert len(event["witnesses"]) == 1
    assert not event["dissenters"]
    assert event["type"] == "status"
    assert event["date"] == date
    assert event["state"] == "ARBITER"
    assert event["target"] == "34@10gen.com:34343"
    assert event["summary"] == "Server 34@10gen.com:34343 is now ARBITER"


def test_next_event_two_servers():
    """Test next_event() on two servers with matching entries"""
    servers, entries, db = db_setup_n_servers(2)
    server_nums = {"1", "2"}
    server_entries = {}
    server_entries["1"] = []
    server_entries["2"] = []
    info = {}
    info["state"] = "SECONDARY"
    info["state_code"] = 2
    info["server"] = "llama@the.zoo"
    e1 = one_entry("status", "1", datetime.now(), info)
    e2 = one_entry("status", "2", datetime.now(), info)
    server_entries["1"].append(e1)
    server_entries["2"].append(e2)
    # run next_event()
    event = next_event(server_nums, server_entries, db, "AdventureTime")
    assert event
    assert event["witnesses"]
    assert len(event["witnesses"]) == 2
    assert "1" in event["witnesses"]
    assert "2" in event["witnesses"]
    assert not event["dissenters"]
    assert event["type"] == "status"
    assert event["state"] == "SECONDARY"
    assert event["target"] == "llama@the.zoo"
    assert event["summary"] == "Server llama@the.zoo is now SECONDARY"


def test_next_event_four_servers():
    """Test next_event() on four servers with matching entries"""
    servers, entries, db = db_setup_n_servers(4)
    server_nums = {"1", "2", "3", "4"}
    server_entries = {}
    server_entries["1"] = []
    server_entries["2"] = []
    server_entries["3"] = []
    server_entries["4"] = []
    info = {}
    info["state"] = "SECONDARY"
    info["state_code"] = 2
    info["server"] = "llama@the.zoo"
    e1 = one_entry("status", "1", datetime.now(), info)
    e2 = one_entry("status", "2", datetime.now(), info)
    e3 = one_entry("status", "3", datetime.now(), info)
    e4 = one_entry("status", "4", datetime.now(), info)
    server_entries["1"].append(e1)
    server_entries["2"].append(e2)
    server_entries["3"].append(e3)
    server_entries["4"].append(e4)
    # run next_event()
    event = next_event(server_nums, server_entries, db, "AdventureTime")
    assert event
    assert event["witnesses"]
    assert len(event["witnesses"]) == 4
    assert "1" in event["witnesses"]
    assert "2" in event["witnesses"]
    assert "3" in event["witnesses"]
    assert "4" in event["witnesses"]
    assert not event["dissenters"]
    assert event["type"] == "status"
    assert event["state"] == "SECONDARY"
    assert event["target"] == "llama@the.zoo"
    assert event["summary"] == "Server llama@the.zoo is now SECONDARY"


def test_next_event_two_servers_no_match():
    """Test next_event() on two servers with non-matching entries"""
    servers, entries, db = db_setup_n_servers(2)
    server_nums = {"1", "2"}
    server_entries = {}
    server_entries["1"] = []
    server_entries["2"] = []
    info1, info2 = {}, {}
    info1["state"], info2["state"] = "PRIMARY", "SECONDARY"
    info1["state_code"], info2["state_code"] = 1, 2
    info1["server"], info2["server"] = "llama@the.zoo", "llama@the.zoo"
    e1 = one_entry("status", "1", datetime.now(), info1)
    e2 = one_entry("status", "2", datetime.now(), info2)
    server_entries["1"].append(e1)
    server_entries["2"].append(e2)
    # run next_event()
    event1 = next_event(server_nums, server_entries, db, "AdventureTime")
    event2 = next_event(server_nums, server_entries, db, "AdventureTime")
    assert event1
    assert event2
    assert event1["witnesses"]
    assert event2["witnesses"]
    assert event1["dissenters"]
    assert event2["dissenters"]
    assert len(event1["witnesses"]) == 1
    assert len(event2["witnesses"]) == 1
    assert len(event1["dissenters"]) == 1
    assert len(event2["dissenters"]) == 1
    assert "1" in event1["witnesses"]
    assert "2" in event2["witnesses"]
    assert "1" in event2["dissenters"]
    assert "2" in event1["dissenters"]
    assert event1["state"] == "PRIMARY"
    assert event2["state"] == "SECONDARY"
    assert event1["target"] == event2["target"]


def test_next_event_two_servers_lag():
    """Test next_event() on two servers with lag greater than
    allowable network delay"""
    servers, entries, db = db_setup_n_servers(2)
    server_nums = {"1", "2"}
    server_entries = {}
    server_entries["1"] = []
    server_entries["2"] = []
    info = {}
    info["state"] = "ARBITER"
    info["state_code"] = 7
    info["server"] = "sam@10gen.com"
    e1 = one_entry("status", "1", datetime.now(), info)
    e2 = one_entry("status", "2", datetime.now() + timedelta(seconds=4), info)
    server_entries["1"].append(e1)
    server_entries["2"].append(e2)
    # run next_event()
    event1 = next_event(server_nums, server_entries, db, "AdventureTime")
    event2 = next_event(server_nums, server_entries, db, "AdventureTime")
    assert event1
    assert event2
    assert event1["witnesses"]
    assert event2["witnesses"]
    assert event1["dissenters"]
    assert event2["dissenters"]
    assert len(event1["witnesses"]) == 1
    assert len(event2["witnesses"]) == 1
    assert len(event1["dissenters"]) == 1
    assert len(event2["dissenters"]) == 1
    assert "1" in event1["witnesses"]
    assert "2" in event2["witnesses"]
    assert "1" in event2["dissenters"]
    assert "2" in event1["dissenters"]


def test_next_event_three_servers_one_lag():
    """Test next_event() on three servers with lag greater than
    allowable network delay affecting one server"""
    servers, entries, db = db_setup_n_servers(3)
    server_nums = {"1", "2", "3"}
    server_entries = {}
    server_entries["1"] = []
    server_entries["2"] = []
    server_entries["3"] = []
    info = {}
    info["state"] = "ARBITER"
    info["state_code"] = 7
    info["server"] = "sam@10gen.com"
    e1 = one_entry("status", "1", datetime.now(), info)
    e2 = one_entry("status", "2", datetime.now() + timedelta(seconds=4), info)
    e3 = one_entry("status", "3", datetime.now(), info)
    server_entries["1"].append(e1)
    server_entries["2"].append(e2)
    server_entries["3"].append(e3)
    # run next_event()
    event1 = next_event(server_nums, server_entries, db, "AdventureTime")
    event2 = next_event(server_nums, server_entries, db, "AdventureTime")
    assert not next_event(server_nums, server_entries, db, "AdventureTime")
    assert event1
    assert event2
    assert event1["witnesses"]
    assert event2["witnesses"]
    assert event1["dissenters"]
    assert event2["dissenters"]
    assert len(event1["witnesses"]) == 2
    assert len(event2["witnesses"]) == 1
    assert len(event1["dissenters"]) == 1
    assert len(event2["dissenters"]) == 2
    assert "1" in event1["witnesses"]
    assert "3" in event1["witnesses"]
    assert "2" in event2["witnesses"]
    assert "3" in event2["dissenters"]
    assert "1" in event2["dissenters"]
    assert "2" in event1["dissenters"]


def test_next_event_no_entries():
    """Test next_event() for an event where there
    are no entries for a certain server.  So,
    server_entries["name"] is None"""
    servers, entries, db = db_setup_n_servers(2)
    server_nums = {"1", "2"}
    server_entries = {}
    server_entries["1"] = []
    server_entries["2"] = []
    info = {}
    info["state"] = "SECONDARY"
    info["state_code"] = 2
    info["server"] = "llama@the.zoo"
    e1 = one_entry("status", "1", datetime.now(), info)
    server_entries["1"].append(e1)
    # run next_event()
    event = next_event(server_nums, server_entries, db, "AdventureTime")
    assert event
    assert event["witnesses"]
    assert len(event["witnesses"]) == 1
    assert "1" in event["witnesses"]
    assert event["dissenters"]
    assert len(event["dissenters"]) == 1
    assert "2" in event["dissenters"]


def test_next_event_all_empty():
    """Test next_event() on all empty lists, but with
    server names present (i.e. we ran out of entries)"""
    servers, entries, db = db_setup_n_servers(2)
    server_nums = {"1", "2"}
    server_entries = {}
    server_entries["1"] = []
    server_entries["2"] = []
    # run next_event()
    assert not next_event(server_nums, server_entries, db, "AdventureTime")


def test_next_event_all_empty_but_one():
    """Test next_event() on input on many servers, but with
    all servers' lists empty save one (i.e. we went through
    the other servers' entries already)"""
    """Test next_event() for an event where there
    are no entries for a certain server.  So,
    server_entries["name"] is None"""
    servers, entries, db = db_setup_n_servers(4)
    server_nums = {"1", "2", "3", "4"}
    server_entries = {}
    server_entries["1"] = []
    server_entries["2"] = []
    server_entries["3"] = []
    server_entries["4"] = []
    info = {}
    info["state"] = "SECONDARY"
    info["state_code"] = 2
    info["server"] = "llama@the.zoo"
    e1 = one_entry("status", "1", datetime.now(), info)
    server_entries["1"].append(e1)
    # run next_event()
    event = next_event(server_nums, server_entries, db, "AdventureTime")
    assert event
    assert event["witnesses"]
    assert len(event["witnesses"]) == 1
    assert "1" in event["witnesses"]
    assert event["dissenters"]
    assert len(event["dissenters"]) == 3
    assert "2" in event["dissenters"]
    assert "3" in event["dissenters"]
    assert "4" in event["dissenters"]


def test_next_event_two_matching_some_lag():
    """Test next_event() on lists from two servers
    with entries that do match, but are a second apart in time"""
    servers, entries, db = db_setup_n_servers(2)
    server_nums = {"1", "2"}
    server_entries = {}
    server_entries["1"] = []
    server_entries["2"] = []
    info = {}
    info["state"] = "SECONDARY"
    info["state_code"] = 2
    info["server"] = "llama@the.zoo"
    e1 = one_entry("status", "1", datetime.now(), info)
    e2 = one_entry("status", "2", datetime.now() + timedelta(seconds=1), info)
    server_entries["2"].append(e2)
    server_entries["1"].append(e1)
    info2 = {}
    info2["state"] = "FATAL"
    info2["state_code"] = 4
    info2["server"] = "finn@adventure.time"
    e3 = one_entry("status", "1", datetime.now(), info2)
    e4 = one_entry("status", "2", datetime.now() + timedelta(seconds=1), info2)
    server_entries["1"].append(e3)
    server_entries["2"].append(e4)
    # run next_event()
    event = next_event(server_nums, server_entries, db, "AdventureTime")
    event2 = next_event(server_nums, server_entries, db, "AdventureTime")
    assert not next_event(server_nums, server_entries, db, "AdventureTime")
    assert event
    assert event2
    assert event["witnesses"]
    assert event2["witnesses"]
    assert len(event["witnesses"]) == 2
    assert len(event2["witnesses"]) == 2
    assert "1" in event["witnesses"]
    assert "2" in event["witnesses"]
    assert "1" in event2["witnesses"]
    assert "2" in event2["witnesses"]
    assert not event["dissenters"]
    assert not event2["dissenters"]


# -------------------------------------
# test the target_server_match() method
# -------------------------------------


def test_target_server_match_both_self():
    """Test method on two entries whose info.server
    field is 'self'"""
    servers, entries, db = db_setup()
    a, b = generate_entries("self", "self")
    assert not target_server_match(a, b, servers)


def test_target_server_match_both_same_IP():
    """Test method on two entries with corresponding
    info.server fields, using IP addresses"""
    servers, entries, db = db_setup()
    a, b = generate_entries("1.2.3.4", "1.2.3.4")
    assert target_server_match(a, b, servers)


def test_target_server_match_both_same_hostname():
    """Test method on two entries with corresponding
    info.server fields, using hostnames"""
    servers, entries, db = db_setup()
    a, b = generate_entries("sam@10gen.com", "sam@10gen.com")
    assert target_server_match(a, b, servers) == "sam@10gen.com"


def test_target_server_match_both_different_hostnames():
    """Test method on two entries with different
    info.server fields, both hostnames"""
    servers, entries, db = db_setup()
    a, b = generate_entries("sam@10gen.com", "kaushal@10gen.com")
    a["origin_server"] = "1"
    b["origin_server"] = "2"
    assign_address(1, "finn@adventure.time", servers)
    assign_address(2, "jake@adventure.time", servers)
    assert not target_server_match(a, b, servers)


def test_target_server_match_both_different_IPs():
    """Test method on two entries with different
    info.server fields, both IP addresses"""
    servers, entries, db = db_setup()
    a, b = generate_entries("1.2.3.4", "5.6.7.8")
    a["origin_server"] = "1"
    b["origin_server"] = "2"
    assign_address(1, "1.1.1.1", servers)
    assign_address(2, "2.2.2.2", servers)
    assert not target_server_match(a, b, servers)


def test_target_server_match_IP():
    """Test method on entries where one cites 'self',
    other cites IP address"""
    servers, entries, db = db_setup()
    a, b = generate_entries("self", "1.1.1.1")
    a["origin_server"] = "1"
    b["origin_server"] = "2"
    assign_address(1, "1.1.1.1", servers)
    assign_address(2, "2.2.2.2", servers)
    assert target_server_match(a, b, servers) == "1.1.1.1"


def test_target_server_match_hostname():
    """Test method on entries where one cites 'self',
    other cites hostname"""
    servers, entries, db = db_setup()
    a, b = generate_entries("jake@adventure.time", "self")
    a["origin_server"] = "1"
    b["origin_server"] = "2"
    assign_address(1, "finn@adventure.time", servers)
    assign_address(2, "jake@adventure.time", servers)
    assert target_server_match(a, b, servers) == "jake@adventure.time"


def test_target_server_match_IP_no_match():
    """Test method on entries where one cites 'self',
    other cites incorrect IP"""
    servers, entries, db = db_setup()
    a, b = generate_entries("self", "4.4.4.4")
    a["origin_server"] = "1"
    b["origin_server"] = "2"
    assign_address(1, "1.1.1.1", servers)
    assign_address(2, "2.2.2.2", servers)
    assert not target_server_match(a, b, servers)


def test_target_server_match_hostname_no_match():
    """Test method on entries where one cites 'self',
    other cites incorrect hostname"""
    servers, entries, db = db_setup()
    a, b = generate_entries("self", "marcelene@adventure.time")
    a["origin_server"] = "1"
    b["origin_server"] = "2"
    assign_address(1, "iceking@adventure.time", servers)
    assign_address(2, "bubblegum@adventure.time", servers)
    assert not target_server_match(a, b, servers)


def test_target_server_match_unknown_IP():
    """Test method on entries where one cites 'self',
    other cites first server's true IP, but IP is not yet
    recorded in the .servers collection"""
    servers, entries, db = db_setup()
    a, b = generate_entries("self", "1.1.1.1")
    a["origin_server"] = "1"
    b["origin_server"] = "2"
    assign_address(1, "unknown", servers)
    assign_address(2, "2.2.2.2", servers)
    assert target_server_match(a, b, servers) == "1.1.1.1"


def test_target_server_match_unknown_hostname():
    """Test method on entries where one cites 'self',
    other cites first server's true hostname, but
    hostname is not yet recorded in the .servers collection"""
    servers, entries, db = db_setup()
    a, b = generate_entries("treetrunks@adventure.time", "self")
    a["origin_server"] = "1"
    b["origin_server"] = "2"
    assign_address(1, "LSP@adventure.time", servers)
    assign_address(2, "unknown", servers)
    assert target_server_match(a, b, servers) == "treetrunks@adventure.time"


# -------------------------------------
# test the resolve_dissenters() method
# -------------------------------------




