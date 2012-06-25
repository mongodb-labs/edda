# Copyright 2009-2012 10gen, Inc.
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

import json
import os
import webbrowser
import socket

# The documents this module
# generates will include the following information:

# time : (int, in seconds?)
# server_count : (int)
# body_count : (int)
# flag : (something conflicted about this view of the world? boolean)
# bodies (servers/users): [
       # name : (current_state, prev_state)...
# ]
# syncs: [
       # from_1 : to_1...
# ]
# user_conns: [
       # from_1 : to_1...
# ]

def generate_frames():
    """Generates frames to be passed to JavaScript
    client to be animated"""
    # for now, program will assume that all servers
    # view the world in the same way.  If it detects something
    # amiss between two or more servers, it will set the 'flag'
    # to true, but will do nothing further.
    pass


def send_to_js(data):
    """Sends information to the JavaScript
    client"""
    # open the JS page
    url = "file://"
    url += str(os.path.dirname(os.path.abspath(__file__)))
    url += "/../display/logl.html"
    webbrowser.open(url, 1, True)

    # open socket, bind and listen
    host = 'localhost'
    port = 28018
    size = 1024
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(backlog)

    # accept connection and send data
    client, address = s.accept()
    client.send(data)
    client.close()

    # return upon completion
    pass


