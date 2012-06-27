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


from logl.post.replace_clock_skew import *
from logl.logl import new_server
import pymongo
from datetime import datetime
from pymongo import Connection
from time import sleep
from nose.plugins.skip import Skip, SkipTest


def db_setup():
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

def test_replacing_none():
    """"Replaces servers without skews."""""
    #result = db_setup()
    servers, entries, clock_skew, db = db_setup()
    original_date = datetime.now()
    print original_date
    entries.insert(generate_doc("status", "apple", "STARTUP2", 5, "pear", original_date))
    entries.insert(generate_doc("status", "pear", "STARTUP2", 5, "apple", original_date))
    doc1 = generate_cs_doc("pear", "apple")
    doc1["partners"]["apple"]["0"] = 5
    clock_skew.insert(doc1)
    doc1 = generate_cs_doc("apple", "pear")
    doc1["partners"]["pear"]["0"] = 5
    clock_skew.insert(doc1)

    print entries.find()
    fix_clock_skew(db, "fruit")
    print entries.find()
    print clock_skew.find()
    docs = entries.find({"origin_server": "pear"})
    for doc in docs:
        print doc["date"]
        print original_date
        print original_date - doc["date"]
        delta = original_date - doc["date"]
        print repr(delta)
        if delta < timedelta(milliseconds = 1):
            assert  True
            continue
        assert False    
    #assert 4 == 5
    #assert original_date == entries.find().


def test_replacing_one_value():
    result = db_setup()
    servers, entries, clock_skew, db = db_setup()
    skew1 = 5

    original_date = datetime.now()
    entries.insert(generate_doc("status", "apple", "STARTUP2", 5, "pear", original_date))
    entries.insert(generate_doc("status", "pear", "STARTUP2", 5, "apple", original_date))
    doc1 = generate_cs_doc("pear", "apple")
    doc1["partners"]["apple"]["5"] = skew1
    clock_skew.insert(doc1)
    doc1 = generate_cs_doc("apple", "pear")
    doc1["partners"]["pear"]["0"] = -skew1
    clock_skew.insert(doc1)

    clock_skew.insert(doc1)
    fix_clock_skew(db, "fruit")
    print entries.find()
    print clock_skew.find()
    docs = entries.find({"origin_server": "apple"})
    for doc in docs:
        print doc["date"]
        print doc["adjusted_date"]
        delta = abs(original_date - doc["adjusted_date"])
        print repr(delta)
        if delta - timedelta(seconds = skew1) < timedelta(milliseconds = 1):
            assert test_replacing_one_value
            continue
        assert False

def test_replacing_multiple():
    result = db_setup()
    servers, entries, clock_skew, db = db_setup()
    skew = "14"
    neg_skew = "-14"
    weight = 10

    original_date = datetime.now()
    entries.insert(generate_doc("status", "apple", "STARTUP2", 5, "pear", original_date))
    entries.insert(generate_doc("status", "pear", "STARTUP2", 5, "apple", original_date))
    entries.insert(generate_doc("status", "plum", "STARTUP2", 5, "apple", original_date))
    entries.insert(generate_doc("status", "apple", "STARTUP2", 5, "plum", original_date))
    entries.insert(generate_doc("status", "pear", "STARTUP2", 5, "plum", original_date))
    entries.insert(generate_doc("status", "plum", "STARTUP2", 5, "pear", original_date))

    doc1 = generate_cs_doc("pear", "apple")
    doc1["partners"]["apple"][skew] = weight
    doc1["partners"]["plum"] = {}
    doc1["partners"]["plum"][skew] = weight
    clock_skew.insert(doc1)
    doc1 = generate_cs_doc("apple", "pear")
    doc1["partners"]["plum"] = {}
    doc1["partners"]["plum"][skew] = weight
    doc1["partners"]["pear"][neg_skew] = weight
    clock_skew.insert(doc1)
    doc1 = generate_cs_doc("plum", "pear")
    doc1["partners"]["apple"] = {}
    doc1["partners"]["apple"][neg_skew] = weight
    doc1["partners"]["pear"][neg_skew] = weight
    clock_skew.insert(doc1)
    fix_clock_skew(db, "fruit")
    print entries.find()
    print clock_skew.find()
    docs = entries.find({"origin_server": "plum"})
    for doc in docs:
        print doc["date"]
        print doc["adjusted_date"]
        delta = abs(original_date - doc["adjusted_date"])
        print repr(delta)
        if delta - timedelta(seconds=int(skew)) < timedelta(milliseconds=1):
            assert True
            continue
        assert False

    docs = entries.find({"origin_server": "apple"})
    for doc in docs:
        print doc["date"]
        print doc["adjusted_date"]
        delta = abs(original_date - doc["adjusted_date"])
        print repr(delta)
        if delta - timedelta(seconds=int(skew)) < timedelta(milliseconds=1):
            assert True
            continue
        assert False

    docs = entries.find({"origin_server": "pear"})
    
    for doc in docs:
        if not "adjusted_date" in doc:
            assert True
            continue
        assert False

def generate_doc(type, server, label, code, target, date):
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

# anatomy of a clock skew document:
# document = {
#    "type" = "clock_skew"
#    "server_name" = "name"
#    "partners" = {
#          server_name : {
#                "skew_1" : weight,
#                "skew_2" : weight...
#          }
#     }
def generate_cs_doc(name, referal):
    doc = {}
    doc["type"] = "clock_skew"
    doc["server_name"] = name
    doc["partners"] = {}
    doc["partners"][referal] = {}
    return doc
