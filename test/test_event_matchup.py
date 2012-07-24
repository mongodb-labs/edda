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

# testing file for edda/post/event_matchup.py

import logging
import pymongo
import unittest #there is a relative input problem with this file as well. MARKED TO FIX.

from copy import deepcopy
from datetime import datetime
from datetime import timedelta
from edda.run_edda import assign_address
from edda.post.event_matchup import *
from pymongo import Connection


# -----------------------------
# helper methods for testing
# -----------------------------

class test_event_matchup(unittest.TestCase):

    def db_setup(self):
        """Set up necessary server connections"""
        c = Connection()
        logging.basicConfig(level=logging.DEBUG)
        db = c["test_event_matchup"]
        servers = db["AdventureTime.servers"]
        entries = db["AdventureTime.entries"]
        db.drop_collection(servers)
        db.drop_collection(entries)
        return [servers, entries, db]

    def db_setup_n_servers(self, n):
        """Set up necessary server connection, and
        add n servers to the .servers collection.  Set
        the server_num to an int i < n, set the IP
        field to i.i.i.i, and the self_name to i@10gen.com"""
        servers, entries, db = self.db_setup()
        for i in range(1,n + 1):
            ip = str(i) + "." + str(i) + "." + str(i) + "." + str(i)
            self_name = str(i) + "@10gen.com"
            assign_address(i, ip, False, servers)
            assign_address(i, self_name, True, servers)
        return [servers, entries, db]


    def generate_entries(self, x, y):
        """Generate two entries with server fields x and y"""
        a, b = {}, {}
        a["info"], b["info"] = {}, {}
        a["info"]["server"], b["info"]["server"] = x, y
        return [a, b]


    def one_entry(self, type, o_s, date, info):
        """Generate an entry with the specified type and origin_server"""
        e = {}
        e["type"] = type
        e["origin_server"] = o_s
        e["date"] = date
        e["info"] = info
        return e


    def one_event(self, type, target, date):
        """Generates and returns an event with
        the specified fields"""
        e = {}
        e["type"] = type
        if e["type"] == "status":
            e["state"] = "UNKNOWN"
        if e["type"] == "sync":
            e["sync_to"] = "jake@adventure.time"
        if e["type"] == "new_conn" or e["type"] == "end_conn":
            e["conn_number"] = "3"
            e["conn_IP"] = "jake@adventure.time"
        e["target"] = target
        e["date"] = date
        e["summary"] = generate_summary(e, target)
        return e


    # -------------------------------
    # test the event_matchup() method
    # -------------------------------


    def test_event_match_up_empty(self):
        """Test event_matchup on an empty database"""
        pass


    # -----------------------------
    # test the next_event() method
    # -----------------------------


    def test_next_event_one_server_state_msg(self):
        """Test next_event() on lists from just one server"""
        servers, entries, db = self.db_setup_n_servers(1)
        server_nums = {"1"}
        server_entries = {}
        server_entries["1"] = []
        info = {}
        info["state"] = "ARBITER"
        info["state_code"] = 7
        info["server"] = "34@10gen.com:34343"
        date = datetime.now()
        e1 = self.one_entry("status", "1", date, info)
        server_entries["1"].append(e1)
        event = next_event(server_nums, server_entries, db, "AdventureTime")
        assert event
        assert event["witnesses"]
        assert len(event["witnesses"]) == 1
        assert not event["dissenters"]
        assert event["type"] == "status"
        assert event["date"] == date
        assert event["state"] == "ARBITER"
        num = servers.find_one({"network_name": "34@10gen.com:34343"})
        assert event["target"] != num
    #    assert event["summary"] == "Server 34@10gen.com:34343 is now ARBITER"


    def test_next_event_two_servers(self):
        """Test next_event() on two servers with matching entries"""
        servers, entries, db = self.db_setup_n_servers(2)
        server_nums = {"1", "2"}
        server_entries = {}
        server_entries["1"] = []
        server_entries["2"] = []
        info = {}
        info["state"] = "SECONDARY"
        info["state_code"] = 2
        info["server"] = "llama@the.zoo"
        e1 = self.one_entry("status", "1", datetime.now(), info)
        e2 = self.one_entry("status", "2", datetime.now(), info)
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
        num = servers.find_one({"network_name": "llama@the.zoo"})["server_num"]
        assert event["target"] == num
        assert event["summary"] == "llama@the.zoo is now SECONDARY".format(num)


    def test_next_event_four_servers(self):
        """Test next_event() on four servers with matching entries"""
        servers, entries, db = self.db_setup_n_servers(4)
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
        e1 = self.one_entry("status", "1", datetime.now(), info)
        e2 = self.one_entry("status", "2", datetime.now(), info)
        e3 = self.one_entry("status", "3", datetime.now(), info)
        e4 = self.one_entry("status", "4", datetime.now(), info)
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
        num = servers.find_one({"network_name": "llama@the.zoo"})["server_num"]
        assert event["target"] == num
        print event["summary"]
        assert event["summary"] == "llama@the.zoo is now SECONDARY"


    def test_next_event_two_servers_no_match(self):
        """Test next_event() on two servers with non-matching entries"""
        servers, entries, db = self.db_setup_n_servers(2)
        server_nums = {"1", "2"}
        server_entries = {}
        server_entries["1"] = []
        server_entries["2"] = []
        info1, info2 = {}, {}
        info1["state"], info2["state"] = "PRIMARY", "SECONDARY"
        info1["state_code"], info2["state_code"] = 1, 2
        info1["server"], info2["server"] = "llama@the.zoo", "llama@the.zoo"
        e1 = self.one_entry("status", "1", datetime.now(), info1)
        e2 = self.one_entry("status", "2", datetime.now(), info2)
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


    def test_next_event_two_servers_lag(self):
        """Test next_event() on two servers with lag greater than
        allowable network delay"""
        servers, entries, db = self.db_setup_n_servers(2)
        server_nums = {"1", "2"}
        server_entries = {}
        server_entries["1"] = []
        server_entries["2"] = []
        info = {}
        info["state"] = "ARBITER"
        info["state_code"] = 7
        info["server"] = "sam@10gen.com"
        e1 = self.one_entry("status", "1", datetime.now(), info)
        e2 = self.one_entry("status", "2", datetime.now() + timedelta(seconds=4), info)
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


    def test_next_event_three_servers_one_lag(self):
        """Test next_event() on three servers with lag greater than
        allowable network delay affecting one server"""
        servers, entries, db = self.db_setup_n_servers(3)
        server_nums = {"1", "2", "3"}
        server_entries = {}
        server_entries["1"] = []
        server_entries["2"] = []
        server_entries["3"] = []
        info = {}
        info["state"] = "ARBITER"
        info["state_code"] = 7
        info["server"] = "sam@10gen.com"
        e1 = self.one_entry("status", "1", datetime.now(), info)
        e2 = self.one_entry("status", "2", datetime.now() + timedelta(seconds=4), info)
        e3 = self.one_entry("status", "3", datetime.now(), info)
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


    def test_next_event_no_entries(self):
        """Test next_event() for an event where there
        are no entries for a certain server.  So,
        server_entries["name"] is None"""
        servers, entries, db = self.db_setup_n_servers(2)
        server_nums = {"1", "2"}
        server_entries = {}
        server_entries["1"] = []
        server_entries["2"] = []
        info = {}
        info["state"] = "SECONDARY"
        info["state_code"] = 2
        info["server"] = "llama@the.zoo"
        e1 = self.one_entry("status", "1", datetime.now(), info)
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


    def test_next_event_all_empty(self):
        """Test next_event() on all empty lists, but with
        server names present (i.e. we ran out of entries)"""
        servers, entries, db = self.db_setup_n_servers(2)
        server_nums = {"1", "2"}
        server_entries = {}
        server_entries["1"] = []
        server_entries["2"] = []
        # run next_event()
        assert not next_event(server_nums, server_entries, db, "AdventureTime")


    def test_next_event_all_empty_but_one(self):
        """Test next_event() on input on many servers, but with
        all servers' lists empty save one (i.e. we went through
        the other servers' entries already)"""
        """Test next_event() for an event where there
        are no entries for a certain server.  So,
        server_entries["name"] is None"""
        servers, entries, db = self.db_setup_n_servers(4)
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
        e1 = self.one_entry("status", "1", datetime.now(), info)
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


    def test_next_event_two_matching_some_lag(self):
        """Test next_event() on lists from two servers
        with entries that do match, but are a second apart in time"""
        servers, entries, db = self.db_setup_n_servers(2)
        server_nums = {"1", "2"}
        server_entries = {}
        server_entries["1"] = []
        server_entries["2"] = []
        info = {}
        info["state"] = "SECONDARY"
        info["state_code"] = 2
        info["server"] = "llama@the.zoo"
        e1 = self.one_entry("status", "1", datetime.now(), info)
        e2 = self.one_entry("status", "2", datetime.now() + timedelta(seconds=1), info)
        server_entries["2"].append(e2)
        server_entries["1"].append(e1)
        info2 = {}
        info2["state"] = "FATAL"
        info2["state_code"] = 4
        info2["server"] = "finn@adventure.time"
        e3 = self.one_entry("status", "1", datetime.now(), info2)
        e4 = self.one_entry("status", "2", datetime.now() + timedelta(seconds=1), info2)
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


    def test_target_server_match_both_self(self):
        """Test method on two entries whose info.server
        field is 'self'"""
        servers, entries, db = self.db_setup()
        a, b = self.generate_entries("self", "self")
        assert not target_server_match(a, b, servers)


    def test_target_server_match_both_same_IP(self):
        """Test method on two entries with corresponding
        info.server fields, using IP addresses"""
        servers, entries, db = self.db_setup()
        a, b = self.generate_entries("1.2.3.4", "1.2.3.4")
        assert target_server_match(a, b, servers)


    def test_target_server_match_both_same_self_name(self):
        """Test method on two entries with corresponding
        info.server fields, using self_names"""
        servers, entries, db = self.db_setup()
        a, b = self.generate_entries("sam@10gen.com", "sam@10gen.com")
        assert target_server_match(a, b, servers)


    def test_target_server_match_both_different_self_names(self):
        """Test method on two entries with different
        info.server fields, both self_names
        """
        servers, entries, db = self.db_setup()
        a, b = self.generate_entries("sam@10gen.com", "kaushal@10gen.com")
        a["origin_server"] = "1"
        b["origin_server"] = "2"
        assign_address(1, "finn@adventure.time", True, servers)
        assign_address(2, "jake@adventure.time", True, servers)
        assert not target_server_match(a, b, servers)


    def test_target_server_match_both_different_network_names(self):
        """Test method on two entries with different
        info.server fields, both network addresses
        """
        servers, entries, db = self.db_setup()
        a, b = self.generate_entries("1.2.3.4", "5.6.7.8")
        a["origin_server"] = "1"
        b["origin_server"] = "2"
        assign_address(1, "1.1.1.1", False, servers)
        assign_address(2, "2.2.2.2", False, servers)
        assert not target_server_match(a, b, servers)


    def test_target_server_match_network(self):
        """Test method on entries where one cites 'self',
        other cites network_name
        """
        servers, entries, db = self.db_setup()
        a, b = self.generate_entries("self", "1.1.1.1")
        a["origin_server"] = "1"
        b["origin_server"] = "2"
        assign_address(1, "1.1.1.1", False, servers)
        assign_address(2, "2.2.2.2", False, servers)
        assert target_server_match(a, b, servers)


    def test_target_server_match_self_name(self):
        """Test method on entries where one cites 'self',
        other cites self_name
        """
        servers, entries, db = self.db_setup()
        a, b = self.generate_entries("jake@adventure.time", "self")
        a["origin_server"] = "1"
        b["origin_server"] = "2"
        assign_address(1, "finn@adventure.time", True, servers)
        assign_address(2, "jake@adventure.time", True, servers)
        assert target_server_match(a, b, servers)


    def test_target_server_match_IP_no_match(self):
        """Test method on entries where one cites 'self',
        other cites incorrect network_name"""
        servers, entries, db = self.db_setup()
        a, b = self.generate_entries("self", "4.4.4.4")
        a["origin_server"] = "1"
        b["origin_server"] = "2"
        assign_address(1, "1.1.1.1", False, servers)
        assign_address(2, "2.2.2.2", False, servers)
        assert not target_server_match(a, b, servers)


    def test_target_server_match_self_name_no_match(self):
        """Test method on entries where one cites 'self',
        other cites incorrect network_name
        """
        servers, entries, db = self.db_setup()
        a, b = self.generate_entries("self", "marcelene@adventure.time")
        a["origin_server"] = "1"
        b["origin_server"] = "2"
        assign_address(1, "iceking@adventure.time", False, servers)
        assign_address(2, "bubblegum@adventure.time", False, servers)
        assert not target_server_match(a, b, servers)


    def test_target_server_match_unknown_network_name(self):
        """Test method on entries where one cites 'self',
        other cites first server's true IP, but IP is not yet
        recorded in the .servers collection
        """
        servers, entries, db = self.db_setup()
        a, b = self.generate_entries("self", "1.1.1.1")
        a["origin_server"] = "1"
        b["origin_server"] = "2"
        assign_address(1, "unknown", False, servers)
        assign_address(2, "2.2.2.2", False, servers)
        assert target_server_match(a, b, servers)


    def test_target_server_match_unknown_self_name(self):
        """Test method on entries where one cites 'self',
        other cites first server's true self_name, but
        self_name is not yet recorded in the .servers collection
        """
        servers, entries, db = self.db_setup()
        a, b = self.generate_entries("treetrunks@adventure.time", "self")
        a["origin_server"] = "1"
        b["origin_server"] = "2"
        assign_address(1, "LSP@adventure.time", True, servers)
        assign_address(2, "unknown", True, servers)
        assert target_server_match(a, b, servers)


    # add some tests for the way that next_event handles
    # certain types of entries, namely "conn", "sync", and "fsync"

    # add some tests for generate_summary()

    # -------------------------------------
    # test the resolve_dissenters() method
    # -------------------------------------

    def test_resolve_dissenters_no_lag(self):
        """Test on a list of events where there
        were no problems due to excessive network delay
        or skewed clocks"""
        e1 = self.one_event("status", "finn@adventure.time", datetime.now())
        e2 = self.one_event("status", "me@10.gen", datetime.now())
        e3 = self.one_event("status", "you@10.gen", datetime.now())
        e1["dissenters"] = []
        e2["dissenters"] = []
        e3["dissenters"] = []
        e1["witnesses"] = ["1", "2", "3"]
        e2["witnesses"] = ["1", "2", "3"]
        e3["witnesses"] = ["1", "2", "3"]
        events = [e1, e2, e3]
        events2 = resolve_dissenters(deepcopy(events))
        assert events2 == events


    def test_resolve_dissenters_empty_list(self):
        """Test resolve_dissenters() on an empty
        list of events"""
        events = []
        assert not resolve_dissenters(events)


    def test_resolve_dissenters_two_matching(self):
        """Test resolve_dissenters() on a list
        of two events that do correspond, but were
        separated in time for next_event()"""
        date = datetime.now()
        e1 = self.one_event("status", "finn@adventure.time", date)
        e2 = self.one_event("status", "finn@adventure.time",
                       date + timedelta(seconds=5))
        e1["dissenters"] = ["2"]
        e1["witnesses"] = ["1"]
        e2["dissenters"] = ["1"]
        e2["witnesses"] = ["2"]
        events = [e1, e2]
        events = resolve_dissenters(events)
        assert len(events) == 1
        e = events.pop(0)
        assert e
        assert not e["dissenters"]
        assert e["witnesses"]
        assert len(e["witnesses"]) == 2
        assert "1" in e["witnesses"]
        assert "2" in e["witnesses"]
        assert e["date"] == date + timedelta(seconds=5)


    def test_resolve_dissenters_three_servers(self):
        """Test two events from three different servers,
        with one at a lag"""
        date = datetime.now()
        e1 = self.one_event("status", "finn@adventure.time", date)
        e2 = self.one_event("status", "finn@adventure.time",
                       date + timedelta(seconds=5))
        e1["dissenters"] = ["2"]
        e1["witnesses"] = ["1", "3"]
        e2["dissenters"] = ["1", "3"]
        e2["witnesses"] = ["2"]
        events = [e1, e2]
        events = resolve_dissenters(events)
        assert len(events) == 1
        e = events.pop(0)
        assert e
        assert not e["dissenters"]
        assert e["witnesses"]
        assert len(e["witnesses"]) == 3
        assert "1" in e["witnesses"]
        assert "2" in e["witnesses"]
        assert "3" in e["witnesses"]
        assert e["date"] == date


    def test_resolve_dissenters_five_servers(self):
        """Test events from five servers, three on one
        event, and two on a later event"""
        date = datetime.now()
        e1 = self.one_event("status", "finn@adventure.time", date)
        e2 = self.one_event("status", "finn@adventure.time",
                       date + timedelta(seconds=5))
        e2["dissenters"] = ["4", "5"]
        e2["witnesses"] = ["1", "2", "3"]
        e1["dissenters"] = ["1", "2", "3"]
        e1["witnesses"] = ["4", "5"]
        events = [e1, e2]
        events = resolve_dissenters(events)
        assert len(events) == 1
        e = events.pop(0)
        assert e
        assert not e["dissenters"]
        assert e["witnesses"]
        assert len(e["witnesses"]) == 5
        assert "1" in e["witnesses"]
        assert "2" in e["witnesses"]
        assert "3" in e["witnesses"]
        assert "4" in e["witnesses"]
        assert "5" in e["witnesses"]
        assert e["date"] == date + timedelta(seconds=5)


    def test_resolve_dissenters_same_witnesses_no_match(self):
        """Test a case where events have corresponding
        lists of witnesses and dissenters, but the events
        themselves are not a match"""
        pass


    def test_resolve_dissenters_same_event_overlapping_viewers(self):
        """Test a case where events correspond, but lists
        of witnesses and dissenters do not"""
        pass


    def test_resolve_dissenters_one_skew_in_list(self):
        """Test a list where one event must be resolved,
        but there are also many other events in the list
        that should remain unchanged by resolve_dissenters()"""
        pass

if __name__ == '__main__':
    unittest.main()
