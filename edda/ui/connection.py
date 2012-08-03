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
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

import socket
import webbrowser

try:
    import json
except ImportError:
    import simplejson as json
import threading

data = None
server_list = None
admin = None


def run(http_port):
    """Open page and send GET request to server"""
    # open the JS page
    url = "http://localhost:" + http_port
    try:
        webbrowser.open(url, 1, True)
    except webbrowser.Error as e:
        print "Webbrowser failure: Unable to launch webpage:"
        print e
        print "Enter the following url into a browser to bring up edda:"
        print url
    # end of thread


def send_to_js(frames, servers, info, http_port):
    """Sends information to the JavaScript
    client"""

    global data
    global server_list
    global admin

    admin = info
    data = frames
    server_list = servers

    # fork here!
    t = threading.Thread(target=run(http_port))
    t.start()
    # parent starts a server listening on localhost:27080
    # child opens page to send GET request to server
    # open socket, bind and listen
    print " \n"
    print "================================================================="
    print "Opening server, kill with Ctrl+C once you are finished with edda."
    print "================================================================="
    try:
        server = HTTPServer(('', int(http_port)), eddaHTTPRequest)
    except socket.error, (value, message):
        if value == 98:
            print "Error: could not bind to localhost:28018"
        else:
            print message
            return
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()
        # return upon completion
        print "Done serving, exiting"
        return


class eddaHTTPRequest(BaseHTTPRequestHandler):

    mimetypes = mimetypes = {"html": "text/html",
                  "htm": "text/html",
                  "gif": "image/gif",
                  "jpg": "image/jpeg",
                  "png": "image/png",
                  "json": "application/json",
                  "css": "text/css",
                  "js": "text/javascript",
                  "ico": "image/vnd.microsoft.icon"}

    docroot = str(os.path.dirname(os.path.abspath(__file__)))
    docroot += "/display/"

    def process_uri(self, method):
        """Process the uri"""
        if method == "GET":
            (uri, q, args) = self.path.partition('?')
        else:
            return

        uri = uri.strip('/')

        # default "/" to "edda.html"
        if len(uri) == 0:
            uri = "edda.html"

        # find type of file
        (temp, dot, file_type) = uri.rpartition('.')
        if len(dot) == 0:
            file_type = ""

        return (uri, args, file_type)

    def do_GET(self):
        # do nothing with message
        # return data
        (uri, args, file_type) = self.process_uri("GET")

        if len(file_type) == 0:
            return

        if file_type == "admin":
            #admin = {}
            admin["total_frame_count"] = len(data)
            self.send_response(200)
            self.send_header("Content-type", 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(admin))

        elif file_type == "all_frames":
            self.wfile.write(json.dumps(data))

        # format of a batch request is
        # 'start-end.batch'
        elif file_type == "batch":
            uri = uri[:len(uri) - 6]
            parts = uri.partition("-")
            try:
                start = int(parts[0])
            except ValueError:
                start = 0
            try:
                end = int(parts[2])
            except ValueError:
                end = 0
            batch = {}

            # check for entries out of range
            if end < 0:
                return
            if start < 0:
                start = 0;
            if start >= len(data):
                return
            if end >= len(data):
                end = len(data) - 1

            for i in range(start, end):
                if not str(i) in data:
                    break
                batch[str(i)] = data[str(i)];

            self.send_response(200)
            self.send_header("Content-type", 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(batch))


        elif file_type == "servers":
            self.send_response(200)
            self.send_header("Content-type", 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(server_list))

        elif file_type in self.mimetypes and os.path.exists(self.docroot + uri):
            f = open(self.docroot + uri, 'r')

            self.send_response(200, 'OK')
            self.send_header('Content-type', self.mimetypes[file_type])
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
            return

        else:
            self.send_error(404, 'File Not Found: ' + uri)
            return
