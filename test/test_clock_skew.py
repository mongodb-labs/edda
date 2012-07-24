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

import unittest
from edda.post.clock_skew import *
from edda.run_edda import assign_address
import pymongo
from datetime import datetime
from pymongo import Connection
from time import sleep
from nose.plugins.skip import Skip, SkipTest


class test_clock_skew(unittest.TestCase):
    def db_setup(self):
        """Set up a database for use by tests"""
        c = Connection()
        db = c["test"]
        servers = db["wildcats.servers"]
        entries = db["wildcats.entries"]
        clock_skew = db["wildcats.clock_skew"]
        db.drop_collection(servers)
        db.drop_collection(entries)
        db.drop_collection(clock_skew)
        return [servers, entries, clock_skew, db]


    def test_clock_skew_none(self):
        """Test on an empty db"""
        servers, entries, clock_skew, db = self.db_setup()
        server_clock_skew(db, "wildcats")
        cursor = clock_skew.find()
        assert cursor.count() == 0


    def test_clock_skew_one(self):
        """DB with entries from one server"""
        servers, entries, clock_skew, db = self.db_setup()
        assign_address(1, "Sam", False, servers)
        entries.insert(self.generate_doc(
                "status", "Sam", "STARTUP2", 5, "Gaya", datetime.now()))
        entries.insert(self.generate_doc(
                "status", "Sam", "PRIMARY", 1, "self", datetime.now()))
        server_clock_skew(db, "wildcats")
        doc = db["wildcats.clock_skew"].find_one()
        assert doc
        assert doc["server_num"] == "1"
        assert not doc["partners"]


    def test_clock_skew_two(self):
        """Two different servers"""
        servers, entries, clock_skew, db = self.db_setup()
        # fill in some servers
        assign_address(1, "Sam", False, servers)
        assign_address(2, "Nuni", False, servers)
        # fill in some entries
        entries.insert(self.generate_doc(
                "status", "Sam", "SECONDARY", 2, "Nuni", datetime.now()))
        entries.insert(self.generate_doc(
                "status", "Sam", "DOWN", 8, "Nuni", datetime.now()))
        entries.insert(self.generate_doc(
                "status", "Sam", "STARTUP2", 5, "Nuni", datetime.now()))
        sleep(3)
        entries.insert(self.generate_doc(
                "status", "Nuni", "SECONDARY", 2, "self", datetime.now()))
        entries.insert(self.generate_doc(
                "status", "Nuni", "DOWN", 8, "self", datetime.now()))
        entries.insert(self.generate_doc(
                "status", "Nuni", "STARTUP2", 5, "self", datetime.now()))
        server_clock_skew(db, "wildcats")
        cursor = clock_skew.find()
        assert cursor.count() == 2
        # check first server entry
        doc = clock_skew.find_one({"server_num" : "1"})
        assert doc
        assert doc["type"] == "clock_skew"
        assert doc["partners"]
        assert doc["partners"]["2"]
        assert len(doc["partners"]["2"]) == 1
        assert not "1" in doc["partners"]
        t1, wt1 = doc["partners"]["2"].popitem()
        t1 = int(t1)
        assert abs(abs(t1) - 3) < .01
        assert t1 > 0
        assert wt1 == 6
        # check second server entry
        doc2 = clock_skew.find_one({"server_num" : "2"})
        assert doc2
        assert doc2["type"] == "clock_skew"
        assert doc2["partners"]
        assert doc2["partners"]["1"]
        assert len(doc2["partners"]["1"]) == 1
        assert not "2" in doc2["partners"]
        t2, wt2 = doc2["partners"]["1"].popitem()
        t2 = int(t2)
        assert abs(abs(t2) - 3) < .01
        assert t2 < 0
        assert wt2 == 6
        # compare entries against each other
        assert abs(t1) == abs(t2)
        assert t1 == -t2


    def test_clock_skew_three(self):
        """Test on a db that contains entries from
        three different servers
        """
        pass



    def test_detect_simple(self):
        """A simple test of the detect() method in post.py"""
        servers, entries, clock_skew, db = self.db_setup()
        # fill in some servers
        assign_address(1, "Erica", False, servers)
        assign_address(2, "Alison", False, servers)
        # fill in some entries
        entries.insert(self.generate_doc(
            "status", "Erica", "STARTUP2", 5, "Alison", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Erica", "SECONDARY", 2, "Alison", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Erica", "PRIMARY", 1, "Alison", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Erica", "PRIMARY", 1, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Erica", "SECONDARY", 2, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Erica", "DOWN", 8, "self", datetime.now()))
        # wait for a bit (skew the clocks)
        sleep(3)
        # fill in more entries
        entries.insert(self.generate_doc(
            "status", "Alison", "STARTUP2", 5, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Alison", "SECONDARY", 2, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Alison", "PRIMARY", 1, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Alison", "PRIMARY", 1, "Erica", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Alison", "SECONDARY", 2, "Erica", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Alison", "DOWN", 8, "Erica", datetime.now()))
        # check a - b
        skews1 = detect("Erica", "Alison", db, "wildcats")
        assert skews1
        assert len(skews1) == 1
        t1, wt1 = skews1.popitem()
        t1 = int(t1)
        assert t1
        assert -.01 < (abs(t1) - 3) < .01
        assert t1 > 0
        # check b - a
        skews2 = detect("Alison", "Erica", db, "wildcats")
        assert skews2
        assert len(skews2) == 1
        t2, wt2 = skews2.popitem()
        t2 = int(t2)
        assert t2
        assert t2 < 0
        assert abs(abs(t2) - 3) < .01
        # compare runs against each other
        assert abs(t1) == abs(t2)
        assert t1 == -t2
        assert wt1 == wt2
        assert wt1 == 6


    def test_detect_a_has_more(self):
        """Test the scenario where server a has more
        entries about b than b has about itself
        """
        servers, entries, clock_skew, db = self.db_setup()
        # fill in some servers
        assign_address(1, "Erica", False, servers)
        assign_address(2, "Alison", False, servers)
        # fill in some entries
        entries.insert(self.generate_doc(
            "status", "Erica", "STARTUP2", 5, "Alison", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Erica", "SECONDARY", 2, "Alison", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Erica", "PRIMARY", 1, "Alison", datetime.now()))
        # wait for a bit (skew the clocks)
        sleep(3)
        # fill in more entries
        entries.insert(self.generate_doc(
            "status", "Alison", "SECONDARY", 2, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Alison", "PRIMARY", 1, "self", datetime.now()))
        # first pair doesn't match
        skews1 = detect("Erica", "Alison", db, "wildcats")
        assert skews1
        assert len(skews1) == 1
        t1, wt1 = skews1.popitem()
        t1 = int(t1)
        assert t1
        assert wt1
        assert wt1 == 3
        assert abs(abs(t1) - 3) < .01
        # replace some entries
        entries.remove(
            {"origin_server": "Alison"})
        entries.insert(self.generate_doc(
            "status", "Alison", "STARTUP2", 5, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Alison", "STARTUP2", 5, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Alison", "SECONDARY", 2, "self", datetime.now()))
        # second pair doesn't match
        skews2 = detect("Erica", "Alison", db, "wildcats")
        assert skews2
        assert len(skews2) == 1
        assert in_skews(3, skews2)
        assert skews2['3'] == 4


    def test_detect_b_has_more(self):
        """Test the case where server b has more
        entries about itself than server a has about b
        """
        pass


    def test_two_different_skews(self):
        """Test the case where corresponding entries
        are skewed randomly in time
        """
        # only tests a-b, not b-a
        servers, entries, clock_skew, db = self.db_setup()
        # fill in some servers
        assign_address(1, "Hannah", False, servers)
        assign_address(2, "Mel", False, servers)
        # these are skewed by 3 seconds
        entries.insert(self.generate_doc(
            "status", "Hannah", "PRIMARY", 1, "Mel", datetime.now()))
        sleep(3)
        entries.insert(self.generate_doc(
            "status", "Mel", "PRIMARY", 1, "self", datetime.now()))
        # one other message to break the matching pattern
        sleep(2)
        entries.insert(self.generate_doc(
            "status", "Hannah", "ARBITER", 7, "Mel", datetime.now()))
        sleep(2)
        # these are skewed by 5 seconds
        entries.insert(self.generate_doc(
            "status", "Hannah", "SECONDARY", 2, "Mel", datetime.now()))
        sleep(5)
        entries.insert(self.generate_doc(
            "status", "Mel", "SECONDARY", 2, "self", datetime.now()))
        skews = detect("Hannah", "Mel", db, "wildcats")
        assert skews
        assert len(skews) == 2
        assert in_skews(5, skews)
        assert skews['5'] == 1
        assert in_skews(3, skews)
        assert skews['3'] == 1


    def test_detect_zero_skew(self):
        """Test the case where there is no clock skew."""
        servers, entries, clock_skew, db = self.db_setup()
        # fill in some servers
        assign_address(1, "Sam", False, servers)
        assign_address(2, "Gaya", False, servers)
        # fill in some entries (a - b)
        entries.insert(self.generate_doc(
            "status", "Sam", "STARTUP2", 5, "Gaya", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Gaya", "STARTUP2", 5, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Sam", "ARBITER", 7, "Gaya", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Gaya", "ARBITER", 7, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Sam", "DOWN", 8, "Gaya", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Gaya", "DOWN", 8, "self", datetime.now()))
        # fill in some entries (b - a)
        entries.insert(self.generate_doc(
            "status", "Gaya", "STARTUP2", 5, "Sam", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Sam", "STARTUP2", 5, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Gaya", "STARTUP2", 5, "Sam", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Sam", "STARTUP2", 5, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Gaya", "STARTUP2", 5, "Sam", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Sam", "STARTUP2", 5, "self", datetime.now()))
        skews1 = detect("Sam", "Gaya", db, "wildcats")
        skews2 = detect("Gaya", "Sam", db, "wildcats")
        assert not skews1
        assert not skews2


    def test_detect_network_delay(self):
        """Test the case where there are time differences
        too small to be considered clock skew
        """
        servers, entries, clock_skew, db = self.db_setup()
        # fill in some servers
        assign_address(1, "Erica", False, servers)
        assign_address(2, "Alison", False, servers)
        # fill in some entries
        entries.insert(self.generate_doc(
            "status", "Erica", "STARTUP2", 5, "Alison", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Erica", "SECONDARY", 2, "Alison", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Erica", "PRIMARY", 1, "Alison", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Erica", "PRIMARY", 1, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Erica", "SECONDARY", 2, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Erica", "DOWN", 8, "self", datetime.now()))
        # wait for a bit (skew the clocks)
        sleep(1)
        # fill in more entries
        entries.insert(self.generate_doc(
            "status", "Alison", "STARTUP2", 5, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Alison", "SECONDARY", 2, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Alison", "PRIMARY", 1, "self", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Alison", "PRIMARY", 1, "Erica", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Alison", "SECONDARY", 2, "Erica", datetime.now()))
        entries.insert(self.generate_doc(
            "status", "Alison", "DOWN", 8, "Erica", datetime.now()))
        # run detect()!
        skews1 = detect("Erica", "Alison", db, "wildcats")
        skews2 = detect("Alison", "Erica", db, "wildcats")
        assert not skews1
        assert not skews2


    def generate_doc(self, d_type, server, label, code, target, date):
        """Generate an entry"""
        doc = {}
        doc["type"] = d_type
        doc["origin_server"] = server
        doc["info"] = {}
        doc["info"]["state"] = label
        doc["info"]["state_code"] = code
        doc["info"]["server"] = target
        doc["date"] = date
        return doc


    def test_clock_skew_doc(self):
        """Simple tests of the clock_skew_doc() method
        in post.py"""
        doc = clock_skew_doc("6")
        assert doc
        assert doc["server_num"] == "6"
        assert doc["type"] == "clock_skew"

if __name__ == '__main__':
    unittest.main()
