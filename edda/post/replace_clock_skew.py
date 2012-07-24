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
from datetime import timedelta


def replace_clock_skew(db, collName):
    logger = logging.getLogger(__name__)
    fixed_servers = {}
    first = True
    """"Using clock skew values that we have recieved from the
        clock skew method, fixes these values in the
        original DB, (.entries)."""""
    entries = db[collName + ".entries"]
    clock_skew = db[collName + ".clock_skew"]
    servers = db[collName + ".servers"]
    logger.debug("\n------------List of Collections------------"
        "\n".format(db.collection_names()))

    for doc in clock_skew.find():
        #if !doc["name"] in fixed_servers:
        logger.debug("---------------Start of first Loop----------------")
        if first:
            fixed_servers[doc["server_num"]] = 0
            first = False
            logger.debug("Our supreme leader is: {0}".format(
                doc["server_num"]))
        for server_num in doc["partners"]:
            if server_num in fixed_servers:
                logger.debug("Server name already in list of fixed servers. "
                    "EXITING: {}".format(server_num))
                logger.debug("---------------------------------------------\n")
                continue

            #could potentially use this
            largest_weight = 0
            largest_time = 0
            logger.debug("Server Name is: {0}".format(server_num))

            for skew in doc["partners"][server_num]:
                weight = doc["partners"][server_num][skew]
                logger.debug("Skew Weight is: {0}".format(weight))

                if abs(weight) > largest_weight:
                    largest_weight = weight
                    logger.debug("Skew value on list: {}".format(skew))
                    largest_time = int(skew)
                        #int(doc["partners"][server_name][skew])

            adjustment_value = largest_time
            logger.debug("Skew value: {}".format(largest_time))
            adjustment_value += fixed_servers[doc["server_num"]]
            logger.debug("Strung server name: {}".format(doc["server_num"]))

            logger.debug("Adjustment Value: {0}".format(adjustment_value))
            #weight = doc["partners"][server_num][skew]
            logger.debug("Server is added to list of fixed servers: {}")
            fixed_servers[server_num
                ] = adjustment_value + fixed_servers[doc["server_num"]]
            logger.debug("Officially adding: {0} to fixed "
                "servers".format(server_num))

            cursor = entries.find({"origin_server": server_num})
            if not cursor:
                continue

            for entry in cursor:
                logger.debug('Entry adjusted from: {0}'.format(entry["date"]))
                entry["adjusted_date"
                    ] = entry["date"] + timedelta(seconds=adjustment_value)

                entries.save(entry)
                logger.debug("Entry adjusted to: {0}"
                    "".format(entry["adjusted_date"]))
                logger.debug(entry["origin_server"])
