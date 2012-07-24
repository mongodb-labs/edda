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

import unittest #organizing servers uses the supporting methods module and is going to have the same import problem that replacing clock skew has. TO BE FIXED.
from edda.post.event_matchup import organize_servers
from edda.run_edda import assign_address
import pymongo
import logging
from datetime import *
from pymongo import Connection
from time import sleep
from nose.plugins.skip import Skip, SkipTest


class test_organizing_servers(unittest.TestCase):
    def db_setup(self):
        """Set up a database for use by tests"""
        c = Connection()
        db = c["test"]
        servers = db["fruit.servers"]
        entries = db["fruit.entries"]
        clock_skew = db["fruit.clock_skew"]
        db.drop_collection(servers)
        db.drop_collection(entries)
        db.drop_collection(clock_skew)
        return [servers, entries, clock_skew, db]


    def test_organize_two_servers(self):
        logger = logging.getLogger(__name__)
        servers, entries, clock_skew, db = self.db_setup()
        original_date = datetime.now()

        entries.insert(self.generate_doc(
            "status", "apple", "STARTUP2", 5, "pear", original_date))
        entries.insert(self.generate_doc("status", "pear", "STARTUP2"
            "", 5, "apple", original_date + timedelta(seconds=5)))

        assign_address(self, 1, "apple", servers)
        assign_address(self, 2, "pear", servers)

        organized_servers = organize_servers(db, "fruit")
        logger.debug("Organized servers Printing: {}".format(organized_servers))
        for server_name in organized_servers:
            logger.debug("Server Name: {}".format(server_name))
            for item in organized_servers[server_name]:
                logger.debug("Item list: {}".format(item))
                logger.debug("Item: {}".format(item))
                assert item


    def test_organizing_three_servers(self):
        servers, entries, clock_skew, db = self.db_setup()
        logger = logging.getLogger(__name__)
        original_date = datetime.now()

        entries.insert(self.generate_doc(
            "status", "apple", "STARTUP2", 5, "pear", original_date))
        entries.insert(self.generate_doc("status", "apple", "STARTUP2"
            "", 5, "pear", original_date + timedelta(seconds=14)))
        entries.insert(self.generate_doc("status", "pear", "STARTUP2"
            "", 5, "apple", original_date + timedelta(seconds=5)))
        entries.insert(self.generate_doc("status", "pear", "STARTUP2"
            "", 5, "apple", original_date + timedelta(seconds=15)))
        entries.insert(self.generate_doc("status", "plum", "STARTUP2"
            "", 5, "apple", original_date + timedelta(seconds=9)))
        entries.insert(self.generate_doc("status", "plum", "STARTUP2"
            "", 5, "apple", original_date + timedelta(seconds=11)))

        servers.insert(self.generate_server_doc(
            "status", "plum", "STARTUP2", 5, "apple", original_date))
        servers.insert(self.generate_server_doc("status", "apple", "STARTUP2"
            "", 5, "plum", original_date + timedelta(seconds=9)))
        servers.insert(self.generate_server_doc("status", "pear", "STARTUP2"
            "", 5, "apple", original_date + timedelta(seconds=6)))

        organized_servers = organize_servers(db, "fruit")
        logger.debug("Organized servers Printing: {}".format(organized_servers))
        for server_name in organized_servers:
            logger.debug("Server Name: {}".format(server_name))
            first = True
            for item in organized_servers[server_name]:
                logger.debug("Item list: {}".format(item))
                if first:
                    past_date = item["date"]
                    first = False
                    continue
                current_date = item["date"]
                assert past_date <= current_date
                past_date = current_date

                #ogger.debug("Item: {}".format(item))


    def test_organize_same_times(self):
        servers, entries, clock_skew, db = self.db_setup()
        logger = logging.getLogger(__name__)
        original_date = datetime.now()

        entries.insert(self.generate_doc(
            "status", "apple", "STARTUP2", 5, "pear", original_date))
        entries.insert(self.generate_doc(
            "status", "apple", "STARTUP2", 5, "pear", original_date))
        entries.insert(self.generate_doc(
            "status", "pear", "STARTUP2", 5, "apple", original_date))
        entries.insert(self.generate_doc(
            "status", "pear", "STARTUP2", 5, "apple", original_date))
        entries.insert(self.generate_doc(
            "status", "plum", "STARTUP2", 5, "apple", original_date))
        entries.insert(self.generate_doc(
            "status", "plum", "STARTUP2", 5, "apple", original_date))

        servers.insert(self.generate_server_doc(
            "status", "plum", "STARTUP2", 5, "apple", original_date))
        servers.insert(self.generate_server_doc(
            "status", "apple", "STARTUP2", 5, "plum", original_date))
        servers.insert(self.generate_server_doc(
            "status", "pear", "STARTUP2", 5, "apple", original_date))

        organized_servers = organize_servers(db, "fruit")
        logger.debug("Organized servers Printing: {}".format(organized_servers))
        for server_name in organized_servers:
            logger.debug("Server Name: {}".format(server_name))
            first = True
            for item in organized_servers[server_name]:
                logger.debug("Item list: {}".format(item))
                if first:
                    past_date = item["date"]
                    first = False
                    continue
                current_date = item["date"]
                assert past_date <= current_date
                past_date = current_date


    def generate_doc(self, type, server, label, code, target, date):
        """Generate an entry"""
        doc = {}
        doc["type"] = type
        doc["origin_server"] = server
        doc["info"] = {}
        doc["info"]["state"] = label
        doc["info"]["state_code"] = code
        doc["info"]["server"] = target
        doc["date"] = date
        return doc


    def generate_server_doc(self, type, server, label, code, target, date):
        """Generate an entry"""
        doc = {}
        doc["type"] = type
        doc["server_num"] = server
        doc["origin_server"] = server
        doc["info"] = {}
        doc["info"]["state"] = label
        doc["info"]["state_code"] = code
        doc["info"]["server"] = target
        doc["date"] = date
        return doc

if __name__ == '__main__':
    unittest.main()

