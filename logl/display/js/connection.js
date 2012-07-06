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

// without the async messing things up?
function connect() {
    $.ajax({
	    async: false,
		url: "http://localhost:28018/data.please",
		dataType: "json",
		success: function(data) {
		frames = data;
	    }
	});
};


// get frames from python using jquery
// this method is asynchronous!!
function connect_async() {
    $.getJSON("http://localhost:28018/data.please",
	      function(data) {
		  console.log("got data from the server:");
		  console.log(data);
		  frames = data;
		  console.log(frames);
		  console.log(frames["0"]);
		  render("0");
	      });
    //    render("0");
    //console.log(frames["0"]);
};

