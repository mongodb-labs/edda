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

from logl.post.server_matchup import *
from test_clock_skew import generate_doc
from logl.logl import assign_address
import pymongo
from pymongo import Connection
from datetime import datetime
from time import sleep


def db_setup():
    """Set up a database for use by tests"""
    c = Connection()
    db = c["test_server_matchup"]
    servers = db["hp.servers"]
    entries = db["hp.entries"]
    clock_skew = db["hp.clock_skew"]
    db.drop_collection(servers)
    db.drop_collection(entries)
    db.drop_collection(clock_skew)
    return [servers, entries, clock_skew, db]


def test_eliminate_empty():
    """Test the eliminate() method on two empty lists"""
    assert eliminate([], []) == None


def test_eliminate_s_bigger():
    """Test eliminate() on two lists where the "small"
    list actually has more entries than the "big" list"""
    assert eliminate(["2", "3", "4"], ["2", "3"]) == None


def test_eliminate_s_empty():
    """Test eliminate() on two lists where s
    is empty and b has one entry"""
    assert eliminate([], ["Henry"]) == "Henry"


def test_eliminate_s_empty_b_large():
    """Test eliminate() on two lists where s
    is empty and b is large"""
    assert eliminate([], ["a", "b", "c", "d", "e"]) == None


def test_eliminate_normal_one():
    """S has one entry, b has two entries"""
    assert eliminate(["a"], ["b", "a"]) == "b"


def test_eliminate_normal_two():
    """A normal case for eliminate()"""
    assert eliminate(["f", "g", "h"], ["f", "z", "g", "h"]) == "z"


def test_eliminate_different_lists():
    """s and b have no overlap"""
    assert eliminate(["a", "b", "c"], ["4", "5", "6"]) == None


def test_eliminate_different_lists_b_one():
    """s and b have no overlap, b only has one entry"""
    print eliminate(["a", "b", "c"], ["fish"])
    assert eliminate(["a", "b", "c"], ["fish"]) == "fish"


def test_eliminate_too_many_extra():
    """Test eliminate() on the case where there
    is more than one entry left in b after analysis"""
    assert eliminate(["a", "b", "c"], ["a", "b", "c", "d", "e"]) == None


def test_empty():
    """Test on an empty database"""
    servers, entries, clock_skew, db = db_setup()
    assert address_matchup(db, "hp") == 1


def test_one_unknown():
    """Test on a database with one unknown server"""
    servers, entries, clock_skew, db = db_setup()
    # insert one unknown server
    assign_address(1, "1", servers)
    assert address_matchup(db, "hp") == -1


def test_one_known():
    """Test on one named server (hostname)"""
    servers, entries, clock_skew, db = db_setup()
    assign_address(1, "Dumbledore", servers)
    assert address_matchup(db, "hp") == 1


def test_one_known_IP():
    """Test on one named server (IP)"""
    servers, entries, clock_skew, db = db_setup()
    assign_address(1, "100.54.24.66", servers)
    assert address_matchup(db, "hp") == 1


def test_all_servers_unknown():
    """Test on db where all servers are unknown
    (neither hostname or IP)"""
    # this case could be handled, in the future
    servers, entries, clock_skew, db = db_setup()
    assign_address(1, "1", servers)
    assign_address(2, "2", servers)
    assign_address(3, "3", servers)
    assert address_matchup(db, "hp") == -1


def test_all_known():
    """Test on db where all servers' names
    are already known (hostnames only)"""
    servers, entries, clock_skew, db = db_setup()
    assign_address(1, "Harry", servers)
    assign_address(2, "Hermione", servers)
    assign_address(3, "Rom", servers)
    assert address_matchup(db, "hp") == 1


def test_all_known_IPs():
    """Test on db where all servers' names
    are already known (IPs only)"""
    servers, entries, clock_skew, db = db_setup()
    assign_address(1, "1.1.1.1", servers)
    assign_address(2, "2.2.2.2", servers)
    assign_address(3, "3.3.3.3", servers)
    assert address_matchup(db, "hp") == 1


