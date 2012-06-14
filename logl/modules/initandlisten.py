#!/usr/bin/env python
"""This module processes INITANDLISTEN log lines."""

import re
import string
import logging


def criteria(msg):
    """does the given log line fit the criteria for this module?
return True if yes, False if no."""
    # maybe we should fix this later...
    if (string.find(msg, '[initandlisten]') >= 0):
        return True


def process(msg, date):
    """If the given log line fits the criteria for this modules,
    processes the line and creates a document for it.
    document = {
    "date" : date,
    "type" : "init",
    "msg" : msg,
    "info" field structure varies with subtype:
    (startup) "info" : {
       "subtype" : "startup"
       "server" : "hostaddr:port"
    }
    (new_conn) "info" : {
       "subtype" : "new_conn",
       "server" : "hostaddr:port",
       "conn_number" : int,
    }"""
    if criteria(msg) == False:
        return None
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


def starting_up(msg, doc):
    """this server is starting up.  Capture host information."""
    logger = logging.getLogger(__name__)
    doc["info"]["subtype"] = "startup"
    # isolate port number
    start = string.find(msg, 'port=')
    doc["info"]["port"] = msg[start + 5:start + 10]

    # isolate host IP address
    start = string.find(msg, 'host=')
    doc["info"]["host"] = msg[start + 5:len(msg) - 1]
    logger.debug("Returning new doc for a message of type: initandlisten: starting_up")
    return doc


def new_conn(msg, doc):
    """this server has accepted a new connection."""
    doc["info"]["subtype"] = "new_conn"
    logger = logging.getLogger(__name__)

    # this very long regex recognizes legal IP addresses
    pattern = re.compile("(([0|1]?[0-9]{1,2})|(2[0-4][0-9])|(25[0-5]))(\.([0|1]?[0-9]{1,2})|(2[0-4][0-9])|(25[0-5])){3}")
    m = pattern.search(msg)
    if (m == None):
        return None
    doc["info"]["host"] = m.group(0)

    # isolate port number
    doc["info"]["port"] = msg[m.end(0) + 1: m.end(0) + 6]
    # isolate connection number
    pattern2 = re.compile("#[0-9]+")
    m = pattern2.search(msg)
    if m is None:
        return None
    doc["info"]["conn_number"] = m.group(0)[1:]
    logger.debug("Returning new doc for a message of type: initandlisten: new_conn")
    return doc
