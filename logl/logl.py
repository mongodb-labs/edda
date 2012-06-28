# Copyright 2012 10gen, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/env
"""logl reads in from MongoDB log files and parses them.
After storing the parsed data in a separate collection,
the program then uses this data to provide users with a
visual tool to help them analyze their servers.

Users can customize this tool by adding their own parsers
to the logl/modules/ subdirectory, following the layout specified
in logl/modules/template.py"""
__version__ = "0.1"

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
from datetime import datetime
from filters import *
from post.clock_skew import server_clock_skew
from post.replace_clock_skew import replace_clock_skew
from post.organize_servers import organize_servers


def main():
    """a main function, handles basic parsing and sends
    to traffic_control for more advanced handling"""

    if (len(sys.argv) < 2):
        print "Missing argument: please provide a filename"
        return

    # argparse methods
    parser = argparse.ArgumentParser(description='Process and visualize log files from mongo servers')
    parser.add_argument('--port', nargs=1)
    parser.add_argument('--host', nargs=1)
    parser.add_argument('--verbose', '-v', action='count')
    parser.add_argument('--version', action='version', version="Running logl version {0}".format(__version__))
    parser.add_argument('--db', '-d', nargs=1)
    parser.add_argument('--collection', '-c', nargs=1)
    parser.add_argument('filename', nargs='+')
    namespace = parser.parse_args()

    # handle captured arguments
    if namespace.port:
        port = str(namespace.port[0])
    else:
        port = '27017'
    if namespace.host:
        host = str(namespace.host[0])
        place = string.find(host, ":")
        if place >= 0:
            port = host[place + 1:]
            host = host[:place]
    else:
        host ='localhost'
    uri = host + ":" + port
    uri = "mongodb://" + uri

    # generate a unique collection name, if not specified by user
    if namespace.collection:
        collName = str(namespace.collection[0])
    else:
        collName = str(objectid.ObjectId())
    # for easier debugging:
    print collName


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


    # exit gracefully if no server is running
    try:
        connection = Connection(uri)
    except:
        logger.critical("Unable to connect to {0}, exiting".format(uri))
        return

    if namespace.db:
        db = connection[str(namespace.db[0])]
    else:
        db = connection.logl
    entries = db[collName + ".entries"]
    servers = db[collName + ".servers"]

    now = datetime.now()
    name = str(now.strftime("logl_%m_%d_%Y_at_%H_%M_%S"))

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
        logger.warning('Reading from logfile {0}...'.format(arg))
        previous = "none"
        for line in f:
            add_doc = True
            counter += 1
            logger.debug('Reading line {0} from {1}'.format(counter, arg))
            # handle restart lines
            if (string.find(line, '*****') >= 0):
                reset = True
                server_num += 1
                origin_server = server_num
                continue
            # skip blank lines
            if (len(line) > 1):
                date = date_parser(line)
                if not date:
                    logger.warning("Line {0} has a malformatted date, skipping".format(counter))
                    continue
                doc = traffic_control(line, date)
                if doc:
                    if reset:
                        if doc["type"] == "init":
                            if doc["info"]["subtype"] == "startup":
                                if doc["info"]["server"]:
                                    origin_server = doc["info"]["server"]
                                    servers.insert(new_server(server_num, origin_server))
                    if doc["type"] == "exit":
                        if previous == "exit":
                            add_doc = False
                        pass

                    reset = False
                    doc["origin_server"] = origin_server
                    if add_doc:
                        entries.insert(doc)
                        logger.debug('Stored line {0} of {1} to db'.format(counter, arg))
                        stored += 1
                    previous = doc["type"]

        logger.warning('-' * 64)
        logger.warning('Finished running on {0}'.format(arg))
        logger.info('Stored {0} of {1} log lines to db'.format(stored, counter))
        logger.warning('=' * 64)
    logger.info("Finished reading from log files, performing post processing")
    logger.info('-' * 64)
    if len(namespace.filename) > 1:
        logger.info("Attempting to resolve server names")
        #result = server_matchup(db, collName)
        logger.info('-' * 64)
        logger.info("Attempting to resolve clock skew across servers")
        result = server_clock_skew(db, collName)
        logger.info("Attempting to Fix Clock_skews in original .entries documents")
        replace_clock_skew(db, collName)
        logger.info("Completed replacing skew values. ")

    logger.warning('Exiting.')


def new_server(server_num, origin_server):
    """Checks if this server (hostaddr and port) is already in
    the database.  If so, returns the matching document.
    If not, creates a document for the server"""
    doc = {}
    doc["server_num"] = server_num
    if origin_server == server_num:
        doc["server_name"] = "unknown"
    else:
        doc["server_name"] = origin_server
    return doc


def traffic_control(msg, date):
    """passes given message through a number of filters.  If a
    it fits the criteria of a given filter, that filter returns
    a document, which this function will pass up to main()."""
    pattern = re.compile(".py$")
    dir_name = os.path.dirname(os.path.abspath(__file__)) + "/filters"
    dirList = os.listdir(dir_name)

    logger = logging.getLogger(__name__)

    for fname in dirList:

        # only deal with .py files
        m = pattern.search(fname)
        if (m != None):
            fname = fname[0:len(fname) - 3]

            # ignore __init__ file and template.py
            if fname != "__init__" and fname != "template":
                fname = "filters." + fname

                # if module is valid and contains method, run!
                if 'process' in dir(sys.modules[fname]):
                    doc = sys.modules[fname].process(msg, date)
                    if (doc != None):
                        logger.info('Found {0} type message, storing to db'.format(fname))
                        return doc
                    # for now, this will only return the first module hit...

if __name__ == "__main__":
    main()