def test_all_known_mixed():
    """Test on db where all servers names,
    both IPs and hostnames, are known"""
    servers, entries, clock_skew, db = db_setup()
    assign_address(1, "1.1.1.1", servers)
    assign_address(1, "Harry", servers)
    assign_address(2, "2.2.2.2", servers)
    assign_address(2, "Hermione", servers)
    assign_address(3, "3.3.3.3", servers)
    assign_address(3, "Ron", servers)
    assert address_matchup(db, "hp") == 1


def test_one_known_one_unknown():
    """Test on a db with two servers, one
    known and one unknown (hostnames only)"""
    servers, entries, clock_skew, db = db_setup()
    assign_address(1, "Parvati", servers)
    assign_address(2, "2", servers)
    # add a few entries
    entries.insert(generate_doc("status", "Parvati", "PRIMARY", 1, "Padma", datetime.now()))
    entries.insert(generate_doc("status", "Parvati", "SECONDARY", 2, "Padma", datetime.now()))
    entries.insert(generate_doc("status", "Parvati", "ARBITER", 2, "Padma", datetime.now()))
    sleep(3)
    entries.insert(generate_doc("status", "2", "PRIMARY", 1, "self", datetime.now()))
    entries.insert(generate_doc("status", "2", "SECONDARY", 2, "self", datetime.now()))
    entries.insert(generate_doc("status", "2", "ARBITER", 7, "self", datetime.now()))
    assert address_matchup(db, "hp") == 1
    assert servers.find_one({"server_num": "2"})["server_name"] == "Padma"
    # check that entries were not changed
    assert entries.find({"origin_server": "2"}).count() == 3


def test_one_known_one_unknown_IPs():
    """Test on a db with two servers, one
    known and one unknown (IPs only)"""
    servers, entries, clock_skew, db = db_setup()
    assign_address(1, "1.1.1.1", servers)
    assign_address(2, "2", servers)
    # add a few entries
    entries.insert(generate_doc("status", "1.1.1.1", "PRIMARY", 1, "2.2.2.2", datetime.now()))
    entries.insert(generate_doc("status", "1.1.1.1", "SECONDARY", 2, "2.2.2.2", datetime.now()))
    entries.insert(generate_doc("status", "1.1.1.1", "ARBITER", 2, "2.2.2.2", datetime.now()))
    sleep(3)
    entries.insert(generate_doc("status", "2", "PRIMARY", 1, "self", datetime.now()))
    entries.insert(generate_doc("status", "2", "SECONDARY", 2, "self", datetime.now()))
    entries.insert(generate_doc("status", "2", "ARBITER", 7, "self", datetime.now()))
    assert address_matchup(db, "hp") == 1
    assert servers.find_one({"server_num": "2"})["server_IP"] == "2.2.2.2"
    # check that entries were not changed
    assert entries.find({"origin_server": "2"}).count() == 3


def test_two_known_one_unknown():
    """Test on a db with two known servers and one
    unknown server (hostnames only)"""
    servers, entries, clock_skew, db = db_setup()
    assign_address(1, "Moony", servers)
    assign_address(2, "Padfoot", servers)
    assign_address(3, "unknown", servers)
    entries.insert(generate_doc("status", "Moony", "PRIMARY", 1, "Prongs", datetime.now()))
    entries.insert(generate_doc("status", "Padfoot", "PRIMARY", 1, "Prongs", datetime.now()))
    entries.insert(generate_doc("status", "3", "PRIMARY", 1, "self", datetime.now()))
    entries.insert(generate_doc("status", "Moony", "SECONDARY", 2, "Prongs", datetime.now()))
    entries.insert(generate_doc("status", "Padfoot", "SECONDARY", 2, "Prongs", datetime.now()))
    entries.insert(generate_doc("status", "3", "SECONDARY", 2, "self", datetime.now()))
    assert address_matchup(db, "hp") == 1
    assert servers.find_one({"server_num": "3"})["server_name"] == "Prongs"
    # check that entries were not changed
    assert entries.find({"origin_server": "3"}).count() == 2


