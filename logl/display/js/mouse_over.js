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


on_canvas_mouseover = function(e) {
    var x = e.clientX;
    var y = e.clientY;

    // check if mouse was over server
    for (server in servers) {

	// calculate distance from click
	diffX = x - servers[server]["x"];
	diffY = y - servers[server]["y"];
	distance = Math.sqrt(Math.pow(diffX,2) + Math.pow(diffY,2));
	console.log("Distance is: %d", distance);
	console.log("Xcenter: %d, Ycenter: %d", servers[server]["x"], servers[server]["y"]);
	console.log("Xactual: %d, Yactual: %d",x, y);
		// is it within radius?
		if (distance <= servers[server]["r"]) {
			// check if that server is set to "true" for mouseover
			if (!servers[server]["on"]) {
			    // make a shadow under server, and a sound
			    servers[server]["on"] = true;
			    var shadow = contexts["shadow"]

				// draw the drop shadow
				shadow.beginPath();
			    shadow.arc(servers[server]["x"], servers[server]["y"], servers[server]["r"], 0, 360, false);
			    shadow.strokeStyle = "red";
			    shadow.fillStyle = "rgba(10, 10, 10, 1)";
			    shadow.lineWidth = 10;
			    shadow.shadowColor = "black";
			    shadow.shadowBlur = servers[server]["r"] + 50;
			    shadow.fill();
			    shadow.shadowBlur = 0;

			    // text box over
			    var message = contexts["message"];
			    message.fillStyle = "black";
			    message.rect(x, y, 100, 100);
			}
		}
		// also make sure that we turn the mousing-over off!!
		// add this back in
    }
};
