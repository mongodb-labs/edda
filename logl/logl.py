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

    # file list and option flags
    files = []
    V1 = False
    V2 = False
    V3 = False
    V4 = False

    pattern = re.compile("^-")

    # handle filenames v command-line options
    for arg in sys.argv[1:]:

        # is it an option? 
        m = pattern.search(arg)
        if (m != None):
            if "version" in arg:
                print "Running logl version: 0.0.1" 
                return
            elif "help" in arg:
                print helpMsg()

            elif "verbose" in arg:
                V1 = True
                print "V1 on"
            else:
                vstring = re.compile("v+")
                m = vstring.search(arg)
                if (m != None):
                    x = m.end(0) - m.start(0)
                    if x >= 1: V1 = True
                    if x >= 2: V2 = True
                    if x >= 3: V3 = True
                    if x >= 4: V4 = True

        # No, must be a filename
        else:
            files.append(arg)

    connection = Connection('localhost', 27017)
    db = connection.logl
    now = datetime.datetime.now()
    name = str(now.strftime("logl_%m_%d_%Y_at_%H_%M_%S"))
    newcoll = db[name]

    # some verbose comments
    if V1: print 'Connection opened with logl mongod'
    if V2: print 'Connected to localhost on port 27017'
    if V3: print 'Writing to db logl, collection ', name
    if V4: print 'Preparing to parse log files'

    # read in from each log file
    for arg in files:
        
        f = open(arg, 'r')
        counter = 0 
        stored = 0

        if V1: print 'Reading from logfile', arg, '...'
        
        for line in f:

            counter += 1
            if V4: print 'Reading line {0} from {1}'.format(counter, arg)

            # skip restart messages
            if (string.find(line, '*****') >= 0):
                continue

            # skip blank lines
            if (len(line) > 1):
                date = date_parser(line)
                if (date == None): 
                    continue
                doc = trafficControl(line, date, V3, V4)
                if (doc != None):
                    storeInDB(newcoll, date, doc)
                    if V4: print 'Stored line {0} of {1} to db'.format(counter, arg)
                    stored += 1

        if V1: print '-'*64
        if V1: print 'Finished running on {0}'.format(arg)
        if V2: print 'Stored {0} of {1} log lines to db'.format(stored, counter)
        if V1: 
            print '='*64
            print 'Exiting.'

#-------------------------------------------------------------    

# passes given message through a number of modules.  If a 
# it fits the criteria of a given module, that module returns
# a document, which this function will pass up to main().
def trafficControl(msg, date, V3, V4):

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
                        if V3: print 'Found a {0} type message, storing to db'.format(fname)  
                        return doc
                    # for now, this will only return the first module hit...

#------------------------------------------------------------    

def helpMsg():
    str_list = []
    str_list.append("Logl version: 0.0.1\n")
    str_list.append("usage: logl.py [options] [log filenames]\n")
    str_list.append("options:\n")
    str_list.append(" -v [--verbose]\tto increase verbosity, increase number of v's (-vvvv is max)\n")
    str_list.append(" --host\t\tspecify host to connect to (can also use --host hostname:port)\n")
    str_list.append(" --port\t\tspecify server port\n")
    str_list.append(" --version\tprint logl version number\n")
    return ''.join(str_list)

#------------------------------------------------------------    

if __name__ == "__main__":
    main()
