#!/usr/bin/env python
"""This module processes RS STATUS CHANGE types of log lines."""

import string
import re

def criteria(msg):
    """does the given log line fit the criteria for this module?
    return an integer code if yes, -1 if no"""

    # check for rsStart msg
    if (string.find(msg, '[rsStart]') >= 0):
        return 1

    # check for rsHealthPoll msg
    if (string.find(msg, '[rsHealthPoll] replSet') >= 0):
        return 2


def process(msg, date):
    """if the given log line fits the critera for this module,
    processes the line and creates a document for it.
    document = {
       "date" : date,
       "type" : "status",
       "msg" : msg,
       "origin_server" : name,
       "info" : {
          "subtype" : None,
          "status" : status,
          "status_code" : int,
          "server" : "host:port",
          }
    }"""

    result = criteria(msg)
    if result < 0:
        return None

    doc = {}
    doc["date"] = date
    doc["type"] = "status"
    doc["info"] = {}
    doc["msg"] = msg

    # is the replSet starting up?
    if result == 1:
        return rs_start(msg, doc)
    # is the replSet reporting a health change?
    elif result == 2:
        return rs_health(msg, doc)
    else:
        return None


def rs_start(msg, doc):
    """this replica set is starting up.  Capture host information."""

    # capture host information from state STARTUP1
    place = string.find(msg, "I am")
    if (place >= 0):
        doc["info"]["server"] = msg[place + 6:]
        doc["info"]["status"] = "STARTUP1"
        doc["info"]["status_code"] = 0
        return doc
    # capture information for state STARTUP2
    place = string.find(msg, "STARTUP2")
    if (place >= 0):
        doc["info"]["server"] = "self"
        doc["info"]["status"] = "STARTUP2"
        doc["info"]["status_code"] = 5
        return doc
    return None


def rs_health(msg, doc):
    """this replica set is reporting a health change."""
    return doc

