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
from logl.logl import new_server
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
    servers.insert(new_server(1, "1"))
    assert address_matchup(db, "hp") == -1


def test_one_known():
    """Test on one named server (hostname)"""
    servers, entries, clock_skew, db = db_setup()
    servers.insert(new_server(1, "Dumbledore"))
    assert address_matchup(db, "hp") == 1


def test_one_known_IP():
    """Test on one named server (IP)"""
    servers, entries, clock_skew, db = db_setup()
    servers.insert(new_server(1, "100.54.24.66"))
    assert address_matchup(db, "hp") == 1


def test_all_servers_unknown():
    """Test on db where all servers are unknown
    (neither hostname or IP)"""
    # this case could be handled, in the future
    servers, entries, clock_skew, db = db_setup()
    servers.insert(new_server(1, "1"))
    servers.insert(new_server(2, "2"))
    servers.insert(new_server(3, "3"))
    assert address_matchup(db, "hp") == -1


def test_all_known():
    """Test on db where all servers' names
    are already known (hostnames only)"""
    servers, entries, clock_skew, db = db_setup()
    servers.insert(new_server(1, "Harry"))
    servers.insert(new_server(2, "Hermione"))
    servers.insert(new_server(3, "Ron"))
    assert address_matchup(db, "hp") == 1


def test_all_known_IPs():
    """Test on db where all servers' names
    are already known (IPs only)"""
    servers, entries, clock_skew, db = db_setup()
    servers.insert(new_server(1, "1.1.1.1"))
    servers.insert(new_server(2, "2.2.2.2"))
    servers.insert(new_server(3, "3.3.3.3"))
    assert address_matchup(db, "hp") == 1


def test_all_known_mixed():
    """Test on db where all servers names,
    both IPs and hostnames, are known"""
    servers, entries, clock_skew, db = db_setup()
    servers.insert(new_server(1, "1.1.1.1"))
    servers.insert(new_server(1, "Harry"))
    servers.insert(new_server(2, "2.2.2.2"))
    servers.insert(new_server(2, "Hermione"))
    servers.insert(new_server(3, "3.3.3.3"))
    servers.insert(new_server(3, "Ron"))
    assert address_matchup(db, "hp") == 1


def test_one_known_one_unknown():
    """Test on a db with two servers, one
    known and one unknown (hostnames only)"""
    servers, entries, clock_skew, db = db_setup()
    servers.insert(new_server(1, "Parvati"))
    servers.insert(new_server(2, "2"))
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
    servers.insert(new_server(1, "1.1.1.1"))
    servers.insert(new_server(2, "2"))
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
    servers.insert(new_server(1, "Moony"))
    servers.insert(new_server(2, "Padfoot"))
    servers.insert(new_server(3, "unknown"))
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
    servers.insert(new_server(1, "1.1.1.1"))
    servers.insert(new_server(2, "2.2.2.2"))
    servers.insert(new_server(3, "unknown"))
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
    servers.insert(new_server(1, "unknown"))
    servers.insert(new_server(2, "Luna"))
    servers.insert(new_server(3, "unknown"))
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
    servers.insert(new_server(1, "unknown"))
    servers.insert(new_server(2, "1.2.3.4"))
    servers.insert(new_server(3, "unknown"))
    # add entries about server 1, Ginny
    entries.insert(generate_doc("status", "1", "UNKNOWN", 6, "self", datetime.now()))
    entries.insert(generate_doc("status", "1.2.3.4", "UNKNOWN", 6, "5.6.7.8", datetime.now()))
    entries.insert(generate_doc("status", "3", "UNKNOWN", 6, "5.6.7.8", datetime.now()))
    entries.insert(generate_doc("status", "1", "ARBITER", 7, "self", datetime.now()))
    entries.insert(generate_doc("status", "1.2.3.4", "ARBITER", 7, "5.6.7.8", datetime.now()))
    entries.insert(generate_doc("status", "3", "ARBITER", 7, "5.6.7.8", datetime.now()))
    # add entries about server 3, Neville
    entries.insert(generate_doc("status", "1", "PRIMARY", 1, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "1.2.3.4", "PRIMARY", 1, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "3", "PRIMARY", 1, "self", datetime.now()))
    entries.insert(generate_doc("status", "1", "FATAL", 4, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "1.2.3.4", "FATAL", 4, "3.3.3.3", datetime.now()))
    entries.insert(generate_doc("status", "3", "FATAL", 4, "self", datetime.now()))
    # check name matching
    assert address_matchup(db, "hp") == 1
    assert servers.find_one({"server_num": "1"})["server_IP"] == "5.6.7.8"
    assert servers.find_one({"server_num": "3"})["server_IP"] == "3.3.3.3"
    # check that entries were changed
    assert entries.find({"origin_server": "1"}).count() == 4
    assert entries.find({"origin_server": "3"}).count() == 4