def test_two_known_one_unknown_IPs():
    """Test on a db with two known servers and one
    unknown server (IPs only)"""
    servers, entries, clock_skew, db = db_setup()
    assign_address(1, "1.1.1.1", servers)
    assign_address(2, "2.2.2.2", servers)
    assign_address(3, "unknown", servers)
    entries.insert(generate_doc("status", "1.1.1.1", "PRIMARY", 1, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "2.2.2.2", "PRIMARY", 1, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "3", "PRIMARY", 1, "self", datetime.now()))
    entries.insert(generate_doc("status", "1.1.1.1", "SECONDARY", 2, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "2.2.2.2", "SECONDARY", 2, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "3", "SECONDARY", 2, "self", datetime.now()))
    assert address_matchup(db, "hp") == 1
    assert servers.find_one({"server_num": "3"})["server_IP"] == "3.3.3.3"
    # check that entries were not changed
    assert entries.find({"origin_server": "3"}).count() == 2


def test_one_known_two_unknown():
    """Test on a db with one known server and
    two unknown servers (hostnamess only)"""
    servers, entries, clock_skew, db = db_setup()
    # add servers
    assign_address(1, "unknown", servers)
    assign_address(2, "Luna", servers)
    assign_address(3, "unknown", servers)
    # add entries about server 1, Ginny
    entries.insert(generate_doc("status", "1", "UNKNOWN", 6, "self", datetime.now()))
    entries.insert(generate_doc("status", "Luna", "UNKNOWN", 6, "Ginny", datetime.now()))
    entries.insert(generate_doc("status", "3", "UNKNOWN", 6, "Ginny", datetime.now()))
    entries.insert(generate_doc("status", "1", "ARBITER", 7, "self", datetime.now()))
    entries.insert(generate_doc("status", "Luna", "ARBITER", 7, "Ginny", datetime.now()))
    entries.insert(generate_doc("status", "3", "ARBITER", 7, "Ginny", datetime.now()))
    # add entries about server 3, Neville
    entries.insert(generate_doc("status", "1", "PRIMARY", 1, "Neville", datetime.now()))
    entries.insert(generate_doc("status", "Luna", "PRIMARY", 1, "Neville", datetime.now()))
    entries.insert(generate_doc("status", "3", "PRIMARY", 1, "self", datetime.now()))
    entries.insert(generate_doc("status", "1", "FATAL", 4, "Neville", datetime.now()))
    entries.insert(generate_doc("status", "Luna", "FATAL", 4, "Neville", datetime.now()))
    entries.insert(generate_doc("status", "3", "FATAL", 4, "self", datetime.now()))
    # check name matching
    assert address_matchup(db, "hp") == 1
    assert servers.find_one({"server_num": "1"})["server_name"] == "Ginny"
    assert servers.find_one({"server_num": "3"})["server_name"] == "Neville"
    # check that entries were not changed
    assert entries.find({"origin_server": "1"}).count() == 4
    assert entries.find({"origin_server": "3"}).count() == 4


