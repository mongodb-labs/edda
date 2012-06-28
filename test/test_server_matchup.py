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


def test_empty():
    """Test on an empty database"""
    servers, entries, clock_skew, db = db_setup()
    assert server_matchup(db, "hp") == 1


def test_one_unknown():
    """Test on a database with one unknown server"""
    servers, entries, clock_skew, db = db_setup()
    # insert one unknown server
    servers.insert(new_server(1, "1"))
    assert server_matchup(db, "hp") == -1


def test_one_known():
    servers, entries, clock_skew, db = db_setup()
    servers.insert(new_server(1, "Dumbledore"))
    assert server_matchup(db, "hp") == 1


def test_all_servers_unknown():
    """Test on db where all servers are unknown"""
    # this case could be handled, in the future
    servers, entries, clock_skew, db = db_setup()
    servers.insert(new_server(1, "1"))
    servers.insert(new_server(2, "2"))
    servers.insert(new_server(3, "3"))
    assert server_matchup(db, "hp") == -1


def test_all_known():
    """Test on db where all servers' names
    are already known"""
    servers, entries, clock_skew, db = db_setup()
    servers.insert(new_server(1, "Harry"))
    servers.insert(new_server(2, "Hermione"))
    servers.insert(new_server(3, "Ron"))
    assert server_matchup(db, "hp") == 1


def test_one_known_one_unknown():
    """Test on a db with two servers, one
    known and one unknown"""
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
    assert server_matchup(db, "hp") == 1
    assert servers.find_one({"server_num": "2"})["server_name"] == "Padma"
    # check that clock skew is also correct
    assert clock_skew.find_one({"server_num": "2"})["partners"]["1"]["-3"]
    assert clock_skew.find_one({"server_num": "1"})["partners"]["2"]["3"]
    # check that entries were also changed
    assert entries.find({"origin_server": "2"}).count() == 0
    assert entries.find({"origin_server": "Padma"}).count() == 3


def test_two_known_one_unknown():
    """Test on a db with two known servers and one
    unknown server"""
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
    assert server_matchup(db, "hp") == 1
    assert servers.find_one({"server_num": "3"})["server_name"] == "Prongs"
    # check that entries were changed
    assert entries.find({"origin_server": "3"}).count() == 0
    assert entries.find({"origin_server": "Prongs"}).count() == 2


def test_one_known_two_unknown():
    """Test on a db with one known server and
    two unknown servers"""
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
    assert server_matchup(db, "hp") == 1
    assert servers.find_one({"server_num": "1"})["server_name"] == "Ginny"
    assert servers.find_one({"server_num": "3"})["server_name"] == "Neville"
    # check that entries were changed
    assert entries.find({"origin_server": "1"}).count() == 0
    assert entries.find({"origin_server": "3"}).count() == 0
    assert entries.find({"origin_server": "Ginny"}).count() == 4
    assert entries.find({"origin_server": "Neville"}).count() == 4
