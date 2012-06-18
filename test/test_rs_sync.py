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
    assert criteria("[rsSync] replSet syncing to:") == 1
    return


def test_process():
    date = datetime.now()
    assert process("Mon Jun 11 15:56:16 [rsStart] replSet localhost:27018", date) == None
    assert process("Mon Jun 11 15:56:18 [rsHealthPoll] replSet member localhost:27019 is up", date) == None
    check_state("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017", "localhost:27017")
    check_state("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: 10.4.3.56:45456", "10.4.3.56:45456")
    check_state("[rsSync] syncing to: 10.4.3.56:45456", "10.4.3.56:45456")


def test_syncing_diff():

    currTime = datetime.now()
    test = syncing_diff("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017", process("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017", currTime))
    assert test
    assert test["type"] == 'sync'


def check_state(message, server):
    date = datetime.now()
    doc = process(message, date)
    assert doc["type"] == "sync"
    assert doc["info"]["subtype"] == "reSyncing"
    #print 'Server number is: *{0}*, testing against, *{1}*'.format(doc["info"]["server"], server)
    assert doc["info"]["server"] == server
