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


from logl.post.connection import *
from time import sleep
from datetime import datetime
from copy import deepcopy
from nose.plugins.skip import Skip, SkipTest


def test_send_to_js():
    """Test the send_to_js() method"""
    #raise SkipTest
    send_to_js(generate_msg())


def generate_msg():
    # these are sample frames, just for testing
    frames = {}
    frame = {}
    # first frame
    frame["time"] = str(datetime.now())
    frame["server_count"] = 15
    frame["user_count"] = 1
    frame["flag"] = False
    frame["servers"] = {}
    frame["users"] = {}
    frame["servers"]["samantha@home:27017"] = "PRIMARY"
    frame["servers"]["matthew@home:45234"] = "ARBITER"
    frame["servers"]["stewart@home:00981"] = "SECONDARY"
    frame["servers"]["carin@home:27017"] = "FATAL"
    frame["servers"]["kaushal@home:27017"] = "UNKNOWN"
    frame["servers"]["waterbottle@home:27017"] = "SECONDARY"
    frame["servers"]["cellphone@home:27017"] = "DOWN"
    frame["servers"]["notepad@home:27017"] = "ROLLBACK"
    frame["servers"]["laptop@home:27017"] = "RECOVERING"
    frame["servers"]["p@home:27017"] = "SECONDARY"
    frame["users"]["benjamin@home:10098"] = "USER"
    frame["syncs"] = {}
    frame["syncs"]["samantha@home:27017"] = "matthew@home:45234"
    frame["connections"] = {}
    frame["connections"]["benjamin@home:10098"] = "samantha@home:27017"
    # second frame
    frame1 = deepcopy(frame)
    frame2 = deepcopy(frame)
    frame3 = deepcopy(frame)
    frame1["servers"]["samantha@home:27017"] = "DOWN"
    frame2["servers"]["matthew@home:45234"] = "PRIMARY"
    frame2["servers"]["samantha@home:27017"] = "DOWN"
    frame3["servers"]["samantha@home:27017"] = "SECONDARY"
    frame3["servers"]["matthew@home:45234"] = "PRIMARY"

    frame["servers"]["waterbottle@home:27017"] = "PRIMARY"
    frame["servers"]["cellphone@home:27017"] = "PRIMARY"
    frame["servers"]["notepad@home:27017"] = "SECONDARY"
    frame["servers"]["laptop@home:27017"] = "ROLLBACK"
    frame["servers"]["p@home:27017"] = "DOWN"
    frames["0"] = deepcopy(frame)
    frames["1"] = deepcopy(frame1)
    frames["2"] = deepcopy(frame2)
    frames["3"] = deepcopy(frame3)
    frames["4"] = deepcopy(frame)
    frames["5"] = deepcopy(frame1)
    frames["6"] = deepcopy(frame2)
    frames["7"] = deepcopy(frame3)
    frames["8"] = deepcopy(frame)
    frames["9"] = deepcopy(frame1)
    frames["10"] = deepcopy(frame2)
    frames["11"] = deepcopy(frame3)
    frames["12"] = deepcopy(frame)
    frames["13"] = deepcopy(frame1)
    frames["14"] = deepcopy(frame2)
    frames["15"] = deepcopy(frame3)
    frames["16"] = deepcopy(frame)
    frames["17"] = deepcopy(frame1)
    frames["18"] = deepcopy(frame2)
    frames["19"] = deepcopy(frame3)
    frames["20"] = deepcopy(frame)
    count = 0
    while True:
        if count < 21:
            #sleep(1)
            frames[str(count)]["date"] = str(datetime.now())
            count += 1
            continue
        break
    return frames
