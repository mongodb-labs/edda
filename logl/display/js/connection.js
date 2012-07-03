// Copyright 2009-2012 10gen, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

poll = function() {
    // the python server always listens at localhost:28018

    // should probably check browser compatability
    var xmlhttp;

    // send a phony "GET" request
    xmlhttp = new XMLHttpRequest();
    xmlhttp.open("GET", "http://localhost:28018/data.please", true);
    xmlhttp.send();

    // receive information from server
    xmlhttp.onreadystatechange = function() {
	frames = jQuery.parseJSON(xmlhttp.responseText);
	var names = new Array();
	console.log(frames["0"]);
	for (var name in frames["0"]["servers"]) {
	    names.push(name);
	}
	// change time values of slider
	time_setup(frames.size);
	generate_coords(frames["0"]["server_count"], names);
	console.log(servers)
	render("0");
	// also, get rid of default drawing of first frame
	// and get rid of the "Message from Python" line
    };
};

// thanks http://stackoverflow.com/questions/5223/length-of-javascript-object-ie-associative-array
Object.size = function(obj) {
    var size = 0, key;
    for (key in obj) {
	if (obj.hasOwnProperty(key)) size++;
    }
    return size;
};
