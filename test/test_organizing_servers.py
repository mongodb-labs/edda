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



from logl.post.organize_servers import *
from logl.logl import new_server
import pymongo
import logging
from datetime import datetime
from pymongo import Connection
from time import sleep
from nose.plugins.skip import Skip, SkipTest


def db_setup():
    logger = logging.getLogger(__name__)
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

def test_organize_two_servers():
    logger = logging.getLogger(__name__)
    servers, entries, clock_skew, db = db_setup()
    original_date = datetime.now()

    entries.insert(generate_doc("status", "apple", "STARTUP2", 5, "pear", original_date))
    entries.insert(generate_doc("status", "pear", "STARTUP2", 5, "apple", original_date + timedelta(seconds=0)))

    servers.insert(generate_doc("status", "apple", "STARTUP2", 5, "pear", original_date))
    servers.insert(generate_doc("status", "pear", "STARTUP2", 5, "apple", original_date + timedelta(seconds=0)))

    organized_servers = organize_servers(db, "fruit")

    for server_name in organized_servers:
        for item in server_name:
            assert item


def generate_doc(type, server, label, code, target, date):
    logger = logging.getLogger(__name__)
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


