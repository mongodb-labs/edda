#!/usr/bin/env

import pymongo
from pymongo import Connection

#-------------------------------------------------

# right now we have the following structure for a document:

# "date" : date object
# "from_server" : string name, separate collection matching names to info
# "about_server" : string name, ditto
# "type" : either init, exit, etc...
# "msg" : stores the full line from the log

def storeInDB(db, msg, date):

    entry = {}
    entry["date"] = date
    entry["msg"] = msg

    db.loglines.insert(entry)