def test_one_known_two_unknown_IPs():
    """Test on a db with one known server and
    two unknown servers (IPs only)"""
    servers, entries, clock_skew, db = db_setup()
    # add servers
    assign_address(1, "unknown", servers)
    assign_address(2, "1.2.3.4", servers)
    assign_address(3, "unknown", servers)
    # add entries about server 1, Ginny
    entries.insert(generate_doc("status", "1", "UNKNOWN", 6, "self", datetime.now()))
    entries.insert(generate_doc("status", "2", "UNKNOWN", 6, "5.6.7.8", datetime.now()))
    entries.insert(generate_doc("status", "3", "UNKNOWN", 6, "5.6.7.8", datetime.now()))
    entries.insert(generate_doc("status", "1", "ARBITER", 7, "self", datetime.now()))
    entries.insert(generate_doc("status", "2", "ARBITER", 7, "5.6.7.8", datetime.now()))
    entries.insert(generate_doc("status", "3", "ARBITER", 7, "5.6.7.8", datetime.now()))
    # add entries about server 3, Neville
    entries.insert(generate_doc("status", "1", "PRIMARY", 1, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "2", "PRIMARY", 1, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "3", "PRIMARY", 1, "self", datetime.now()))
    entries.insert(generate_doc("status", "1", "FATAL", 4, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "2", "FATAL", 4, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "3", "FATAL", 4, "self", datetime.now()))
    # check name matching
    assert address_matchup(db, "hp") == 1
    assert servers.find_one({"server_num": "1"})["server_IP"] == "5.6.7.8"
    assert servers.find_one({"server_num": "3"})["server_IP"] == "3.3.3.3"
    # check that entries were not changed
    assert entries.find({"origin_server": "1"}).count() == 4
    assert entries.find({"origin_server": "3"}).count() == 4


def test_known_names_unknown_IPs():
    """Test on a db with three servers whose names
    are known, IPs are unknown"""
    servers, entries, clock_skew, db = db_setup()
    # add servers
    assign_address(1, "Grubblyplank", servers)
    assign_address(2, "Hagrid", servers)
    assign_address(3, "Trelawney", servers)
    # add entries
    entries.insert(generate_doc("status", "1", "PRIMARY", 1, "2.2.2.2", datetime.now()))
    entries.insert(generate_doc("status", "1", "SECONDARY", 2, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "2", "ARBITER", 7, "1.1.1.1", datetime.now()))
    entries.insert(generate_doc("status", "2", "RECOVERING", 3, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "3", "DOWN", 8, "1.1.1.1", datetime.now()))
    entries.insert(generate_doc("status", "3", "FATAL", 4, "2.2.2.2", datetime.now()))
    # check name matching
    assert address_matchup(db, "hp") == 1
    assert servers.find_one({"server_num": "1"})["server_IP"] == "1.1.1.1"
    assert servers.find_one({"server_name": "Grubblyplank"})["server_IP"] == "1.1.1.1"
    assert servers.find_one({"server_num": "2"})["server_IP"] == "2.2.2.2"
    assert servers.find_one({"server_name": "Hagrid"})["server_IP"] == "2.2.2.2"
    assert servers.find_one({"server_num": "3"})["server_IP"] == "3.3.3.3"
    assert servers.find_one({"server_name": "Trelawney"})["server_IP"] == "3.3.3.3"


def test_known_IPs_unknown_names():
    """Test on db with three servers whose IPs
    are known, names are unknown"""
    servers, entries, clock_skew, db = db_setup()
    # add servers
    assign_address(1, "1.1.1.1", servers)
    assign_address(2, "2.2.2.2", servers)
    assign_address(3, "3.3.3.3", servers)
    # add entries
    entries.insert(generate_doc("status", "1", "PRIMARY", 1, "Crabbe", datetime.now()))
    entries.insert(generate_doc("status", "1", "SECONDARY", 2, "Goyle", datetime.now()))
    entries.insert(generate_doc("status", "2", "ARBITER", 7, "Malfoy", datetime.now()))
    entries.insert(generate_doc("status", "2", "RECOVERING", 3, "Goyle", datetime.now()))
    entries.insert(generate_doc("status", "3", "DOWN", 8, "Malfoy", datetime.now()))
    entries.insert(generate_doc("status", "3", "FATAL", 4, "Crabbe", datetime.now()))
    # check name matching
    assert address_matchup(db, "hp") == 1
    assert servers.find_one({"server_num": "1"})["server_name"] == "Malfoy"
    assert servers.find_one({"server_IP": "1.1.1.1"})["server_name"] == "Malfoy"
    assert servers.find_one({"server_num": "2"})["server_name"] == "Crabbe"
    assert servers.find_one({"server_IP": "2.2.2.2"})["server_name"] == "Crabbe"
    assert servers.find_one({"server_num": "3"})["server_name"] == "Goyle"
    assert servers.find_one({"server_IP": "3.3.3.3"})["server_name"] == "Goyle"


