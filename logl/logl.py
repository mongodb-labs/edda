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
from supporting_methods import *
from datetime import datetime
from filters import *
from post.server_matchup import address_matchup
from post.clock_skew import server_clock_skew
from post.replace_clock_skew import replace_clock_skew
from post.event_matchup import *
from ui.frames import generate_frames
from ui.connection import send_to_js

def main():
    """a main function, handles basic parsing and sends
    to traffic_control for more advanced handling"""

    if (len(sys.argv) < 2):
        print "Missing argument: please provide a filename"
        return

    # argparse methods
    parser = argparse.ArgumentParser(
        description = 'Process and visualize log files from mongo servers')
    parser.add_argument('--port', nargs=1)
    parser.add_argument('--host', nargs=1)
    parser.add_argument('--verbose', '-v', action='count')
    parser.add_argument('--version', action='version',
                        version="Running logl version {0}".format(__version__))
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
    print "Logl is storing data under collection name {0}".format(collName);


    # configure logger
    # use to switch from console to file: logname = "logl_logs/" + name + ".log"
    if not namespace.verbose:
        logging.basicConfig(level=logging.ERROR)
    elif namespace.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif namespace.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif namespace.verbose >= 3:
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
    logger.info('Connection opened with logl mongod, using {0} on port {1}'
                .format(host, port))
    logger.debug('Writing to db logl, collection {0}\nPreparing to parse log files'
                 .format(name))

    # read in from each log file
    fileNames = []
    for arg in namespace.filename:
        fileNames.append(arg)
        try:
            f = open(arg, 'r')
        except IOError:
            print "Error: Unable to read file {0}\nExiting".format(arg)
            return
        counter = 0
        stored = 0
        server_num = -1

        logger.warning('Reading from logfile {0}...'.format(arg))
        previous = "none"
        #f is the file names
        for line in f:
            counter += 1
            # handle restart lines
            if (string.find(line, '*****') >= 0):
                logger.debug("Skipping restart message")
                continue
            # skip blank lines
            if (len(line) > 1):
                date = date_parser(line)
                if not date:
                    logger.warning("Line {0} has a malformatted date, skipping"
                                   .format(counter))
                    continue
                doc = traffic_control(line, date)
                if doc:
                    # is there a server number for us yet?  If not, get one
                    if server_num == -1:
                        server_num = get_server_num("unknown", servers)
                    # see if we have captured a new server address
                    if doc["type"] == "init" and doc["info"]["subtype"] == "startup":
                        logger.debug("Found addr {0} for server {1} from startup msg"
                                     .format(doc["info"]["addr"], server_num))
                        assign_address(server_num, str(doc["info"]["addr"]), servers)
                    if doc["type"] == "status" and "addr" in doc["info"]:
                        logger.debug("Found addr {0} for server {1} from rs_status msg"
                                     .format(doc["info"]["addr"], server_num))
                        assign_address(server_num, str(doc["info"]["server"]), servers)
                    # skip repetitive 'exit' messages
                    if doc["type"] == "exit" and previous == "exit":
                        continue
                    doc["origin_server"] = server_num
                    entries.insert(doc)
                    logger.debug('Stored line {0} of {1} to db'.format(counter, arg))
                    stored += 1
                    previous = doc["type"]
        logger.warning('-' * 64)
        logger.warning('Finished running on {0}'.format(arg))
        logger.info('Stored {0} of {1} log lines to db'.format(stored, counter))
        logger.warning('=' * 64)

    # if no servers or meaningful events were found, exit
    if servers.find().count() == 0:
        logger.critical("No servers were found, exiting.")
        return
    if entries.find().count() == 0:
        logger.critical("No meaningful events were found, exiting.")
        return
    logger.info("Finished reading from log files, performing post processing")
    logger.info('-' * 64)
    if len(namespace.filename) > 1:
        logger.info("Attempting to resolve server names")
        result = address_matchup(db, collName)
        if result == 1:
            logger.info("Server addresses successfully resolved")
        else:
            logger.warning("Server addresses could not be resolved")
        logger.info('-' * 64)
    # event matchup
    logger.info("Matching events across documents and logs...")
    events = event_matchup(db, collName)
    logger.info("Completed event matchup")
    logger.info('-' * 64)
    # generate frames
    logger.info("Converting events into frames...")
    frames = generate_frames(events, db, collName)
    logger.info("Completed frame conversion")
    logger.info('-' * 64)
    # send to server
    logger.info("Sending frames to server...")
    send_to_js(frames, get_server_names(db, collName), get_admin_info(fileNames))
    logger.info('-' * 64)
    logger.info('=' * 64)
    logger.warning('Completed post processing.\nExiting.')


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

                # for first release, ignore conn_msg.py, not supported
                if fname == "filters.conn_msg":
                    continue

                # if module is valid and contains method, run!
                if 'process' in dir(sys.modules[fname]):
                    doc = sys.modules[fname].process(msg, date)
                    if (doc != None):
                        logger.debug("Filter {0} returned a valuable doc, storing to db".format(fname))
                        return doc


def get_server_names(db, collName):
    """Format the information in the .servers collection
    into a data structure to be sent to the JavaScript client"""
    server_names = {}
    server_names["hostname"] = {}
    server_names["IP"] = {}
    cursor = db[collName + ".servers"].find()
    for doc in cursor:
        server_names["hostname"][doc["server_num"]] = doc["server_name"]
        server_names["IP"][doc["server_num"]] = doc["server_IP"]
    return server_names


def get_admin_info(fileNames):
    """Format administrative information to send to the
    JavaScript client"""
    admin_info = {}
    admin_info["file_names"] = fileNames
    admin_info["version"] = __version__
    return admin_info


if __name__ == "__main__":
    main()
