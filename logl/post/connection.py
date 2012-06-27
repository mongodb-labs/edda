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

import os
from SocketServer import BaseServer
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

try:
    from OpenSSL import SSL
except ImportError:
    pass

import socket
import sys
import webbrowser

try:
    import json
except ImportError:
    import simplejson as json


def send_to_js(data):
    """Sends information to the JavaScript
    client"""
    # open the JS page
    url = "http://localhost:27080"
    url += str(os.path.dirname(os.path.abspath(__file__)))
    url += "/../display/logl.html"
    webbrowser.open(url, 1, True)

    # open socket, bind and listen
    print "Opening server"
    try:
        server = HTTPServer(('', 28018), LoglHTTPRequest)
    except socket.error, (value, message):
        if value == 98:
            print "could not bind to localhost:28018"
        else:
            print message
        return

    print 'listening for connections on http://localhost:28018\n'
    server.serve_forever()

    # return upon completion
    return

class LoglHTTPRequest(BaseHTTPRequestHandler):

    def do_GET(self):
        # do nothing with message
        # return data
        print 'got a GET request'
        self.send_response(200, 'OK')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("Hi, Javascript, it's me, Python!")

        # serve up logl.html
        f = open(docroot + path, 'r')
        self.send_response(200, 'OK')
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(f.read())
        f.close()
        return

