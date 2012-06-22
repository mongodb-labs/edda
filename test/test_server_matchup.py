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
from logl.logl import new_server
import pymongo
from pymongo import Connection


def db_setup():
    """Set up a database for use by tests"""
    c = Connection()
    db = c["test_server_matchup"]
    servers = db["hp.servers"]
    entries = db["hp.entries"]
    db.drop_collection(servers)
    db.drop_collection(entries)
    return [servers, entries, db]


def test_empty():
    """Test on an empty database"""
    results = db_setup()
    assert server_matchup(results[2], "hp") == 1


def test_one_unknown():
    """Test on a database with one unknown server"""
    results = db_setup()
    # insert one unknown server
    results[0].insert(new_server(1, 1))
    assert server_matchup(results[2], "hp") == -1


def test_one_known():
    results = db_setup()
    results[0].insert(new_server(1, "Dumbledore"))
    assert server_matchup(results[2], "hp") == 1


def test_all_servers_unknown():
    """Test on db where all servers are unknown"""
    # this case could be handled, in the future
    results = db_setup()
    results[0].insert(new_server(1, 1))
    results[0].insert(new_server(2, 2))
    results[0].insert(new_server(3, 3))
    assert server_matchup(results[2], "hp") == -1


def test_all_known():
    """Test on db where all servers' names
    are already known"""
    results = db_setup()
    results[0].insert(new_server(1, "Harry"))
    results[0].insert(new_server(2, "Hermione"))
    results[0].insert(new_server(3, "Ron"))
    assert server_matchup(results[2], "hp") == 1





