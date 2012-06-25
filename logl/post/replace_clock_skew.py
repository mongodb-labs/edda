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


#Make sure you run this file after you run clock_skew.py

#General plan of action for this method:
    #Run a loop to make sure you haven't already gone through the server that you are on.
    #It will run through the first time.
    #Loop for each entry in the partners field of the specific server that you are on
        #Isolate messages that have the origin server the same as the partners field
        #Loop through each message and adjust clock skew for each server individually
        #Along the way, add each server to a list that has already been checked. From here on out, we will only be going through servers not on this list

        #Move on to the next server and continue
    #Since the time deltas should be signed, we should be able to add the time skews of the different servers together. 
    #This should work for the case of the line of servers where every server is connected to every other server

# anatomy of a clock skew document:
# document = {
#    "type" = "clock_skew"
#    "server_name" = "name"
#    "partners" = {
#          server_name : 
#                [time_delay1, time_delay2, ...]: [weight]
#          }
#     }

import pymongo
import logging
import operator
from datetime import datetime
from datetime import timedelta

def fix_clock_skew(db, collName):
    fixed_servers = []#moving forward, make this a dictionary with a server_name field and a clock skew field that will constantly be added to. work on this first
    fixed_skews = {}
    first = True
    """"Using clock skew values that we have recieved from the
        clock skew method, fixes these values in the original DB, (.entries)."""""
    print 'I am here'
    entries = db[collName + ".entries"]

    logger = logging.getLogger(__name__)
    for doc in db[collName + ".clock_skews"].find():
        #the first thing that we suold do is make sure doc is not in fixed_servers. 
        #if !doc["name"] in fixed_servers:
        if first:
            fixed_skews[doc["name"]] = 0
            first = False
        for server_name in doc["partners"]:
            if(server_name in fixed_servers):
                continue
            fixed_servers.append(server_name)

            adjustment_value = max(server_name.iteritems(), key=operator.itemgetter(1))[0]
            adjustment_value += fixed_skews[doc["name"]]
            print "Adjustment Value: {}".format(adjustment_value)

            cursor = entries.find({"origin_server": server_name})
            for entry in cursor:
                entry["adjusted_date"] = entry["date"] + timedelta(seconds = adjustment_value)
