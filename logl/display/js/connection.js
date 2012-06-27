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
	console.log(xmlhttp.responseText);
	document.getElementById("msg").innerHTML = xmlhttp.responseText;
    };
};
