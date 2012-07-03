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

var slider;

time_setup = function(max_time) {
    $("#slider").slider({
	    min: 0,
	    max: max_time,
	    step: 1,
	});
    $("slider").bind("slide", function(event, ui){
	    render(ui.value);
	    // and update the time in the timestamp div
	    document.getElementById("timestamp").innerHTML = frames[ui.value]["date"]
	});
};

sample_frames = function() {

    // first frame
    var frame_1 = {};
    frame_1["time"] = 0;
    frame_1["server_count"] = 1;
    frame_1["body_count"] = 1;
    frame_1["flag"] = false;
    frame_1["bodies"] = {};
    frame_1["bodies"]["Lucy"] = "secondary";
    frame_1["bodies"]["Abe"] = "primary";
    frame_1["syncs"] = {};
    frame_1["user_conns"] = {};

    // seconds frame
    var frame_2 = {};
    frame_2["time"] = 1;
    frame_2["server_count"] = 1;
    frame_2["body_count"] = 1;
    frame_2["flag"] = false;
    frame_2["bodies"] = {};
    frame_2["bodies"]["Abe"] = "secondary"
    frame_2["bodies"]["Lucy"] = "primary";
    frame_2["syncs"] = {};
    frame_2["user_conns"] = {};

    // add in server
    servers["Abe"] = {"x" : 300, "y" : 300, "r" : 50, "on" : false};
    servers["Lucy"] = {"x" : 500, "y" : 300, "r" : 50, "on" : false};

    // add frames to var frames
    frames["0"] = frame_1;
    frames["1"] = frame_2;

    // render first frame
    render(0);
};


render = function(time) {
    // this function renders a single frame, based
    // on the time
    // could be more efficient than wiping everything every time...

    // check that there exists a corresponding frame
    if (frames[time] != null) {

	// wipe server layer and draw all servers
	server_canvas = document.getElementById("server_layer");
	server_ctx = server_canvas.getContext("2d");
	server_canvas.width = server_canvas.width;

	for (var name in frames[time]["servers"]) {
	    var state = frames[time]["servers"][name];
	    console.log(state);
	    switch(state) {
	    case "PRIMARY":
		primary(servers[name]["x"], servers[name]["y"], servers[name]["r"], server_ctx);
		break;
	    case "SECONDARY":
		secondary(servers[name]["x"], servers[name]["y"], servers[name]["r"], server_ctx);
		break;
	    case "ARBITER":
		arbiter(servers[name]["x"], servers[name]["y"], servers[name]["r"], server_ctx);
		break;
	    case "DOWN":
		down(servers[name]["x"], servers[name]["y"], servers[name]["r"], server_ctx);
		break;
	    }
	}

	// wipe arrow layer and redraw all arrows
	arrow_canvas = document.getElementById("arrow_layer");
	arrow_canvas.width = arrow_canvas.width;
    }
};
