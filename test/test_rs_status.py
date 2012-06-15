from logl.filters.rs_status import *
from datetime import datetime


def test_criteria():
    """test the criteria() method of this module"""
    # invalid messages
    assert criteria("this is an invalid message") < 0
    assert criteria("I am the primary") < 0
    assert criteria("I am the secondary") < 0
    assert criteria("the server is down") < 0
    assert criteria("the server is back up") < 0
    # check for proper return codes
    assert criteria("Mon Jun 11 15:56:16 [rsStart] replSet I am localhost:27018") == 0
    assert criteria("Mon Jun 11 15:57:04 [rsMgr] replSet PRIMARY") == 1
    assert criteria("Mon Jun 11 15:56:16 [rsSync] replSet SECONDARY") == 2
    assert criteria("Mon Jun 11 15:56:16 [rsStart] replSet STARTUP2") == 5
    assert criteria("Mon Jun 11 15:56:18 [rsHealthPoll] replSet member localhost:27019 is now in state ARBITER") == 7
    assert criteria("Mon Jun 11 15:56:58 [rsHealthPoll] replSet member localhost:27017 is now in state DOWN") == 8
    return


def test_process():
    """test the process() method of this module"""
    date = datetime.now()
    # invalid lines
    assert process("Mon Jun 11 15:56:16 [rsStart] replSet localhost:27018", date) == None
    assert process("Mon Jun 11 15:56:18 [rsHealthPoll] replSet member localhost:27019 is up", date) == None
    # STARTUP1
    doc = process("Mon Jun 11 15:56:16 [rsStart] replSet I am localhost:27018", date)
    assert doc["type"] == "status"
    assert doc["info"]["state_code"] == 0
    assert doc["info"]["state"] == "STARTUP1"
    print doc["info"]["server"]
    assert doc["info"]["server"] == "localhost:27018"
    # PRIMARY
    doc = process("Mon Jun 11 15:57:04 [rsMgr] replSet PRIMARY", date)
    assert doc["type"] == "status"
    assert doc["info"]["state_code"] == 1
    assert doc["info"]["state"] == "PRIMARY"
    assert doc["info"]["server"] == "self"
    # SECONDARY
    doc = process("Mon Jun 11 15:56:16 [rsSync] replSet SECONDARY", date)
    assert doc["type"] == "status"
    assert doc["info"]["state_code"] == 2
    assert doc["info"]["state"] == "SECONDARY"
    assert doc["info"]["server"] == "self"
    # STARTUP2
    doc = process("Mon Jun 11 15:56:16 [rsStart] replSet STARTUP2", date)
    assert doc["type"] == "status"
    assert doc["info"]["state_code"] == 5
    assert doc["info"]["state"] == "STARTUP2"
    assert doc["info"]["server"] == "self"
    # ARBITER
    doc = process("Mon Jun 11 15:56:18 [rsHealthPoll] replSet member localhost:27019 is now in state ARBITER", date)
    assert doc["type"] == "status"
    assert doc["info"]["state_code"] == 7
    assert doc["info"]["state"] == "ARBITER"
    assert doc["info"]["server"] == "localhost:27019"
    # DOWN
    doc = process("Mon Jun 11 15:56:58 [rsHealthPoll] replSet member localhost:27017 is now in state DOWN", date)
    assert doc["type"] == "status"
    assert doc["info"]["state_code"] == 8
    assert doc["info"]["state"] == "DOWN"
    assert doc["info"]["server"] == "localhost:27017"
