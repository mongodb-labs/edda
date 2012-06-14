import datetime
from logl.modules.rsSync import *

def test_criteria():
    assert criteria("Tue Jun 12 13:08:47 [rsSync] replSet syncing to: localhost:27017") == 1
    assert criteria("Tue Jun 12 13:08:47 [rsSync] replSet to: localhost:27017") == -1

def test_process():
	pass

def test_syncingDiff():
    pass
