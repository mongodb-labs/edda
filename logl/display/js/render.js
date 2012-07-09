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

render = function(time) {
    // this function renders a single frame, based
    // on the time
    // could be more efficient than wiping everything every time...

    // check that there exists a corresponding frame
    if (frames[time]) {

    // wipe server layer and draw all servers
    canvases["server"].width = canvases["server"].width;
    var first = false;
    var prevx, prevy;
    var count = 0;
    var xvals = [], yvals = [];

    for (var name in frames[time]["servers"]) {
        var state = frames[time]["servers"][name];
	// add logic to parse out ".LOCKED"
	// to capture actual server state
	var n = state.split(".");
	state = n[0];
	console.log(state);
        switch(state) {
        case "PRIMARY":
	    primary(servers[name]["x"], servers[name]["y"], servers[name]["r"], contexts["server"]);
	    break;
        case "SECONDARY":
	    secondary(servers[name]["x"], servers[name]["y"], servers[name]["r"], contexts["server"]);
	    break;
        case "ARBITER":
	    arbiter(servers[name]["x"], servers[name]["y"], servers[name]["r"], contexts["server"]);
	    break;
        case "DOWN":
	    down(servers[name]["x"], servers[name]["y"], servers[name]["r"], contexts["server"]);
	    break;
        case "RECOVERING":
	    recovering(servers[name]["x"], servers[name]["y"], servers[name]["r"], contexts["server"]);
	    break;
        case "ROLLBACK":
	    rollback(servers[name]["x"], servers[name]["y"], servers[name]["r"], contexts["server"]);
	    break;
        case "FATAL":
	    fatal(servers[name]["x"], servers[name]["y"], servers[name]["r"], contexts["server"]);
	    break;
        case "UNKNOWN":
	    unknown(servers[name]["x"], servers[name]["y"], servers[name]["r"], contexts["server"]);
	    break;
	case "UNDISCOVERED":
	    undiscovered(servers[name]["x"], servers[name]["y"], servers[name]["r"], contexts["server"]);
	    break;
        case "REMOVED":
	    removed(servers[name]["x"], servers[name]["y"], servers[name]["r"], contexts["server"]);
	    break;
        }

	// add lock, if necessary
	if (n.length == 2) {
	    lock(servers[name]["x"], servers[name]["y"], servers[name]["r"]);
	}
        xvals[count] = servers[name]["x"];
        yvals[count] = servers[name]["y"];
        count++;
    }
    var xvals2 = xvals, yvals2 = yvals;
    for(var i = 0; i < count; i++) {
        for(var j = 0; j < count; j++) {
            one_line(xvals[i], yvals[i], xvals2[j], yvals2[j], contexts["arrow"]);
            one_arrow(100, 100, 200, 200, contexts["arrow"]);
        }
    }


    }
};