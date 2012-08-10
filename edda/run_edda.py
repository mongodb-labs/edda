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
"""edda reads in from MongoDB log files and parses them.
After storing the parsed data in a separate collection,
the program then uses this data to provide users with a
visual tool to help them analyze their servers.

Users can customize this tool by adding their own parsers
to the edda/filters/ subdirectory, following the layout specified
in edda/filters/template.py.
"""
__version__ = "0.7.0"

import argparse
import gzip
import os
import sys
import json

from bson import objectid
from datetime import datetime
from filters import *
from post.server_matchup import address_matchup
from post.event_matchup import event_matchup
from pymongo import Connection
from supporting_methods import *
from ui.frames import generate_frames
from ui.connection import send_to_js

PARSERS = [
    rs_status.process,
    fsync_lock.process,
    rs_sync.process,
    init_and_listen.process,
    stale_secondary.process,
    rs_exit.process,
    rs_reconfig.process
]

LOGGER = None


def main():
    """This is the main function of edda.  It takes log
    files as command line arguments and sends each
    line of each log through a series of parses.  Then, this
    function sends the parsed-out information through several
    rounds of post-processing, and finally to a JavaScript
    client that displays a visual representation of the files.
    """

    if (len(sys.argv) < 2):
        print "Missing argument: please provide a filename"
        return
    mongo_version = ""
    # argparse methods
    parser = argparse.ArgumentParser(
    description='Process and visualize log files from mongo servers')
    parser.add_argument('--port', help="Specify the MongoDb port to use")
    parser.add_argument('--http_port', help="Specify the HTTP Port")
    parser.add_argument('--host', help="Specify host")
    parser.add_argument('--verbose', '-v', action='count')
    parser.add_argument('--json', help="json file")
    parser.add_argument('--version', action='version',
                        version="Running edda version {0}".format(__version__))
    parser.add_argument('--db', '-d', help="Specify DB name")
    parser.add_argument('--collection', '-c')  # Fixed
    parser.add_argument('filename', nargs='+')
    namespace = parser.parse_args()

    # handle captured arguments
    if namespace.json:
        has_json = True
    else:
        has_json = False
    if namespace.http_port:
        http_port = namespace.http_port
    else:
        http_port = '28000'
    if namespace.port:
        port = namespace.port
    else:
        port = '27017'
    if namespace.host:
        host = namespace.host
        place = host.find(":")
        if place >= 0:
            port = host[place + 1:]
            host = host[:place]
    else:
        host = 'localhost'
    uri = host + ":" + port
    uri = "mongodb://" + uri

    # generate a unique collection name, if not specified by user
    if namespace.collection:
        coll_name = namespace.collection
    else:
        coll_name = str(objectid.ObjectId())
    # for easier debugging:

    # configure logger
    # use to switch from console to file: logname = "edda_logs/" + name + ".log"
    if not namespace.verbose:
        logging.basicConfig(level=logging.ERROR)
    elif namespace.verbose == 1:
        logging.basicConfig(level=logging.WARNING)
    elif namespace.verbose == 2:
        logging.basicConfig(level=logging.INFO)
    elif namespace.verbose >= 3:
        logging.basicConfig(level=logging.DEBUG)

    global LOGGER
    LOGGER = logging.getLogger(__name__)

    # exit gracefully if no server is running
    try:
        connection = Connection(uri)
    except:
        LOGGER.critical("Unable to connect to {0}, exiting".format(uri))
        return

    if namespace.db:
        db = connection[namespace.db[0]]
    else:
        db = connection.edda
    entries = db[coll_name].entries
    servers = db[coll_name].servers

    now = datetime.now()

    # some verbose comments
    LOGGER.info('Connection opened with edda mongod, using {0} on port {1}'
                .format(host, port))

    # read in from each log file
    file_names = []
    f = None
    previous_version = False
    version_change = False
    first = True
    for arg in namespace.filename:
        gzipped = False
        if ".json" in arg:
            print "\n\nFound file {}, of type 'json'".format(arg)
            if not first:
                print "Ignoring previously processed files"
                " and loading configuration found in '.json' file."
            json_file = open(arg, "r")
            json_obj = json.loads(json_file.read())
            has_json = True
            break
        first = False
        if ".gz" in arg:
            opened_file = gzip.open(arg, 'r')
            gzipped = True
        if arg in file_names:
            LOGGER.warning("\nSkipping duplicate file {0}".format(arg))
            continue
        try:
            f = open(arg, 'r')
        except IOError as e:
            print "\nError: Unable to read file {0}".format(arg)
            print e
        file_names.append(arg)
        counter = 0
        stored = 0
        server_num = -1

        LOGGER.warning('Reading from logfile {0}...'.format(arg))
        previous = "none"
        print "\nCurrently parsing log-file: {}".format(arg)
        total_characters = 0
        total_chars = 0

        # Build log lines out of characters
        if gzipped:
            text = opened_file.read()
            #for char in text:
            total_chars = len(text)
            array = text.split('\n')
            file_lines = array
        else:
            file_lines = f

        LOGGER.debug(("Finished processing gzipped with a time of: " + str(datetime.now() - now)))
        file_info = os.stat(arg)
        total = 0
        total = file_info.st_size
        # Make sure the progress bar works with gzipped file.
        if gzipped:
            intermediate_total = total_chars
            total = int(intermediate_total * .98)

        point = total / 100
        increment = total / 100
        old_total = -1
        for line in file_lines:
            ratio = total_characters / point
            total_characters += len(line)
            if ratio >= 99:
                percent_string = "100"
            else:
                percent_string = str(total_characters / point)

            if ratio != old_total or ratio >= 99:
                sys.stdout.flush()
                sys.stdout.write("\r[" + "=" * (
                    (total_characters) / increment) + " " * (
                    (total - (total_characters)) / increment) + "]" + percent_string + "%")
                old_total = ratio

            counter += 1
            # handle restart lines
            if '******' in line:
                LOGGER.debug("Skipping restart message")
                continue
            # skip blank lines
            if (len(line) > 1):
                date = date_parser(line)
                if not date:
                    LOGGER.warning("Line {0} has a malformatted date, skipping"
                                   .format(counter))
                    continue
                doc = traffic_control(line, date)
                if doc:
                    # see if we have captured a new server address
                    # if server_num is at -1, this is a new server
                    if (doc["type"] == "init" and
                        doc["info"]["subtype"] == "startup"):
                        LOGGER.debug("Found addr {0} for server {1} from startup msg"
                                     .format(doc["info"]["addr"], server_num))
                        # if we have don't yet have a server number:
                        if server_num == -1:
                            server_num = get_server_num(
                                str(doc["info"]["addr"]), True, servers)
                        else:
                            assign_address(server_num,
                                           str(doc["info"]["addr"]), True, servers)
                    if (doc["type"] == "status" and
                        "addr" in doc["info"]):
                        LOGGER.debug("Found addr {0} for server {1} from rs_status msg"
                                     .format(doc["info"]["addr"], server_num))
                        if server_num == -1:
                            server_num = get_server_num(
                                str(doc["info"]["server"]), False, servers)
                        else:
                            assign_address(server_num,
                                           str(doc["info"]["server"]), False, servers)
                    # is there a server number for us yet?  If not, get one
                    if server_num == -1:
                        server_num = get_server_num("unknown", False, servers)

                    if doc["type"] == "version":
                        update_mongo_version(doc["version"], server_num, servers)
                        if not previous_version:
                            mongo_version = doc["version"]
                            previous_version = True
                        elif previous_version:
                            if doc["version"] != mongo_version:
                                version_change = True
                                mongo_version = doc["version"]

                    # skip repetitive 'exit' messages
                    if doc["type"] == "exit" and previous == "exit":
                        continue
                    doc["origin_server"] = server_num
                    entries.insert(doc)
                    LOGGER.debug('Stored line {0} of {1} to db'.format(counter, arg))
                    previous = doc["type"]
        LOGGER.warning('-' * 64)
        LOGGER.warning('Finished running on {0}'.format(arg))
        LOGGER.info('Stored {0} of {1} log lines to db'.format(stored, counter))
        LOGGER.warning('=' * 64)
    LOGGER.debug(("Finished processing everything with a time of: " + str(datetime.now() - now)))
    if version_change == True:
        print "\n VERSION CHANGE DETECTED!!"
        print mongo_version

    # if no servers or meaningful events were found, exit
    if servers.count() == 0 and has_json == False:
        LOGGER.critical("No servers were found, exiting.")
        return
    if entries.count() == 0 and has_json == False:
        LOGGER.critical("No meaningful events were found, exiting.")
        return

    LOGGER.info("Finished reading from log files, performing post processing")
    LOGGER.info('-' * 64)

    LOGGER.debug("\nTotal processing time for log files: " + str(datetime.now() - now))

    # Perform address matchup
    if len(namespace.filename) > 1:
        LOGGER.info("Attempting to resolve server names")
        result = address_matchup(db, coll_name)
        if result == 1:
            LOGGER.info("Server names successfully resolved")
        else:
            LOGGER.warning("Could not resolve server names")
        LOGGER.info('-' * 64)

    # Event matchup
    LOGGER.info("Matching events across documents and logs...")
    events = event_matchup(db, coll_name)
    LOGGER.info("Completed event matchup")
    LOGGER.info('-' * 64)

    # Create json file
    if not has_json:
        print "\nEdda is storing data under collection name {0}".format(coll_name)
        frames = generate_frames(events, db, coll_name)
        names = get_server_names(db, coll_name)
        admin = get_admin_info(file_names)
        large_json = open(coll_name + ".json", "w")
        json.dump(dicts_to_json(frames, names, admin), large_json)
    # No need to create json, one already provided.
    elif has_json:
        frames, names, admin = json_to_dicts(json_obj)
    send_to_js(frames, names, admin, http_port)
    LOGGER.info('-' * 64)
    LOGGER.info('=' * 64)
    LOGGER.warning('Completed post processing.\nExiting.')

    # Drop the collections created for this run.
    db.drop_collection(coll_name + ".servers")
    db.drop_collection(coll_name + ".entries")


