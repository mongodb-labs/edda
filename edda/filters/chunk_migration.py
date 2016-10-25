# Copyright 2016 MongoDB, Inc.
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


import logging


def criteria(msg):
    """Does the given log line fit the criteria for this filter?
    If so, return an integer code.  Otherwise, return 0.
    """
    if 'Starting chunk migration' in msg:
        return 1
    if 'moveChunk.commit' in msg:
        return 2
    if 'moveChunk.abort' in msg:
        return 3
    if 'moveChunk data transfer progress' in msg:
        return 4
    return 0

def process(msg, date):
    """If the given log line fits the criteria for this filter,
    process the line and create a document of the following format:
    document = {
       "date" : date,
       "type" : "start_migration",
       "msg" : msg,
       "info" : {
          "server" : "self",
          }
    }

    For actual data transfer information:
    document = {
       "date" : date,
       "type" : "migration" or "commit_migration" or "abort_migration",
       "msg"  : msg,
       "info" : {
          "server"     : "self",
          "from_shard" : "string",
          "to_shard"   : "string"
       }
    """
    messageType = criteria(msg)
    if not messageType:
        return None

    doc = {}
    doc["date"] = date
    doc["info"] = {}
    doc["msg"] = msg

    # populate info
    doc["info"]["server"] = "self"

    # starts
    if messageType == 1:
        doc["type"] = "start_migration"
    # successful migrations
    elif messageType == 2:
        doc["type"] = "commit_migration"
    # aborted migrations
    elif messageType == 3:
        doc["type"] = "abort_migration"
    # progress messages
    elif messageType == 4:
        doc["type"] = "migration"
        label = "sessionId: \""
        shards = msg[msg.find(label) + len(label):].split('_')
        doc["info"]["from_shard"] = shards[0]
        doc["info"]["to_shard"] = shards[1]

    # clean this up
    if messageType == 2 or messageType == 3:
        from_label = "from: \""
        doc["info"]["from_shard"] = msg[msg.find(from_label) + len(from_label):].split("\"")[0]
        to_label = "to: \""
        doc["info"]["to_shard"] = msg[msg.find(to_label) + len(to_label):].split("\"")[0]

    logger = logging.getLogger(__name__)
    logger.debug(doc)
    return doc
