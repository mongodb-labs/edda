from logl.post.clock_skew import *
from logl.logl import new_server
import pymongo
from datetime import datetime
from pymongo import Connection
from time import sleep


def db_setup():
    """Set up a database for use by tests"""
    c = Connection()
    db = c["test"]
    servers = db["wildcats.servers"]
    entries = db["wildcats.entries"]
    db.drop_collection(servers)
    db.drop_collection(entries)
    return [servers, entries, db]


def test_clock_skew_none():
    """Test on an empty db"""
    result = db_setup()
    db = result[2]
    server_clock_skew(db, "wildcats")
    cursor = db["wildcats.clock_skew"].find()
    assert cursor.count() == 0


def test_clock_skew_one():
    """Test on a db that only contains entries
    from one server"""
    result = db_setup()
    db = result[2]
    entries = result[1]
    result[0].insert(new_server(1, "Sam"))
    entries.insert(generate_doc("status", "Sam", "STARTUP2", 5, "Gaya", datetime.now()))
    entries.insert(generate_doc("status", "Sam", "PRIMARY", 1, "self", datetime.now()))
    server_clock_skew(db, "wildcats")
    cursor = db["wildcats.clock_skew"].find()
    assert cursor.count() == 0


def test_clock_skew_two():
    """Test on a db that contains entries from
    two different servers"""
    result = db_setup()
    servers = result[0]
    entries = result[1]
    db = result[2]
    # fill in some servers
    servers.insert(new_server(1, "Sam"))
    servers.insert(new_server(2, "Nuni"))
    # fill in some entries
    entries.insert(generate_doc("status", "Sam", "SECONDARY", 2, "Nuni", datetime.now()))
    entries.insert(generate_doc("status", "Sam", "DOWN", 8, "Nuni", datetime.now()))
    entries.insert(generate_doc("status", "Sam", "STARTUP2", 5, "Nuni", datetime.now()))
    sleep(3)
    entries.insert(generate_doc("status", "Nuni", "SECONDARY", 2, "self", datetime.now()))
    entries.insert(generate_doc("status", "Nuni", "DOWN", 8, "self", datetime.now()))
    entries.insert(generate_doc("status", "Nuni", "STARTUP2", 5, "self", datetime.now()))
    server_clock_skew(db, "wildcats")
    cursor = db["wildcats.clock_skew"].find()
    assert cursor.count() > 0
    doc = db["wildcats.clock_skew"].find_one({"server" : "Sam"})
    assert doc
    assert doc["type"] == "clock_skew"
    assert doc["partners"]
    assert doc["partners"]["Nuni"]
    assert not doc["partners"]["Sam"]
    # please change once clock_skew stores a list of entries
    t1 = doc["partners"]["Nuni"]
    assert abs(abs(t1) - timedelta(seconds=3)) < timedelta(seconds=.01)
    doc2 = db["wildcats.clock_skew"].find_one({"server" : "Nuni"})
    assert doc2
    assert doc2["type"] == "clock_skew"
    assert doc2["partners"]
    assert doc2["partners"]["Sam"]
    assert not doc2["partners"]["Nuni"]
    t2 = doc2["partners"]["Sam"]
    assert abs(abs(t2) - timedelta(seconds=3)) < timedelta(seconds=.01)
    assert abs(t1) == abs(t2)


def test_clock_skew_three():
    """Test on a db that contains entries from
    three different servers"""
    pass