def test_missing_four_two_one_one():
    """Test on db with four total servers: two named,
    one unnamed, one not present (simulates a missing log)"""
    servers, entries, clock_skew, db = db_setup()
    assign_address(1, "Gryffindor", servers)
    assign_address(1, "1.1.1.1", servers)
    assign_address(2, "Ravenclaw", servers)
    assign_address(2, "2.2.2.2", servers)
    assign_address(3, "Slytherin", servers)
    # this case should be possible with the strong algorithm (aka a complete graph)
    # although we will be left with one unmatched name, "Hufflepuff" - "4.4.4.4"
    # fill in entries
    entries.insert(generate_doc("status", "1", "PRIMARY", 1, "2.2.2.2", datetime.now()))
    entries.insert(generate_doc("status", "1", "PRIMARY", 1, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "1", "PRIMARY", 1, "4.4.4.4", datetime.now()))
    entries.insert(generate_doc("status", "2", "PRIMARY", 1, "1.1.1.1", datetime.now()))
    entries.insert(generate_doc("status", "2", "PRIMARY", 1, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "2", "PRIMARY", 1, "4.4.4.4", datetime.now()))
    entries.insert(generate_doc("status", "3", "PRIMARY", 1, "1.1.1.1", datetime.now()))
    entries.insert(generate_doc("status", "3", "PRIMARY", 1, "2.2.2.2", datetime.now()))
    entries.insert(generate_doc("status", "3", "PRIMARY", 1, "4.4.4.4", datetime.now()))
    # address_matchup will return -1
    assert address_matchup(db, "hp") == -1
    # but Slytherin should be named
    assert servers.find_one({"server_num": "3"})["server_IP"] == "3.3.3.3"
    assert servers.find_one({"server_name": "Slytherin"})["server_IP"] == "3.3.3.3"
    assert not servers.find_one({"server_name": "Hufflepuff"})
    assert not servers.find_one({"server_IP": "4.4.4.4"})


def test_missing_four_one_two_one():
    """Test on a db with four total servers: one named,
    one unnamed, two not present (simulates missing logs)"""
    pass


def test_missing_four_one_two_one():
    """Test on a db with four total servers: one named,
    two unnamed, one not present (simulates midding log)"""
    pass


def test_missing_three_total_one_present():
    """Test on a db with three total servers, one unnamed,
    two not present (missing logs)"""
    pass


def test_incomplete_graph_one():
    """Test a network graph with three servers, A, B, C,
    and the following edges:
    A - B, B - C"""
    pass


def test_incomplete_graph_two():
    """Test a network graph with four servers, A, B, C, D
    with the following edges:
    A - B, B - C, C - D, D - A"""
    # this case contains a cycle, not possible for this algorithm to solve
    pass


def test_incomplete_graph_three():
    """Test a network graph with four servers: A, B, C, D
    and the following edges:
    A - B, B - C, C - D, D - A, B - D"""
    # this case should be doable.  It may take a few rounds of the
    # algorithm to work, though
    pass

def test_incomplete_graph_four():
    """Test a network graph with four servers: A, B, C, D
    and the following edges:
    B - A, B - C, B - D"""
    # this is not a doable case
    pass


def test_incomplete_graph_five():
    """Test a network graph with four servers: A, B, C, D, E
    and the following edges:
    A - B, B - C, C - D, D - E"""
    # doable in a few rounds
    pass


def test_incomplete_graph_six():
    """Test a graph with three servers: A, B, C
    and the following edges:
    A - B"""
    # is doable for A and B, not C
    pass


def test_incomplete_graph_seven():
    """Test a graph with four servers: A, B, C, D
    and the following edges:
    A - B, C - D"""
    # is doable with strong algorithm, not weak algorithm
    pass
