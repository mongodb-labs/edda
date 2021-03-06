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
    if '***** SERVER RESTARTED *****' in msg:
        return 1
    return 0


def process(msg, date):
    """If the given log line fits the criteria for this filter,
    process the line and create a document of the following format:
    document = {
       "date" : date,
       "type" : "restart",
       "msg" : msg,
       "info" : {
          "server" : "self"
          }
    }
    """
    if criteria(msg) == 0:
        return None

    doc = {}
    doc["date"] = date
    doc["type"] = "restart"
    doc["info"] = { "server" : "self" }

    logger = logging.getLogger(__name__)
    logger.debug(doc)
    return doc
