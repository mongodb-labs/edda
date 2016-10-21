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

#!/usr/bin/env python

from edda.supporting_methods import capture_address

def criteria(msg):
    """Does the given log line fit the criteria for this filter?
    If yes, return an integer code.  Otherwise, return -1.
    """
    # recognize a shard
    if 'starting new replica set monitor for replica set' in msg:
        return 1
    if 'Starting new replica set monitor for' in msg:
        return 2
    return 0

def process(msg, date):
    """If the given log line fits the critera for this filter,
    process it and create a document of the following format:
    doc = {
       "date" : date,
       "type" : "balancer",
       "msg" : msg,
       "origin_server" : name,
       "info" : {
          "subtype" : "new_shard",
          "replSet" : name,
          "members" : [ strings of server names ],
          "mongos"  : True/False
          }
    }
    """
    result = criteria(msg)
    if result == 0:
        return None

    doc = {}
    doc["date"] = date
    doc["type"] = "balancer"
    doc["msg"] = msg
    doc["info"] = {}

    doc["info"]["mongos"] = False
    if '[mongosMain]' in msg:
        doc["info"]["mongos"] = True

    if result == 1:
        # get replica set name and seeds
        a = msg.split("starting new replica set monitor for replica set")
        b = a[1].split()
        doc["info"]["subtype"] = "new_shard"
        doc["info"]["replSet"] = b[0]
        doc["info"]["members"] = b[3].split(',')
        doc["info"]["server"] = "self"
        return doc

    if result == 2:
        # updated parsing for 3.4
        a = msg.split("Starting new replica set monitor for ")
        b = a[1].split('/')
        doc["info"]["subtype"] = "new_shard"
        doc["info"]["replSet"] = b[0]
        doc["info"]["members"] = b[1].split(',')
        doc["info"]["server"] = "self"
        print "returning shard doc " + str(doc)
        return doc

    return None
