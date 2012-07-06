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


from pymongo import Connection
from logl.logl import assign_address
from logl.post.event_matchup import *
import pymongo
from datetime import datetime


def db_setup():
    """Set up necessary server connections"""
    c = Connection()
    db = c["test_event_matchup"]
    servers = db["AdventureTime.servers"]
    entries = db["AdventureTime.entries"]
    db.drop_collection(servers)
    db.drop_collection(entries)
    return [servers, entries, db]


def generate_entries(x, y):
    """Generate two entries with server fields x and y"""
    a, b = {}, {}
    a["info"], b["info"] = {}, {}
    a["info"]["server"], b["info"]["server"] = x, y
    return [a, b]


def one_entry(type, )
    """Generate an entry with the specified fields"""
    return e


def test_event_matchup_empty():
    """Test event_matchup on an empty database"""
    pass


# -----------------------------
# test the next_event() method
# -----------------------------

def test_next_event_one_server():
    """Test next_event() on lists from just one server"""
    pass


def test_next_event_all_empty():
    """Test next_event() on all empty lists, but with
    server names present (i.e. we ran out of entries)"""
    pass


def test_next_event_all_empty_but_one():
    """Test next_event() on input on many servers, but with
    all servers' lists empty save one (i.e. we went through
    the other servers' entries already)"""
    pass


def test_next_event_one():
    """Test next_event() on lists from two servers
    with one matching entry in each server's list"""
    pass


def test_next_event_two():
    """Test next_event() on lists from two servers
    with entries that do not match"""
    pass


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
    assert target_server_match(a, b, servers)


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
    assert target_server_match(a, b, servers)


def test_target_server_match_hostname():
    """Test method on entries where one cites 'self',
    other cites hostname"""
    servers, entries, db = db_setup()
    a, b = generate_entries("jake@adventure.time", "self")
    a["origin_server"] = "1"
    b["origin_server"] = "2"
    assign_address(1, "finn@adventure.time", servers)
    assign_address(2, "jake@adventure.time", servers)
    assert target_server_match(a, b, servers)


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
    assert target_server_match(a, b, servers)


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
    assert target_server_match(a, b, servers)


# -------------------------------------
# test the resolve_dissenters() method
# -------------------------------------




