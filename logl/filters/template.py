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

#!/usr/bin/env python


def criteria(msg):
    """Does the given log line fit the criteria for this filter?
    If yes, return an integer code.  Otherwise return 0.
    """
    # perform a check or series of checks here on msg
    raise NotImplementedError


def process(msg, date):
    """If the given log line fits the critera for this filter,
    processes the line and creates a document for it of the
    following format:
    doc = {
         "date" : date,
         "msg"  : msg,
         "type" : (name of filter),
         "info" : {
                "server" : "host:port" or "self",
                (any additional fields)
                }
    }
    """

    # doc = {}
    # doc["date"] = date
    # doc["msg"] = msg
    # doc["type"] = "your_filter_name"
    # doc["info"] = {}
    # etc.
    raise NotImplementedError
