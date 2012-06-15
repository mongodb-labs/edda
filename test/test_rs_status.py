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
    assert criteria("replSet RECOVERING") == 3
    assert criteria("replSet encountered a FATAL ERROR") == 4
    assert criteria("Mon Jun 11 15:56:16 [rsStart] replSet STARTUP2") == 5
    assert criteria("replSet member is now in state UNKNOWN") == 6
    assert criteria("Mon Jun 11 15:56:18 [rsHealthPoll] replSet member localhost:27019 is now in state ARBITER") == 7
    assert criteria("Mon Jun 11 15:56:58 [rsHealthPoll] replSet member localhost:27017 is now in state DOWN") == 8
    assert criteria("replSet member is now in state ROLLBACK") == 9
    assert criteria("replSet member is now in state REMOVED") == 10
    return


def test_process():
    """test the process() method of this module"""
    date = datetime.now()
    # invalid lines
    assert process("Mon Jun 11 15:56:16 [rsStart] replSet localhost:27018", date) == None
    assert process("Mon Jun 11 15:56:18 [rsHealthPoll] replSet member localhost:27019 is up", date) == None
    # valid lines
    check_state("Mon Jun 11 15:56:16 [rsStart] replSet I am localhost:27018", "STARTUP1", 0, "localhost:27018")
    check_state("[rsMgr] replSet PRIMARY", "PRIMARY", 1, "self")
    check_state("[rsSync] replSet SECONDARY", "SECONDARY", 2, "self")
    check_state("[rsSync] replSet is RECOVERING", "RECOVERING", 3, "self")
    check_state("[rsSync] replSet member encountered FATAL ERROR", "FATAL", 4, "self")
    check_state("[rsStart] replSet STARTUP2", "STARTUP2", 5, "self")
    check_state("[rsSync] replSet member 10.4.3.56:45456 is now in state UNKNOWN", "UNKNOWN", 6, "10.4.3.56:45456")
    check_state("[rsHealthPoll] replSet member localhost:27019 is now in state ARBITER", "ARBITER", 7, "localhost:27019")
    check_state("[rsHealthPoll] replSet member localhost:27017 is now in state DOWN", "DOWN", 8, "localhost:27017")
    check_state("[rsSync] replSet member example@domain.com:22234 is now in state ROLLBACK", "ROLLBACK", 9, "example@domain.com:22234")
    check_state("[rsSync] replSet member my-MacBook-pro:43429 has been REMOVED", "REMOVED", 10, "my-MacBook-pro:43429")


def check_state(msg, state, code, server):
    date = datetime.now()
    doc = process(msg, date)
    assert doc["type"] == "status"
    assert doc["info"]["state_code"] == code
    assert doc["info"]["state"] == state
    assert doc["info"]["server"] == server
