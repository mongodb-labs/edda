from datetime import datetime
from logl.modules.rsSync import *

def test_criteria():
    assert criteria("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017") == 1
    assert criteria("Tue Jun 12 13:08:47 [rsSync] replSet to: localhost:27017") == -1

def test_process():

    doc =  process("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017", datetime.now())
    assert doc
    assert doc["type"] == 'sync'
    assert process("This should fail", datetime.now()) == None


def test_syncingDiff():

    currTime = datetime.now()
    test = syncingDiff("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017", 
    	process("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017", currTime))
    assert test
    assert test["type"] == 'sync'
    assert syncingDiff("This should fail", datetime.now()) == test
