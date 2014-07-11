# Copyright 2014 MongoDB, Inc.
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
"""Edda reads in from MongoDB log files and parses them.
After storing the parsed data in a separate collection,
the program then uses this data to provide users with a
visual tool to help them analyze their servers.

Users can customize this tool by adding their own parsers
to the edda/filters/ subdirectory, following the layout specified
in edda/filters/template.py.
"""
__version__ = "0.7.0+"

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
from ui.frames import generate_frames, update_frames_with_config
from ui.connection import send_to_js

LOGGER = None
PARSERS = [
    rs_status.process,
    fsync_lock.process,
    rs_sync.process,
    init_and_listen.process,
    stale_secondary.process,
    rs_exit.process,
    rs_reconfig.process,
    balancer.process
]

def main():
    if (len(sys.argv) < 2):
        print "Missing argument: please provide a filename"
        return

    # parse command-line arguments
    parser = argparse.ArgumentParser(
    description='Process and visualize log files from mongo servers')
    parser.add_argument('--port', help="Specify the MongoDb port to use")
    parser.add_argument('--http_port', help="Specify the HTTP Port")
    parser.add_argument('--host', help="Specify host")
    parser.add_argument('--json', help="json file")
    parser.add_argument('--verbose', '-v', action='count')
    parser.add_argument('--version', action='version',
                        version="Running edda version {0}".format(__version__))
    parser.add_argument('--db', '-d', help="Specify DB name")
    parser.add_argument('--collection', '-c')
    parser.add_argument('filename', nargs='+')
    namespace = parser.parse_args()

    has_json = namespace.json or False
    http_port = namespace.http_port or '28000'
    port = namespace.port or '27017'
    coll_name = namespace.collection or str(objectid.ObjectId())
    if namespace.host:
        host = namespace.host
        m = host.find(":")
        if m > -1:
            port = host[m + 1]
            host = host[:m]
    else:
        host = 'localhost'
    uri = "mongodb://" + host + ":" + port

    # configure logging
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
    config = db[coll_name].config

    # first, see if we've gotten any .json files
    for file in namespace.filename:
        if ".json" in file:
            LOGGER.debug("Loading in edda data from {0}".format(file))
            json_file = open(file, "r")
            data = json.loads(json_file.read())
            send_to_js(data["frames"],
                       data["admin"],
                       http_port)
            edda_cleanup(db, coll_name)
            return
            
    # were we supposed to have a .json file?
    if has_json:
        LOGGER.critical("--json option used, but no .json file given")
        return

    # run full log processing
    processed_files = []
    for filename in namespace.filename:
        if filename in processed_files:
            continue
        logs = extract_log_lines(filename)
        process_log(logs, servers, entries, config)
        processed_files.append(filename)

    # anything to show?
    if servers.count() == 0:
        LOGGER.critical("No servers were found, exiting")
        return
    if entries.count() == 0:
        LOGGER.critical("No meaningful events were found, exiting")
        return

    # match up addresses
    if len(namespace.filename) > 1:
        if address_matchup(db, coll_name) != 1:
            LOGGER.warning("Could not resolve server names")

    # match up events
    events = event_matchup(db, coll_name)
    
    frames = generate_frames(events, db, coll_name)
    server_config = get_server_config(servers, config)
    update_frames_with_config(frames, server_config)
    admin = get_admin_info(processed_files)

    LOGGER.critical("\nEdda is storing data under collection name {0}"
                    .format(coll_name))
    edda_json = open(coll_name + ".json", "w")
    json.dump(format_json(frames, admin), edda_json)

    send_to_js(frames, admin, http_port)
    edda_cleanup(db, coll_name)


def edda_cleanup(db, coll_name):
    """ Clean up collections created during run.
    """
    db.drop_collection(coll_name + ".servers")
    db.drop_collection(coll_name + ".entries")


def extract_log_lines(filename):
    """ Given a file, extract the lines from this file
    and return in an array.
    """
    # handle gzipped files
    if ".gz" in filename:
        LOGGER.debug("Opening a gzipped file")
        try:
            file = gzip.open(filename, 'r')
        except IOError as e:
            LOGGER.warning("\nError: Unable to read file {0}".format(filename))
            return []
    else:
        try:
            file = open(filename, 'r')
        except IOError as e:
            LOGGER.warning("\nError: Unable to read file {0}".format(filename))
            return []

    return file.read().split('\n')


