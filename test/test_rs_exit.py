from logl.filters.rs_exit import *
from datetime import datetime


def test_criteria():
    assert criteria("this should not pass") == -1
    assert criteria("Thu Jun 14 11:43:28 [interruptThread] closing listening socket: 6") == 0
    assert criteria("Thu Jun 14 11:43:28 [interruptThread] shutdown: going to close listening sockets...") == 1
    assert criteria("Thu Jun 14 11:43:28 dbexit: really exiting now") == 2
    assert criteria("Foo bar") == -1

def test_process():
    date = datetime.now()
    check_state("Thu Jun 14 11:43:28 [interruptThread] closing", 0, date)
    check_state("Thu Jun 14 11:43:28 [interruptThread] shutdown: ", 1, date)
    check_state("Thu Jun 14 11:43:28 dbexit: really exiting now", 2, date)
    check_state("Thu Jun 14 11:43:28 [interruptThread] closing", 0, date)
    check_state("Thu Jun 14 11:43:28 [interruptThread] shutdown: going to close listening sockets...", 1, date)
    check_state("Thu Jun 14 11:43:28 dbexit: really exiting now", 2, date)
    assert process("This should fail", date) == None


def check_state(message, code, date):
    doc = process(message, date)
    assert doc
    assert doc["type"] == "exit"
    assert doc["original_message"] == message
    assert doc["info"]["state_code"] == code
    #print 'Server number is: *{0}*, testing against, *{1}*'.format(doc["info"]["server"], server)