def traffic_control(msg, date):
    """ Passes given message through a number of filters.  If a
        it fits the criteria of a given filter, that filter returns
        a document, which this function will pass up to main().
    """

    for process in PARSERS:
        doc = process(msg, date)
        if doc:
            return doc


def get_server_names(db, coll_name):
    """ Format the information in the .servers collection
        into a data structure to be sent to the JavaScript client.
    """
    server_names = {}
    server_names["self_name"] = {}
    server_names["network_name"] = {}
    server_names["version"] = {}
    for doc in db[coll_name].servers.find():
        server_names["self_name"][doc["server_num"]] = doc["self_name"]
        server_names["network_name"][doc["server_num"]] = doc["network_name"]
        try:
            if doc["version"]:
                server_names["version"][doc["server_num"]] = doc['version']
        except:
            LOGGER.debug("No version field detected")
            server_names["version"][doc["server_num"]] = "unknown"
    return server_names


def get_admin_info(file_names):
    """ Format administrative information to send to the
        JavaScript client.
    """
    admin_info = {}
    admin_info["file_names"] = file_names
    admin_info["version"] = __version__
    return admin_info


def json_to_dicts(large_dict):
    # Splits dictionary into frames, names, and admin parts.
    frames = large_dict["frames"]
    names = large_dict["names"]
    admin = large_dict["admin"]
    return frames, names, admin


def dicts_to_json(frames, names, admin):
    # Takes three dictionaries and makes one dictionary out of them.
    large_dict = {}
    large_dict["frames"] = frames
    large_dict["names"] = names
    large_dict["admin"] = admin
    return large_dict

if __name__ == "__main__":
    main()
