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

import unittest
from edda.ui.connection import * #Relative import error.
from time import sleep
from datetime import datetime
from copy import deepcopy
from nose.plugins.skip import Skip, SkipTest


class test_connection(unittest.TestCase):
    def dont_run_send_to_js(self):
        """Test the send_to_js() method"""
        raise SkipTest
        send_to_js(self.generate_msg())


    def test_sending_one_frame(self):
        raise SkipTest
        frame = {}
        frame2 = {}
        servers = ['sam', 'kaushal', 'kristina']
        frame = self.new_frame(servers)
        frame2 = self.new_frame(servers)
        frame['broken_links']['kaushal'] = ['kristina']
        frame["links"]['sam'] = ['kaushal', 'kristina']
        frame["links"]["water"] = ["kaushal", "sam", "kristina"]
        frame["servers"]["water"] = "PRIMARY"
        frame["servers"]["sam"] = "PRIMARY"
        frame["servers"]["kaushal"] = "SECONDARY"
        frame["servers"]["kristina"] = "DOWN"
        frame["summary"] = "This is a summary of the frame one."
        frames = {}
        frames["0"] = frame

        frame2["links"]["kaushal"] = ["sam"]
        frame2["links"]["water"] = ["kaushal", "sam", "kristina"]

        frame2["broken_links"]["kristina"] = ["sam", "kaushal", "water"]
        frame2["servers"]["sam"] = "PRIMARY"
        frame2["servers"]["kaushal"] = "DOWN"
        frame2["servers"]["kristina"] = "DOWN"
        frame2["servers"]["water"] = "PRIMARY"
        frame2["syncs"]["kaushal"] = ["sam", "kristina"]
        frame2["summary"] = "This is a summary of frame two."
        frames["1"] = frame2
        server_names = {}
        server_names["hostname"] = {}
        server_names["hostname"]["sam"] = "sam"
        server_names["hostname"]["kaushal"] = "UNKNOWN"
        server_names["hostname"]["kristina"] = "kristina"
        send_to_js(frames, server_names)


    def new_frame(self, servers):
        """Generate a new frame, with no links, broken_links,
        syncs, or users, and all servers set to UNDISCOVERED
        does not set the 'summary' field"""
        f = {}
        f["date"] = str(datetime.now())
        f["server_count"] = len(servers)
        f["witnesses"] = []
        f["summary"] = []
        f["dissenters"] = []
        f["flag"] = False
        f["links"] = {}
        f["broken_links"] = {}
        f["syncs"] = {}
        f["users"] = {}
        f["servers"] = {}
        for s in servers:
            f["servers"][s] = "UNDISCOVERED"
            f["links"][s] = []
            f["broken_links"][s] = []
            f["users"][s] = []
            f["syncs"][s] = []
        return f


    def generate_msg(self):
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
        frames["0"] = frame
        frames["1"] = frame1
        frames["2"] = frame2
        frames["3"] = frame3
        frames["4"] = frame
        frames["5"] = frame1
        frames["6"] = frame2
        frames["7"] = frame3
        frames["8"] = frame
        frames["9"] = frame1
        frames["10"] = frame2
        frames["11"] = frame3
        frames["12"] = frame
        frames["13"] = frame1
        frames["14"] = frame2
        frames["15"] = frame3
        frames["16"] = frame
        frames["17"] = frame1
        frames["18"] = frame2
        frames["19"] = frame3
        frames["20"] = frame
        count = 0
        while True:
            if count < 4:
                #sleep(1)
                frames[str(count)]["date"] = str(datetime.now())
                count += 1
                continue
            break
        return frames

if __name__ == '__main__':
    unittest.main()
