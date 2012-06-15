#!/usr/bin/env python
"""This module processes INITANDLISTEN log lines."""

import re
import string
import logging


def criteria(msg):
    """does the given log line fit the criteria for this module?
    return an integer code if yes, -1 if no."""
    # maybe we should fix this later...
    if (string.find(msg, '[initandlisten]') < 0):
        return -1
    # is it this server starting up?
    if (string.find(msg, 'starting') >= 0):
        return 1
    # has this server accepted a new connection?
    if (string.find(msg, 'connection accepted') >= 0):
        return 2


def process(msg, date):
    """If the given log line fits the criteria for this modules,
    processes the line and creates a document for it.
    document = {
       "date" : date,
       "type" : "init",
       "msg" : msg,
       "origin_server" : name --> this field is added in the main file
       "info" field structure varies with subtype:
       (startup) "info" : {
          "subtype" : "startup"
          "server" : "hostaddr:port"
       }
       (new_conn) "info" : {
          "subtype" : "new_conn",
          "server" : "hostaddr:port",
          "conn_number" : int,
       }
    }"""
    result = criteria(msg)
    if result < 0:
        return None
    doc = {}
    doc["date"] = date
    doc["type"] = "init"
    doc["info"] = {}
    doc["msg"] = msg

    # is it this server starting up?
    if result == 1:
        return starting_up(msg, doc)

    # has this server accepted a new connection?
    if result == 2:
        return new_conn(msg, doc)


def starting_up(msg, doc):
    """this server is starting up.  Capture host information."""
    logger = logging.getLogger(__name__)
    doc["info"]["subtype"] = "startup"

    # isolate port number
    pattern = re.compile("port=[0-9]+")
    m = pattern.search(msg)
    if m is None:
        logger.debug("malformed starting_up message: no port number found")
        return None
    port = m.group(0)[5:]

    # isolate host address
    start = string.find(msg, 'host=')
    host = msg[start + 5:len(msg)]

    doc["info"]["server"] = host + ":" + port
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
        logger.debug("malformed new_conn message: no IP address found")
        return None
    host = m.group(0)

    # isolate port number
    pattern = re.compile(":[0-9]{1,5}")
    n = pattern.search(msg[21:])
    if n is None:
        logger.debug("malformed new_conn message: no port number found")
        return None
    port = n.group(0)[1:]
    doc["info"]["server"] = host + ":" + port

    # isolate connection number
    pattern2 = re.compile("#[0-9]+")
    m = pattern2.search(msg)
    if m is None:
        logger.debug("malformed new_conn message: no connection number found")
        return None
    doc["info"]["conn_number"] = m.group(0)[1:]
    logger.debug("Returning new doc for a message of type: initandlisten: new_conn")
    return doc
