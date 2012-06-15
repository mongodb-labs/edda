from datetime import datetime
from logl.filters.rs_sync import *


def test_criteria():
    assert criteria("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017") == 1
    #should fail, absence of word "syncing": malformed message
    assert criteria("Tue Jun 12 13:08:47 [rsSync] replSet to: localhost:27017") == -1
    #should fail, absence of [rsSync]: malformed message
    assert criteria("Tue Jun 12 13:08:47 replSet to: localhost:27017") == -1
    #should pass, it doesn't test to see if there is a valid port number until test_syncingDiff: malformed message to fail at another point
    assert criteria("Tue Jun 12 13:08:47 [rsSync] replSet syncing to:") == 1
    #should pass in this situation, date is irrevealant
    assert criteria("[rsSync] replSet syncing to: localhost:27017") == 1
    #foo bar test from git
    assert criteria("foo bar") == -1

def test_process():

    doc = process("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017", datetime.now())
    assert doc
    assert doc["type"] == 'sync'
    assert process("This should fail", datetime.now()) == None


def test_syncingDiff():

    currTime = datetime.now()
    test = syncingDiff("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017", process("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017", currTime))
    assert test
    assert test["type"] == 'sync'

