#!/usr/bin/env
#------------------------------------------------------------
# This module processes WHICH types of log lines.
#------------------------------------------------------------

import re
import string

#------------------------------------------------------------

# does the given log line fit the criteria for this module?
# return True if yes, False if no.
def criteria(msg):

    # maybe we should fix this later...
    if (string.find(msg, '[initandlisten]') >= 0):
        return True

#------------------------------------------------------------

# if the given log line fits the criteria for this module,
# processes the line and creates a document for it.
# document = {
    # "date" : date,
    # "type" : "init"
    # "msg" : msg
    # "info" field structure varies with subtype:
# (startup) "info" : {
             # "subtype" : "startup",
             # "host" : IP or hostaddr,
             # "port" : port
             # }
# (new_conn) "info" : {
             # "subtype" : "new_conn",
             # "host" : IP,
             # "port" : port,
             # "conn_number" : int,
             # }

def process(msg, date):

    if (criteria(msg) == False): return None
    
    doc = {}
    doc["date"] = date
    doc["type"] = "init"
    doc["info"] = {}
    doc["msg"] = msg

    # is it this server starting up?               
    if (string.find(msg, 'starting') >= 0):
        return starting_up(msg, doc)

    # has this server accepted a new connection?
    if (string.find(msg, 'connection accepted') >= 0):
        return new_conn(msg, doc)

#------------------------------------------------------------

# this server is starting up.  Capture host information.
def starting_up(msg, doc):

    doc["info"]["subtype"] = "startup"

    # isolate port number                                                              
    start = string.find(msg, 'port=')
    doc["info"]["port"] = msg[start + 5:start + 10]

    # isolate host IP address                                                          
    start = string.find(msg, 'host=')
    doc["info"]["host"] = msg[start + 5:len(msg) - 1]

    return doc

#------------------------------------------------------------

# this server has accepted a new connection.
def new_conn(msg, doc):

    doc["info"]["subtype"] = "new_conn"

    # this very long regex recognizes legal IP addresses
    pattern = re.compile("(([0|1]?[0-9]{1,2})|(2[0-4][0-9])|(25[0-5]))(\.([0|1]?[0-9]{1,2})|(2[0-4][0-9])|(25[0-5])){3}")
    m = pattern.search(msg)
    if (m == None): return None
    doc["info"]["host"] = m.group(0)
    
    # isolate port number                  
    doc["info"]["port"] = msg[m.end(0) + 1: m.end(0) + 6]
    
    # isolate connection number                                               
    # it is NOT safe to assume number is the last thing on the line...
    # FIX ME!
    place = string.find(msg, '#')
    doc["info"]["conn_number"] = msg[place + 1: len(msg) - 1]
    
    return doc


