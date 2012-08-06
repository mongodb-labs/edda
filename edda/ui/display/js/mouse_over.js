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
        // check if that server is set to "true" for mouseover
        if (!servers[server]["on"]) {
        // make a shadow under server, and a sound
        servers[server]["on"] = true;
        var shadow = contexts["shadow"];

        // draw the drop shadow
        shadow.beginPath();
        shadow.arc(servers[server]["x"], servers[server]["y"], servers[server]["r"], 0, 360, false);
        shadow.strokeStyle = "red";
        shadow.fillStyle = "rgba(10, 10, 10, 1)";
        shadow.lineWidth = 10;
        shadow.shadowColor = "black";
        shadow.shadowBlur = servers[server]["r"] + 30;
        shadow.fill();
        shadow.shadowBlur = 0;
        }
    }

    // if not in radius:
    else if (servers[server]["on"] === true){
        servers[server]["on"] = false;
        canvases["shadow"].width = canvases["shadow"].width;
    }
    }
};


new_click = function(e) {
    // when a user clicks on a server, pop up a box with information about that server
    var box = document.getElementById("message_box");
    var offset = $("#shadow_layer").offset();
    var x = e.clientX - offset.left;
    var y = e.clientY - offset.top;

    // check if mouse was over server
    var s = is_over_server(e);
    if (s === null) {
    box.style.visibility = "hidden";
    return;
    }

    var info = "Number: " + s;
    info += "<br/>Name: " + server_names["self_name"][s];
    info += "<br/>Network Name: " + server_names["network_name"][s];
    info += "<br/>State: " + frames[current_frame]["servers"][s];
    info += "<br/>Mongo_version: " + server_names["version"][s];
    box.innerHTML = info;
    box.style.left = x + "px";
    box.style.top = y + "px";
    box.style.visibility = "visible";
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
