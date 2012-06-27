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


#Run this file after replace_clock_skew.py

#Anatomy of servers_list
#servers_list
    #{"Server1" : 


from pymongo import *
import logging
from datetime import *

def organize_servers(db, collName):
    servers_list = {}

    entries = db[collName + ".entries"]
    servers = db[collname + ".servers"]

    for server in servers.find():
        servers_list[server["origin_server"]] = []
        cursor = entries.find({"origin_server": server_name})
        cursor.sort("date") 
        for doc in cursor:
            servers_list[server["origin_server"]].add(doc)
    return servers_list
