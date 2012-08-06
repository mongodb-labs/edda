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
__version__ = "0.6.1"

import argparse
import gzip
import os
import sys
import json
import tempfile

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
    #parser.add_argument('--json', action='Take json')
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
    name = now.strftime("edda_%m_%d_%Y_at_%H_%M_%S")

    # some verbose comments
    LOGGER.info('Connection opened with edda mongod, using {0} on port {1}'
                .format(host, port))
    LOGGER.debug('Writing to db edda, collection {0}\nPreparing to parse log files'
                 .format(name))

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
                print "Ignoring previously processed files and loading configuration found in '.json' file."
            json_file = open(arg, "r")
            json_obj = json.loads(json_file.read())
            has_json = True
            break
        first = False
        if ".gz" in arg:
            opened_file = gzip.open(arg, 'r')
            gzipped = True
        if arg in file_names:
            LOGGER.warning("Skipping duplicate file {0}".format(arg))
            continue
        try:
            f = open(arg, 'r')
        except IOError as e:
            print "Error: Unable to read file {0}".format(arg)
            print e
            if f:
                f.close()
            return
        file_names.append(arg)
        counter = 0
        stored = 0
        server_num = -1

        LOGGER.warning('Reading from logfile {0}...'.format(arg))
        previous = "none"
        #f is the file names\

        print ""
        print "Currently parsing log-file: {}".format(arg)
        #sys.stdout.flush()
        total_characters = 0
        lines = []
        new_line = ""
        total_chars = 0
        if gzipped:
            text = opened_file.read()
            for char in text:
                total_chars += 1
                if ord(char) is not 10:
                    new_line += char
                    continue
                else:
                    LOGGER.debug("Found a break point in the .tgz file")
                line = new_line
                lines.append(line)
                new_line = ""
            file_lines = lines
        else:
            file_lines = f

        file_info = os.stat(arg)
        total = 0
        total = file_info.st_size
        if gzipped:
            intermediate_total = total_chars
            total = int(intermediate_total * .98)

        #total *= files_count
        point = total / 100
        increment = total / 100
        old_total = -1
        for line in file_lines:
            #if gzip:
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
            #sys.stdout.flush()

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

    if len(namespace.filename) > 1:
        LOGGER.info("Attempting to resolve server names")
        result = address_matchup(db, coll_name)
        if result == 1:
            LOGGER.info("Server names successfully resolved")
        else:
            LOGGER.warning("Could not resolve server names")
        LOGGER.info('-' * 64)

    # event matchup
    LOGGER.info("Matching events across documents and logs...")
    events = event_matchup(db, coll_name)
    LOGGER.info("Completed event matchup")
    LOGGER.info('-' * 64)

    """"# generate frames
    LOGGER.info("Converting events into frames...")
    frames = generate_frames(events, db, coll_name)
    LOGGER.info("Completed frame conversion")
    LOGGER.info('-' * 64)

    # send to server
    LOGGER.info("Sending frames to server...")

    frames_json = open("frames.json", "w")
    json.dump(frames, frames_json)
    frames_json.close()

    server_names_json = open("names.json", "w")
    names = get_server_names(db, coll_name)
    json.dump(names, server_names_json)
    server_names_json.close()

    admin_info_json = open("admin.json", "w")
    admin = get_admin_info(file_names)
    json.dump(admin, admin_info_json)
    admin_info_json.close()"""
    # Create json file
    if not has_json:
        print "\nEdda is storing data under collection name {0}".format(coll_name)
        frames = generate_frames(events, db, coll_name)
        names = get_server_names(db, coll_name)
        admin = get_admin_info(file_names)
        large_json = open(coll_name + ".json", "w")
        large_dict = {}
        large_dict["frames"] = frames
        large_dict["names"] = names
        large_dict["admin"] = admin
        json.dump(large_dict, large_json)
    elif has_json:
        frames, names, admin = json_to_dicts(json_obj)
    send_to_js(frames, names, admin, http_port)
    LOGGER.info('-' * 64)
    LOGGER.info('=' * 64)
    LOGGER.warning('Completed post processing.\nExiting.')


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
    frames = large_dict["frames"]
    names = large_dict["names"]
    admin = large_dict["admin"]
    return frames, names, admin

if __name__ == "__main__":
    main()
