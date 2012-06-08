#!/usr/bin/env

import sys
import string
import pymongo
from pymongo import Connection
from noOp import storeInDB
from init import process

#------------------------------------------------------------    

# a main function, handles basic parsing and sends 
# to trafficControl for more advanced handling
def main():

    if (len(sys.argv) < 2):
        print "Missing argument: please give me a filename"
        return

    f = open(sys.argv[1], 'r')
    counter = 0 # this is mostly for debugging
    stored = 0

    connection = Connection('localhost', 27017)
    db = connection.log

    # drop the old collection
    db.drop_collection(db.loglines)
    loglines = db.loglines

    for line in f:
        counter += 1

        # skip restart messages
        if (string.find(line, '*****') >= 0):
            print 'handle restart message'
            continue

        # skip blank lines
        if (len(line) > 1):
            date2 = dateParser(line)
            date = efficientDateParser(line)
            if (date == None): 
                continue
            doc = trafficControl(line, date)
            if (doc != None):
                storeInDB(db, doc)
                stored += 1

    print 'Finished running, stored {0} of {1} log lines'.format(stored, counter)

#-------------------------------------------------------------    

# passes given message through a number of modules.  If a 
# it fits the criteria of a given module, that module returns
# a document, which this function will pass up to main().
def trafficControl(msg, date):

    # want to adapt the following to search ANY module in the modules directory
    return process(msg, date)


#-------------------------------------------------------------    

if __name__ == "__main__":
    main()
