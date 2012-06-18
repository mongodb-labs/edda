#!/usr/bin/env python
"""This filter processes RSSYNC types of log lines"""

import string
import logging


def criteria(msg):
    """Does the given log line fit the criteria for this filter?
    return an integer code if yes, -1 if not."""
    if (string.find(msg, 'closing') >= 0):
        return 0
    elif (string.find(msg, 'shutdown') >= 0):
        return 1
    elif (string.find(msg, 'dbexit') >= 0):
        return 2

    return -1


def process(msg, date):
    """if the given log line fits the criteria for this filter,
    processes the line and creates a document for it.
    document = {
       "date" : date,
       "type" : "exit",
       "info" : {
          "state_code" : messagetype
          "state" : state
       }
       "oritinal_message" : msg
       "exit_message" : exit_message
    }"""

    messagetype = criteria(msg)
    if(messagetype == -1):
        return None
    labels = ["CLOSING", "SHUTDOWN", "DBEXIT"]

    doc = {}
    doc["date"] = date
    doc["type"] = "exit"
    doc["info"] = {}
    doc["info"]["state_code"] = messagetype
    doc["info"]["state"] = labels[messagetype]
    doc["original_message"] = msg
    if(messagetype == 0):
        start = string.find(msg, 'closing')
        doc["exit_message"] = msg[start: len(msg)]
    elif(messagetype == 1):
        start = string.find(msg, 'shutdown: ')
        doc["exit_message"] = msg[start + 11: len(msg)]
    elif(messagetype == 2):
        doc["exit_message"] = "dbexit"

    #Has the member begun syncing to a different place
    return doc
