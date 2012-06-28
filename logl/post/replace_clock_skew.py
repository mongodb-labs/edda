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

        #Move on  to the next server and continue
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

def replace_clock_skew(db, collName):
    logger = logging.getLogger(__name__)
    fixed_servers = {}
    first = True
    """"Using clock skew values that we have recieved from the
        clock skew method, fixes these values in the original DB, (.entries)."""""
    #print 'I am here'
    entries = db[collName + ".entries"]
    clock_skew = db[collName + ".clock_skew"]
    servers = db[collName + ".servers"]
    logger.debug("\n------------List of Collections------------\n".format(db.collection_names()))

    
    for doc in clock_skew.find():
        #the first thing that we suold do is make sure doc is not in fixed_servers. 
        #if !doc["name"] in fixed_servers:
        logger.debug("---------------Start of first Loop----------------")
        if first:
            fixed_servers[doc["server_num"]] = 0
            first = False
            logger.debug("Our supreme leader is: {0}".format(doc["server_num"]))
        for server_num in doc["partners"]:
            if server_num in fixed_servers:
                logger.debug("Server name already in list of fixed servers. EXITING: {}".format(server_num))
                logger.debug("------------------------------------------------------   \n")
                continue

            #could potentially use this
            largest_weight = 0
            largest_time = 0
            logger.debug("Server name: {}".format(server_num))
            logger.debug("Server Name is: {0}".format(server_num))

            for skew in doc["partners"][server_num]:
                logger.debug("you can't possibly miss this-------------------------------------------------------------------------------------------------")
                weight = doc["partners"][server_num][skew]
                logger.debug("Skew Weight is: {0}".format(weight))

                if abs(weight) > largest_weight:
                    largest_weight = weight
                    logger.debug("Skew value on list: {}".format(skew))
                    largest_time = int(skew)#int(doc["partners"][server_name][skew])

            adjustment_value = largest_time
            logger.debug("Skew value: {}".format(largest_time))
            adjustment_value += fixed_servers[doc["server_num"]]

            logger.debug("Adjustment Value: {0}".format(adjustment_value))
            #weight = doc["partners"][server_num][skew]
            logger.debug("Server is added to list of fixed servers: {}")
            fixed_servers[server_num] = adjustment_value
            logger.debug("Officially adding: {0} to fixed servers".format(server_num))

            server_cursor = servers.find({"server_num": int(server_num)})
            for server in server_cursor:
                cursor = entries.find({"origin_server": server["server_name"]})
            for entry in cursor:
                logger.debug('Entry adjusted from: {0}'.format(entry["date"]))

                entry["adjusted_date"] = entry["date"] + timedelta(seconds = adjustment_value)
                entries.save(entry)
                logger.debug('Entry adjusted to: {0}'.format(entry["adjusted_date"]))
                logger.debug(entry["origin_server"])
