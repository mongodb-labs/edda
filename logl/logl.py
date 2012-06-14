#!/usr/bin/env

import os
import sys
import string
import re
import logging
import argparse
import getpass
from bson import objectid
from pymongo import Connection
from parse_date import date_parser
import datetime

from modules import *
__version__ = "0.1"


def main():
    """a main function, handles basic parsing and sends
    to trafficControl for more advanced handling"""

    if (len(sys.argv) < 2):
        print "Missing argument: please provide a filename"
        return

    # argparse methods
    parser = argparse.ArgumentParser(description='Process and visualize log files from mongo servers')
    parser.add_argument('--port', nargs=1)
    parser.add_argument('--host', nargs=1)
    parser.add_argument('--verbose', '-v', action='count')
    parser.add_argument('--version', action='version', version="Running logl version {0}".format(__version__))
    parser.add_argument('--auth', action='store_true')
    parser.add_argument('--db', '-d', nargs=1)
    parser.add_argument('--collection', '-c', nargs=1)
    parser.add_argument('filename', nargs='+')
    namespace = parser.parse_args()

    # handle captured arguments
    if namespace.port:
        port = str(namespace.port)
    else:
        port = '27017'
    if namespace.host:
        host = str(namespace.host)
    else:
        host ='localhost'
    uri = host + ":" + port

    # handle auth
    # could probably be more secure...
    if namespace.auth:
        dbuser = getpass.getpass("Username:")
        dbpass = getpass.getpass()
        uri = dbuser + ":" + dbpass + "@" + uri
    uri = "mongodb://" + uri

    # generate a unique collection name, if not specified by user
    if namespace.collection:
        collName = str(namespace.collection)
    else:
        collName = str(objectid.ObjectId())
    print collName
    connection = Connection(uri)
    if namespace.db:
        db = connection[str(namespace.db)]
    else:
        db = connection.logl
    newcoll = db[collName]

    now = datetime.datetime.now()
    name = str(now.strftime("logl_%m_%d_%Y_at_%H_%M_%S"))

    # configure logger
    # use to switch from console to file: logname = "logl_logs/" + name + ".log"
    if not namespace.verbose:
        logging.basicConfig(level=logging.ERROR)
    elif namespace.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif namespace.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif namespace.verbose == 3:
        logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    # some verbose comments
    logger.info('Connection opened with logl mongod, using {0} on port {1}'.format(host, port))
    logger.debug('Writing to db logl, collection {0}\nPreparing to parse log files'.format(name))

    reset = True
    server_num = 0

    # read in from each log file
    for arg in namespace.filename:
        f = open(arg, 'r')
        counter = 0
        stored = 0

        server_num += 1

        # a name for this server
        origin_server = server_num

        logger.info('Reading from logfile {0}...'.format(arg))

        for line in f:
            counter += 1
            logger.debug('Reading line {0} from {1}'.format(counter, arg))

            # skip restart messages
            if (string.find(line, '*****') >= 0):
                reset = True
                server_num += 1
                origin_server = server_num
                continue
            # skip blank lines
            if (len(line) > 1):
                date = date_parser(line)
                if not date:
                    continue
                doc = trafficControl(line, date)
                if doc:
                    if reset:
                        if doc["info"] == "init":
                            if doc["info"]["subtype"] == "startup":
                                origin_server = doc["info"]["server"]
                                reset = False
                    reset = False # yes?
                    doc["origin_server"] = origin_server
                    newcoll.insert(doc)
                    logger.debug('Stored line {0} of {1} to db'.format(counter, arg))
                    stored += 1

        logger.info('-' * 64)
        logger.info('Finished running on {0}'.format(arg))
        logger.debug('Stored {0} of {1} log lines to db'.format(stored, counter))
        logger.info('=' * 64)
        logger.info('Exiting.')


def trafficControl(msg, date):
    """passes given message through a number of modules.  If a
    it fits the criteria of a given module, that module returns
    a document, which this function will pass up to main()."""
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

if __name__ == "__main__":
    main()
