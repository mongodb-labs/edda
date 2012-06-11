#!/usr/bin/env

import os
import sys
import string
import pymongo
import re
from pymongo import Connection
from noOp import storeInDB
from init import process
from parse_date import date_parser
import datetime

from modules import *

#------------------------------------------------------------    

# a main function, handles basic parsing and sends 
# to trafficControl for more advanced handling
def main():

    if (len(sys.argv) < 2):
        print "Missing argument: please give me a filename"
        return

    f = open(sys.argv[1], 'r')
    counter = 0 
    stored = 0

    connection = Connection('localhost', 27017)
    db = connection.log
    now = datetime.datetime.now()
    name = now.strftime("-%m-%d-%Y-at-%H:%M:%S")
    newcoll = db.logl[name]

    for line in f:
        counter += 1

        # skip restart messages
        if (string.find(line, '*****') >= 0):
            print 'handle restart message'
            continue

        # skip blank lines
        if (len(line) > 1):
            date = date_parser(line)
            if (date == None): 
                continue
            doc = trafficControl(line, date)
            if (doc != None):
                storeInDB(newcoll, date, doc)
                stored += 1

    print 'Finished running, stored {0} of {1} log lines'.format(stored, counter)

#-------------------------------------------------------------    

# passes given message through a number of modules.  If a 
# it fits the criteria of a given module, that module returns
# a document, which this function will pass up to main().
def trafficControl(msg, date):

    pattern = re.compile(".py$")
    dirList = os.listdir("modules")

    for fname in dirList:
        
        # only deal with .py files
        m = pattern.search(fname)
        if (m != None):
            fname = fname[0:len(fname) - 3]

            # ignore __init__ file and template.py
            if fname != "__init__" and fname != "template":
                fname = "modules." + fname

                # if module is valid and contains method, run!
                if 'process' in dir(sys.modules[fname]):
                    doc = sys.modules[fname].process(msg, date)
                    if (doc != None):
                        return doc
                    # for now, this will only return the first module hit...

#------------------------------------------------------------    

if __name__ == "__main__":
    main()
