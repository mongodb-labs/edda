#!/usr/bin/env
#------------------------------------------------------------
# This module processes WHICH types of log lines.
#------------------------------------------------------------

import re
import string
import logging

#------------------------------------------------------------

# does the given log line fit the criteria for this module?
# return True if yes, False if no.
# VL: low verbosity, VH: high verbosity (if VH is True, VL is also True)
def criteria(msg):
    if (string.find(msg, '[rsSync]') >= 0):
        if(string.find(msg, 'syncing') >= 0):
            return 1
        return -1

#------------------------------------------------------------

# if the given log line fits the criteria for this module,
# processes the line and creates a document for it.
# VL: low verbosity, VH: high verbosity (if VH is True, VL is also True)
# document = {
    # "date" : date,
    # "type" : "init", 
    # "msg" : msg
    # "info" structure below:
# (syncingDIff) "info" : {
         # "host" : ip or host name
         # "port" : port

def process(msg, date):
    messageType = criteria(msg)
    if(messageType == -1):
        return None
    
    doc = {}
    doc["date"] = date
    doc["type"] = "sync"
    doc["info"] = {}
    doc["msg"] = msg

    #Has the member begun syncing to a different place
    if(messageType == 1):
        return syncingDIff(msg, doc)

#------------------------------------------------------------


def syncingDiff(msg, doc):
    doc["info"]["subtype"] = "reSyncing"

    start = string.find(msg, "to: ")

    doc["info"]["port"] = msg[start + 4: len(msg) - 5]
    doc["info"]["host"] = msg[len(msg) - 5: len(msg)]
    
    logger = logging.getLogger(__name__)
    logger.debug(doc)
    
    return doc
