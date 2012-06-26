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
        #Along the way, add each server to a list that has already been checked. 
            #From here on out, we will only be going through servers not on this list

        #Move on to the next server and continue
    #Since the time deltas should be signed, we should be able to add the time skews of the different servers together. 
    #This should work for the case of the line of servers where every server is connected to every other server

# anatomy of a clock skew document:
# document = {
#    "type" = "clock_skew"
#    "server_name" = "name"
#    "partners" = {
#          server_name : 
#                [time_delay1 : weight1, time_delay2 : weight2, ...]
#          }
#     }

from pymongo import *
import logging
import operator
from datetime import datetime
from datetime import timedelta

def fix_clock_skew(db, collName):
    
    fixed_servers = {}
    first = True
    """"Using clock skew values that we have recieved from the
        clock skew method, fixes these values in the original DB, (.entries)."""""
    #print 'I am here'
    entries = db[collName + ".entries"]
    clock_skew = db[collName + ".clock_skew"]
    print db.collection_names()

    logger = logging.getLogger(__name__)
    for doc in clock_skew.find():
        #the first thing that we suold do is make sure doc is not in fixed_servers. 
        #if !doc["name"] in fixed_servers:
        print ""
        print "-----------------Start of first Loop-----------------"
        if first:
            fixed_servers[doc["server_name"]] = 0
            first = False
            print "Officially adding: {0} to fixed servers".format(doc["server_name"])
        for server_name in doc["partners"]:
            if(server_name in fixed_servers):
                print "Server name already in list of fixed servers. EXITING: " 
                print "------------------------------------------------------   \n"
                continue

            #could potentially use this
            largest_weight = 0
            largest_time = None
            print server_name
            print '                               '
            print "Server Name is: {0}".format(doc["partners"][server_name])
            print '                               '
            for skew in doc["partners"][server_name]:
                weight = doc["partners"][server_name][skew]
                print '                               '
                print "Skew Weight is: {0}".format(weight)
                print '                    '

                if weight > largest_weight:
                    largest_weight = weight
                    largest_time = int(skew)#int(doc["partners"][server_name][skew])

            adjustment_value = largest_time
            adjustment_value += fixed_servers[doc["server_name"]]

            print "Adjustment Value: {0}".format(adjustment_value)
            weight = doc["partners"][server_name][skew]
            fixed_servers[server_name] = adjustment_value
            print "Officially adding: {0} to fixed servers".format(server_name)

            cursor = entries.find({"origin_server": server_name})
            for entry in cursor:
                print 'Entry adjusted from: {0}'.format(entry["date"])

                entry["adjusted_date"] = entry["date"] + timedelta(seconds = adjustment_value)
                entries.save(entry)
                print 'Entry adjusted to: {0}'.format(entry["adjusted_date"])
                print entry["origin_server"]