def process_log(log, servers, entries, config):
    """ Go through the lines of a log file and process them.
    Save stuff in the database as we go?  Or save later?
    """
    mongo_version = None
    upgrade = False
    previous = ""
    line_number = 0
    server_num = get_server_num("unknown", False, servers)

    for line in log:
        date = date_parser(line)
        if not date:
            LOGGER.debug("No date found, skipping")
            continue
        doc = filter_message(line, date)
        if not doc:
            LOGGER.debug("No matching filter found")
            continue

        # We use a server number to associate these messages
        # with the current server.  If we find an address for the server,
        # that's even better, but if not, at least we have some ID for it.
        if (doc["type"] == "init" and
            doc["info"]["subtype"] == "startup"):
            assign_address(server_num,
                           str(doc["info"]["addr"]), True, servers)
            assign_server_type(server_num, str(doc["info"]["type"]), servers)
            
        # balancer messages
        if doc["type"] == "balancer":
            if (doc["info"]["subtype"] == "new_shard"):
                # add this shard to the config collection
                add_shard({ "replSet" : doc["info"]["replSet"],
                            "members" : doc["info"]["members"],
                            "member_nums" : [] }, config)
                # TODO: capture config servers in a similar way
                # we are a mongos, add us!
                add_shard({ "replSet" : "mongos",
                            "members" : [],
                            "member_nums" : [ server_num ] }, config)

        # startup options, config server?
        if doc["type"] == "startup_options":
            # TODO: a server might report its replica set here.
            if "replSet" in doc["info"]:
                add_shard({ "replSet" : doc["info"]["replSet"],
                            "members" : [],
                            "member_nums" : [ server_num ] }, config)
            if doc["info"]["options"].find("configsvr: true") > -1:
                assign_server_type(server_num, "configsvr", servers)
                # add ourselves to list of configsvrs
                add_shard({ "replSet" : "configsvr",
                            "members" : [],
                            "member_nums" : [ server_num ] }, config)

        if (doc["type"] == "status" and
            "addr" in doc["info"]):
            LOGGER.debug("Found addr {0} for server {1} from rs_status msg"
                         .format(doc["info"]["addr"], server_num))
            assign_address(server_num,
                           str(doc["info"]["addr"]), False, servers)
            #assign_server_type(server_num, "mongod", servers)
            # if this is a mongos, make MONGOS-UP
            if server_type(server_num, servers) == "mongos":
                doc["info"]["state"] = "MONGOS-UP"
                doc["info"]["state_code"] = 50 # todo: fix.

        if doc["type"] == "version":
            update_mongo_version(doc["version"], server_num, servers)
            # is this an upgrade?
            if mongo_version and mongo_version != doc["version"]:
                upgrade = True
                # TODO: add a new event for a server upgrade?
                # perhaps we should track startups with a given server.
                # This would be nicer than just "status init" that happens now:
                #
                # 'server 4' was started up
                #        - version number
                #        - options, build info

        if doc["type"] == "startup_options":
            # TODO: save these in some way.
            continue

        if doc["type"] == "build_info":
            # TODO: save these in some way.
            continue

        # skip repetitive exit messages
        if doc["type"] == "exit" and previous == "exit":
            continue

        # format and save to entries collection
        previous = doc["type"]
        doc["origin_server"] = server_num
        doc["line_number"]   = line_number
        doc["log_line"]      = line 
        entries.insert(doc)
        LOGGER.debug("Stored line to db: \n{0}".format(line))
        line_number += 1


def filter_message(msg, date):
    """ Pass this log line through a number of filters.
    The first filter that finds a match will return
    a document, which this function will return to the caller.
    """
    for process in PARSERS:
        doc = process(msg, date)
        if doc:
            return doc

def get_server_config(servers, config):
    """Format the information in the .servers collection
    into a data structure to be send to the JS client.
    The document should have this format:
    server_config = {
       groups : [
          { "name" : "replSet1",
            "type" : "replSet",
            "members" : [ 
                { "n" : 1,
                  "self_name" : "localhost:27017",
                  "network_name" : "SamanthaRitter:27017",
                  "version" : "2.6.0.rc1" } ] },
          { "name" : "Mongos",
            "type" : "mongos",
            "members" : [ ... ] },
          { "name" : "Configs",
            "type" : "configs",
            "members" : [ ... ] } 
        ]
    }
    """
    groups = []

    # attach each replica set
    for rs_doc in config.find():
        rs_group = { "name" : rs_doc["replSet"], "members" : [] }

        # set the type
        if rs_doc["replSet"] == "mongos":
            rs_group["type"] = "mongos"
        elif rs_doc["replSet"] == "configsvr":
            rs_group["type"] = "config"
        else:
            rs_group["type"] = "replSet"

        for num in rs_doc["member_nums"]:
            # get the server doc and append it to this group
            s = servers.find_one({ "server_num" : num }, { "_id" : 0 })
            rs_group["members"].append(s)
        
        groups.append(rs_group)

    server_config = { "groups" : groups }
    return server_config


def format_json(frames, admin):
    return {"frames": frames, "admin": admin}


def get_admin_info(files):
    """ Format administrative information to send to JS client
    """
    return { "file_names" : files, "version" : __version__ }


if __name__ == "__main__":
    main()
