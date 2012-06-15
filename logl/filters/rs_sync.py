#!/usr/bin/env python
"""This filter processes RSSYNC types of log lines"""


import string
import logging


def criteria(msg):
    """Does the given log line fit the criteria for this filter?
    return an integer code if yes, -1 if not."""
    if (string.find(msg, '[rsSync]') >= 0):
        if(string.find(msg, 'syncing') >= 0):
            return 1
    return -1


def process(msg, date):
    """if the given log line fits the criteria for this filter,
    processes the line and creates a document for it.
    document = {
       "date" : date,
       "type" : "rsSync",
       "msg" : msg,
       "origin_server" : name,
       "info" structure below:
       "info" : {
          "subtype" : "reSyncing",
          "server" : "host:port"
          }
    }"""
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
        return syncing_diff(msg, doc)


def syncing_diff(msg, doc):
    """generates and returns a document for rs that are
    syncing to a new server"""

    doc["info"]["subtype"] = "reSyncing"

    start = string.find(msg, "to: ")
    if (start < 0):
        return None
    doc["info"]["server"] = msg[start + 4: len(msg) - 1]
    logger = logging.getLogger(__name__)
    logger.debug(doc)
    return doc