def test_detect_simple():
    """A simple test of the detect() method in post.py"""
    result = db_setup()
    servers = result[0]
    entries = result[1]
    db = result[2]
    # fill in some servers
    servers.insert(new_server(1, "Erica"))
    servers.insert(new_server(2, "Alison"))
    # fill in some entries
    entries.insert(generate_doc("status", "Erica", "STARTUP2", 5, "Alison", datetime.now()))
    entries.insert(generate_doc("status", "Erica", "SECONDARY", 2, "Alison", datetime.now()))
    entries.insert(generate_doc("status", "Erica", "PRIMARY", 1, "Alison", datetime.now()))
    entries.insert(generate_doc("status", "Erica", "PRIMARY", 1, "self", datetime.now()))
    entries.insert(generate_doc("status", "Erica", "SECONDARY", 2, "self", datetime.now()))
    entries.insert(generate_doc("status", "Erica", "DOWN", 8, "self", datetime.now()))
    # wait for a bit (skew the clocks)
    sleep(10)
    # fill in more entries
    entries.insert(generate_doc("status", "Alison", "STARTUP2", 5, "self", datetime.now()))
    entries.insert(generate_doc("status", "Alison", "SECONDARY", 2, "self", datetime.now()))
    entries.insert(generate_doc("status", "Alison", "PRIMARY", 1, "self", datetime.now()))
    entries.insert(generate_doc("status", "Alison", "PRIMARY", 1, "Erica", datetime.now()))
    entries.insert(generate_doc("status", "Alison", "SECONDARY", 2, "Erica", datetime.now()))
    entries.insert(generate_doc("status", "Alison", "DOWN", 8, "Erica", datetime.now()))
    # run detect()!
    t1 = detect("Erica", "Alison", db, "wildcats")
    assert t1
    print t1
    assert abs(abs(t1) - timedelta(seconds=10)) < timedelta(seconds=2)
    t2 = detect("Alison", "Erica", db, "wildcats")
    assert t2
    print t2
    assert abs(abs(t2) - timedelta(seconds=10)) < timedelta(seconds=.01)
    assert abs(abs(t1) - timedelta(seconds=10)) < timedelta(seconds=.01)
    assert abs(t1) - abs(t2) < timedelta(seconds=.01)
    # once sign convention is established:
    # assert t1 == -t2


def test_detect_a_has_more():
    """Test the scenario where server a has more
    entries about b than b has about itself"""
    result = db_setup()
    servers = result[0]
    entries = result[1]
    db = result[2]
    # fill in some servers
    servers.insert(new_server(1, "Erica"))
    servers.insert(new_server(2, "Alison"))
    # fill in some entries
    entries.insert(generate_doc("status", "Erica", "STARTUP2", 5, "Alison", datetime.now()))
    entries.insert(generate_doc("status", "Erica", "SECONDARY", 2, "Alison", datetime.now()))
    entries.insert(generate_doc("status", "Erica", "PRIMARY", 1, "Alison", datetime.now()))
    # wait for a bit (skew the clocks)
    sleep(4)
    # fill in more entries
    entries.insert(generate_doc("status", "Alison", "SECONDARY", 2, "self", datetime.now()))
    entries.insert(generate_doc("status", "Alison", "PRIMARY", 1, "self", datetime.now()))
    # first pair doesn't match
    t1 = detect("Erica", "Alison", db, "wildcats")
    assert t1
    assert abs(abs(t1) - timedelta(seconds=4)) < timedelta(seconds=.01)
    # replace some entries
    entries.remove({"origin_server" : "Alison"})
    entries.insert(generate_doc("status", "Alison", "STARTUP2", 2, "self", datetime.now()))
    entries.insert(generate_doc("status", "Alison", "STARTUP2", 2, "self", datetime.now()))
    entries.insert(generate_doc("status", "Alison", "SECONDARY", 2, "self", datetime.now()))
    # second pair doesn't match
    t2 = detect("Erica", "Alison", db, "wildcats")
    assert t2


def test_detect_b_has_more():
    """Test the case where server b has more
    entries about itself than server a has about b"""
    pass


def test_detect_random_skew():
    """Test the case where corresponding entries
    are skewed randomly in time"""
    # only tests a-b, not b-a
    result = db_setup()
    servers = result[0]
    entries = result[1]
    # fill in some servers
    servers.insert(new_server(1, "Hannah"))
    servers.insert(new_server(2, "Mel"))
    # these are skewed by 3 seconds
    entries.insert(generate_doc("status", "Hannah", "PRIMARY", 1, "Mel", datetime.now()))
    sleep(3)
    entries.insert(generate_doc("status", "Mel", "PRIMARY", 1, "self", datetime.now()))
    # these are skewed by 5 seconds
    entries.insert(generate_doc("status", "Hannah", "SECONDARY", 2, "Mel", datetime.now()))
    sleep(5)
    entries.insert(generate_doc("status", "Mel", "SECONDARY", 1, "self", datetime.now()))
    # these are skewed by 1 second
    entries.insert(generate_doc("status", "Hannah", "ARBITER", 1, "Mel", datetime.now()))
    sleep(1)
    entries.insert(generate_doc("status", "Hannah", "PRIMARY", 1, "Mel", datetime.now()))
    t1 = detect("Hannah", "Mel", result[2], "wildcats")
    assert not t1


