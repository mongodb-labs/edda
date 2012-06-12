#!/usr/bin/env

import os
import sys
import string
import pymongo
import re
import logging
from bson import objectid
from pymongo import Connection
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
    flags = dict.fromkeys(["V1", "V2", "V3", "PORTSET", "HOSTSET"], False)
    port = 27017
    host = 'localhost'

    pattern = re.compile("^-")

    # handle filenames and command-line options
    for arg in sys.argv[1:]:

        if flags["PORTSET"]: 
            port = arg
            flags["PORTSET"] = False
            continue
        if flags["HOSTSET"]:
            pos = string.find(arg, ":")
            if (pos > 0):
                host = arg[0:pos]
                port = arg[pos + 1: len(arg)]
                print 'host: {0} port: {1}'.format(host, port)
            else: 
                host = arg
                print 'host: ', host
            flags["HOSTSET"] = False
            continue

        # is it an option? 
        m = pattern.search(arg)
        if (m != None):

            if "version" in arg:
                print "Running logl version: 0.0.1" 
                return
            elif "help" in arg: print helpMsg()
            elif "port" in arg: flags["PORTSET"] = True
            elif "host" in arg or arg is "-h": flags["HOSTSET"] = True
            elif "verbose" in arg: flags["V1"] = True
            else:
                vstring = re.compile("v+")
                m = vstring.search(arg)
                if (m != None):
                    x = m.end(0) - m.start(0)
                    if x >= 1: flags["V1"] = True
                    if x >= 2: flags["V2"] = True
                    if x >= 3: flags["V3"] = True

        # No, must be a filename
        else: files.append(arg)

    # generate a unique collection name
    collName = str(objectid.ObjectId())
    connection = Connection('localhost', 27017)
    db = connection.logl
    newcoll = db[collName]

    now = datetime.datetime.now()
    name = str(now.strftime("logl_%m_%d_%Y_at_%H_%M_%S"))

    # configure logger      
    logname = "logl_logs/" + name + ".log"
#    if flags["V1"]: logging.basicConfig(filename=logname, level=logging.WARNING)
#    elif flags["V2"]: logging.basicConfig(filename=logname, level=logging.INFO)
#    elif flags["V3"]: logging.basicConfig(filename=logname, level=logging.DEBUG)
    logging.basicConfig(level=logging.DEBUG)

    logger = logging.getLogger(__name__)

    # some verbose comments
    logger.info('Connection opened with logl mongod, using {0} on port {1}'.format(host, port))
    logger.debug('Writing to db logl, collection {0}\nPreparing to parse log files'.format(name))

    # read in from each log file
    for arg in files:
        
        f = open(arg, 'r')
        counter = 0 
        stored = 0

        logger.info('Reading from logfile {0}...'.format(arg))
        
        for line in f:

            counter += 1
            logger.debug('Reading line {0} from {1}'.format(counter, arg))

            # skip restart messages
            if (string.find(line, '*****') >= 0):
                continue

            # skip blank lines
            if (len(line) > 1):
                date = date_parser(line)
                if (date == None): 
                    continue
                doc = trafficControl(line, date)
                if (doc != None):
                    newcoll.insert(doc)
                    logger.debug('Stored line {0} of {1} to db'.format(counter, arg))
                    stored += 1

        logger.info('-'*64)
        logger.info('Finished running on {0}'.format(arg))
        logger.debug('Stored {0} of {1} log lines to db'.format(stored, counter))
        logger.info('='*64)
        logger.info('Exiting.')

#-------------------------------------------------------------    

# passes given message through a number of modules.  If a 
# it fits the criteria of a given module, that module returns
# a document, which this function will pass up to main().
def trafficControl(msg, date):

    pattern = re.compile(".py$")
    dirList = os.listdir("modules")

    logger = logging.getLogger(__name__)

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
                        logger.info('Found {0} type message, storing to db'.format(fname))  
                        return doc
                    # for now, this will only return the first module hit...

#------------------------------------------------------------    

def helpMsg():
    str_list = []
    str_list.append("Logl version: 0.0.1\n")
    str_list.append("usage: logl.py [options] [log filenames]\n")
    str_list.append("options:\n")
    str_list.append(" -v [--verbose]\tto increase verbosity, increase number of v's (-vvv is max)\n")
    str_list.append(" --host\t\tspecify host to connect to (can also use --host hostname:port)\n")
    str_list.append(" --port\t\tspecify server port\n")
    str_list.append(" --version\tprint logl version number\n")
    return ''.join(str_list)

#------------------------------------------------------------    

if __name__ == "__main__":
    main()
