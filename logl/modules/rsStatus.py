#!/usr/bin/env python
"""This module processes WHICH types of log lines."""

import string
import re

def criteria(msg):
    """does the given log line fit the criteria for this module?
    return an integer code if yes, -1 if no"""

    # check for rsStart msg
    if (string.find(msg, '[rsStart]') >= 0):
        return 1

    # check for rsHealthPoll msg
    if (string.find(msg, '[rsHealthPoll]') >= 0):
        if (string.find(msg, 'replSet') >= 0):
            return 2


def process(msg, date):
    """if the given log line fits the critera for this module,
    processes the line and creates a document for it."""

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
    return None


def rs_health(msg, doc):
    """this replica set is reporting a health change."""
    return None

