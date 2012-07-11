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


import re
import string
import logging
from supporting_methods import capture_address

def criteria(msg):
    """Does the given log line fit the criteria for this filter?
    return an integer code if yes, -1 if not."""
    if string.find(msg, 'too stale to catch up') >= 0:
        return 0
    return -1


def process(msg, date):
    """if the given log line fits the criteria for this filter,
    processes the line and creates a document for it.
    document = {
       "date" : date,
       "type" : "stale",
       "info" : {
          "server" : host:port
       }
       "oritinal_message" : msg
    }"""
    message_type = criteria(msg)
    if message_type < 0:
        return None

    doc = {}
    doc["date"] = date
    doc["type"] = "stale"
    doc["info"] = {}
    doc["original_message"] = msg

    if message_type == 0:
        doc["info"]["state"] = "STALE"
        logger = logging.getLogger(__name__)

        addr = capture_address(msg[20:])
        if not addr:
            logger.debug("Unable to find target server going stale")
            return None
        doc["info"]["server"] = addr

    return doc
