from logl.modules.initandlisten import *
from datetime import datetime

def test_criteria():
    # these should not pass
    assert criteria("this should not pass") < 0
    assert criteria("Mon Jun 11 15:56:40 [conn5] end connection 127.0.0.1:55224 (2 connections now open)") < 0
    assert criteria("Mon Jun 11 15:56:16 [initandlisten] ** WARNING: soft rlimits too low. Number of files is 256, should be at least 1000") < 0
    assert criteria("init and listen starting") < 0
    assert criteria("[initandlisten]") < 0
    assert criteria("starting") < 0
    assert criteria("connection accepted") < 0
    # these should pass
    assert criteria("Mon Jun 11 15:56:16 [initandlisten] MongoDB starting : pid=7029 port=27018 dbpath=/data/rs2 64-bit host=Kaushals-MacBook-Air.local") > 0
    assert criteria("Mon Jun 11 15:56:24 [initandlisten] connection accepted from 127.0.0.1:55227 #6 (4 connections now open)") > 0
    return


def test_process():
    date = datetime.now()
    # non-valid message
    assert process("this is an invalid message", date) == None
    # these should pass
    doc = process("Mon Jun 11 15:56:16 [initandlisten] MongoDB starting : pid=7029 port=27018 dbpath=/data/rs2 64-bit host=Kaushals-MacBook-Air.local", date)
    assert doc
    assert doc["type"] == "init"
    assert doc["info"]["server"] == "Kaushals-MacBook-Air.local:27018"
    assert doc["info"]["subtype"] == "startup"
    pass
