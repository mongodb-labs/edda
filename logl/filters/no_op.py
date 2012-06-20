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

#-------------------------------------------------

# right now we have the following structure for a document:

# "date" : date object
# "from_server" : string name, separate collection matching names to info
# "about_server" : string name, ditto
# "type" : either init, exit, etc...
# "msg" : stores the full line from the log


def store_in_db(db, msg, date):
    entry = {}
    entry["date"] = date
    entry["msg"] = msg
    db.loglines.insert(entry)