def test_detect_zero_skew():
    """Test the case where there is no clock skew."""
    result = db_setup()
    servers = result[0]
    entries = result[1]
    # fill in some servers
    servers.insert(new_server(1, "Sam"))
    servers.insert(new_server(2, "Gaya"))
    # fill in some entries (a - b)
    entries.insert(generate_doc("status", "Sam", "STARTUP2", 5, "Gaya", datetime.now()))
    entries.insert(generate_doc("status", "Gaya", "STARTUP2", 5, "self", datetime.now()))
    entries.insert(generate_doc("status", "Sam", "ARBITER", 7, "Gaya", datetime.now()))
    entries.insert(generate_doc("status", "Gaya", "ARBITER", 7, "self", datetime.now()))
    entries.insert(generate_doc("status", "Sam", "DOWN", 8, "Gaya", datetime.now()))
    entries.insert(generate_doc("status", "Gaya", "DOWN", 8, "self", datetime.now()))
    # fill in some entries (b - a)
    entries.insert(generate_doc("status", "Gaya", "STARTUP2", 5, "Sam", datetime.now()))
    entries.insert(generate_doc("status", "Sam", "STARTUP2", 5, "self", datetime.now()))
    entries.insert(generate_doc("status", "Gaya", "STARTUP2", 5, "Sam", datetime.now()))
    entries.insert(generate_doc("status", "Sam", "STARTUP2", 5, "self", datetime.now()))
    entries.insert(generate_doc("status", "Gaya", "STARTUP2", 5, "Sam", datetime.now()))
    entries.insert(generate_doc("status", "Sam", "STARTUP2", 5, "self", datetime.now()))
    t1 = detect("Sam", "Gaya", result[2], "wildcats")
    t2 = detect("Gaya", "Sam", result[2], "wildcats")
    assert t1 == t2
    assert t1 == timedelta(0)
    assert t2 == timedelta(0)


def test_detect_network_delay():
    """Test the case where there are time differences
    too small to be considered clock skew"""
    result = db_setup()
    servers = result[0]
    entries = result[1]
    db = result[2]
    # fill in some servers
    servers.insert(new_server(1, "Erica"))
    servers.insert(new_server(2, "Alison"))
    # fill in some entries
    entries.insert(generate_doc("status", "Erica", "STARTUP2", 5, "Alison", datetime.now()))
    entries.insert(generate_doc("status", "Erica", "SECONDARY", 2, "Alison", datetime.now()))
    entries.insert(generate_doc("status", "Erica", "PRIMARY", 1, "Alison", datetime.now()))
    entries.insert(generate_doc("status", "Erica", "PRIMARY", 1, "self", datetime.now()))
    entries.insert(generate_doc("status", "Erica", "SECONDARY", 2, "self", datetime.now()))
    entries.insert(generate_doc("status", "Erica", "DOWN", 8, "self", datetime.now()))
    # wait for a bit (skew the clocks)
    sleep(1)
    # fill in more entries
    entries.insert(generate_doc("status", "Alison", "STARTUP2", 5, "self", datetime.now()))
    entries.insert(generate_doc("status", "Alison", "SECONDARY", 2, "self", datetime.now()))
    entries.insert(generate_doc("status", "Alison", "PRIMARY", 1, "self", datetime.now()))
    entries.insert(generate_doc("status", "Alison", "PRIMARY", 1, "Erica", datetime.now()))
    entries.insert(generate_doc("status", "Alison", "SECONDARY", 2, "Erica", datetime.now()))
    entries.insert(generate_doc("status", "Alison", "DOWN", 8, "Erica", datetime.now()))
    # run detect()!
    t1 = detect("Erica", "Alison", db, "wildcats")
    t2 = detect("Alison", "Erica", db, "wildcats")
    assert not t1
    assert not t2


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
