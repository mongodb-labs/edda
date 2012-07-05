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

from logl.filters.init_and_listen import *
from datetime import datetime


def test_criteria():
    """Test the criteria() method of this module"""
    # these should not pass
    assert criteria("this should not pass") == -1
    assert criteria("Mon Jun 11 15:56:40 [conn5] end connection "
        "127.0.0.1:55224 (2 connections now open)") == -1
    assert criteria("Mon Jun 11 15:56:16 [initandlisten] ** WARNING: soft "
        "rlimits too low. Number of files is 256, should be at least 1000"
        "") == -1
    assert criteria("init and listen starting") == -1
    assert criteria("[initandlisten]") == -1
    assert criteria("starting") == -1
    assert criteria("connection accepted") == -1
    # these should pass
    assert criteria("Mon Jun 11 15:56:16 [initandlisten] MongoDB starting "
        ": pid=7029 port=27018 dbpath=/data/rs2 64-bit "
        "host=Kaushals-MacBook-Air.local") == 1
    #assert criteria("Mon Jun 11 15:56:24 [initandlisten] connection accepted from 127.0.0.1:55227 #6 (4 connections now open)") == 2
    return


def test_process():
    """test the process() method of this module"""
    date = datetime.now()
    # non-valid message
    assert process("this is an invalid message", date) == None
    # these should pass
    doc = process("Mon Jun 11 15:56:16 [initandlisten] MongoDB starting : "
        "pid=7029 port=27018 dbpath=/data/rs2 64-bit host=Kaushals-MacBook-Air"
        ".local", date)
    assert doc
    assert doc["type"] == "init"
    assert doc["info"]["server"] == "Kaushals-MacBook-Air.local:27018"
    assert doc["info"]["subtype"] == "startup"
    return


def test_starting_up():
    """test the starting_up() method of this module"""
    doc = {}
    doc["type"] = "init"
    doc["info"] = {}
    # non-valid message
    assert starting_up("this is a nonvalid message", doc) == None
    assert starting_up("Mon Jun 11 15:56:16 [initandlisten] MongoDB starting "
        ": 64-bit host=Kaushals-MacBook-Air.local", doc) == None
    # valid messages
    doc = starting_up("Mon Jun 11 15:56:16 [initandlisten] MongoDB starting : "
        "pid=7029 port=27018 dbpath=/data/rs2 64-bit "
        "host=Kaushals-MacBook-Air.local", doc)
    assert doc
    assert doc["type"] == "init"
    assert doc["info"]["subtype"] == "startup"
    assert doc["info"]["server"] == "Kaushals-MacBook-Air.local:27018"
    return


def new_conn():
    """test the new_conn() method of this module"""
    doc = {}
    doc["type"] = "init"
    doc["info"] = {}
    # non-valid messages
    assert new_conn("this is an invalid message", doc) == None
    assert new_conn("Mon Jun 11 15:56:16 [initandlisten] connection accepted "
        "from 127.0.0.1:55224 (4 connections now open)", doc) == None
    assert new_conn("Mon Jun 11 15:56:16 [initandlisten] connection #5 (4 "
        "connections now open)", doc) == None
    assert new_conn("Mon Jun 11 15:56:16 [initandlisten] connection accepted "
        "from 127.0.0.1 #5 (4 connections now open)", doc) == None
    # valid messages
    doc = new_conn("Mon Jun 11 15:56:16 [initandlisten] connection accepted "
        "from 127.0.0.1:55224 #5", doc)
    assert doc
    assert doc["type"] == "init"
    assert doc["info"]["subtype"] == "new_conn"
    assert doc["info"]["conn_number"] == "5"
    assert doc["info"]["server"] == "127.0.0.1:55224"
    return
