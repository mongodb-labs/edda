// Copyright 2014 MongoDB, Inc.
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

var onCanvasMouseover = function(e) {
    var offset = $("#shadow_layer").offset();
    var x = e.clientX - offset.left;
    var y = e.clientY - offset.top;

    // check if mouse was over server
    for (var s in servers) {
        // calculate distance from click
        diffX = x - servers[s]["x"];
        diffY = y - servers[s]["y"];
        distance = Math.sqrt(Math.pow(diffX,2) + Math.pow(diffY,2));

        // is it within radius?
        if (distance <= ICON_RADIUS) {
            // check if that server is set to "true" for mouseover
            if (!servers[s]["on"]) {
                // make a shadow under server, and a sound
                servers[s]["on"] = true;
                var shadow = contexts["shadow"];

                // draw the drop shadow
                shadow.beginPath();
                shadow.arc(servers[s]["x"], servers[s]["y"], ICON_RADIUS, 0, 360, false);
                shadow.strokeStyle = "red";
                shadow.fillStyle = "rgba(10, 10, 10, 1)";
                shadow.lineWidth = 10;
                shadow.shadowColor = "black";
                shadow.shadowBlur = ICON_RADIUS + 30;
                shadow.fill();
                shadow.shadowBlur = 0;
            }
        }
        // if not in radius:
        else if (servers[s]["on"] == true){
            servers[s]["on"] = false;
            canvases["shadow"].width = canvases["shadow"].width;
        }
    }
};

/*
 * When we click on a server, pop up a message box with
 * information about that server.
 */
var onCanvasClick = function(e) {
    console.log("click!");
    var box = document.getElementById("message_box");
    var offset = $("#shadow_layer").offset();
    var x = e.clientX - offset.left;
    var y = e.clientY - offset.top;

    // are we currently over a server?
    for (var s in servers) {
        if (servers[s]["on"]) {
            info = server_names["network_name"][s] || server_names["self_name"] || "unknown";
            info += "<br/>" + frames[current_frame]["servers"][s];
            info += "<br/>" + server_names["version"][s];
            box.innerHTML = info;
            box.style.left = x + "px";
            box.style.top = y + "px";
            box.style.visibility = "visible";
            return;
        }
    }
    box.style.visibility = "hidden";
    console.log("not in a server");
    return;
};


is_over_server = function(e) {
    // check if a captured event happened over a server
    // if so, return that server's server_num
    var offset = $("#shadow_layer").offset();
    var x = e.clientX - offset.left;
    var y = e.clientY - offset.top;

    // check if mouse was over server
    for (server in servers) {

    // calculate distance from click
    diffX = x - servers[server]["x"];
    diffY = y - servers[server]["y"];
    distance = Math.sqrt(Math.pow(diffX,2) + Math.pow(diffY,2));
    // is it within radius?
    if (distance <= servers[server]["r"]) {
        return server;
    }
    }
    return null;
};
