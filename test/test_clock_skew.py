from logl.post.clock_skew import *
from logl.logl import new_server
import pymongo
from datetime import datetime
from pymongo import Connection
from time import sleep

def test_server_clock_skew():
    pass


def test_detect_simple():
    """A simple test of the detect() method in post.py"""
    c = Connection()
    db = c["test"]
    servers = db["wildcats.servers"]
    entries = db["wildcats.entries"]
    # fill in some servers
    servers.insert(new_server(1, "Erica"))
    servers.insert(new_server(2, "Alison"))
    # fill in some entries
    entries.insert(generate_doc("status", "Erica", "STARTUP2", 5, "Alison", datetime.now()))
    entries.insert(generate_doc("status", "Erica", "SECONDARY", 2, "Alison", datetime.now()))
    entries.insert(generate_doc("status", "Erica", "PRIMARY", 1, "Alison", datetime.now()))
    # wait for a bit (skew the clocks)
    sleep(10)
    # fill in more entries
    entries.insert(generate_doc("status", "Alison", "STARTUP2", 5, "self", datetime.now()))
    entries.insert(generate_doc("status", "Alison", "SECONDARY", 2, "self", datetime.now()))
    entries.insert(generate_doc("status", "Alison", "PRIMARY", 1, "self", datetime.now()))
    # run detect()!
    t1 = detect("Erica", "Alison", db, "wildcats")
    assert t1
    assert abs(abs(t1) - timedelta(seconds=10)) < timedelta(seconds=2)
    t2 = detect("Alison", "Erica", db, "wildcats")
    assert t2
    assert abs(abs(t2) - timedelta(seconds=10)) < timedelta(seconds=2)
    assert abs(t1) == abs(t2)
    # once sign convention is established:
    # assert t1 == -t2

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


def test_clock_skew_doc():
    """Simple tests of the clock_skew_doc() method
    in post.py"""
    doc = clock_skew_doc("Samantha")
    assert doc
    assert doc["server_name"] == "Samantha"
    assert doc["type"] == "clock_skew"
    pass


def test_server_matchup():
    pass
