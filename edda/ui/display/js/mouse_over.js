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

/*
 * On mouseover, draws a drop shadow under any server or
 * replica set that we've selected.
 */
var onCanvasMouseover = function(e) {
    if (mouseoverNodes(servers, e)) return;
    mouseoverNodes(replsets, e);
};

/*
 * Given a group of nodes, check if we are mousing over any of them,
 * and respond by drawing a drop shadow. Return true if we were over
 * any of the nodes, false if over none.
 */
var mouseoverNodes = function(nodes, e) {
    for (var n in nodes) {
        var node = nodes[n];
        if (isOverNode(node, e)) {
            if (node["on"]) return true;
            drawDropShadow(node);
            nodes[n]["on"] = true;
            return true;
        }
        else {
            if (node["on"]) undrawDropShadows();
        }
    }
    return false;
};

/*
 * Draw a drop shadow under a server or replica set.
 */
var drawDropShadow = function(node) {
    undrawDropShadows();
    var shadow = contexts["shadow"];
    shadow.beginPath();
    shadow.arc(node["x"], node["y"], node["r"], 0, 360, false);
    shadow.strokeStyle = "red";
    shadow.fillStyle = "rgba(10, 10, 10, 1)";
    shadow.lineWidth = 10;
    shadow.shadowColor = "black";
    shadow.shadowBlur = node["r"] + 30;
    shadow.fill();
    node["on"] = true;
};

/*
 * Erase all drop shadows, and turn off all nodes.
 */
var undrawDropShadows = function() {
    for (var n in replsets) replsets[n]["on"] = false;
    for (var n in servers) servers[n]["on"] = false;
    canvases["shadow"].width = canvases["shadow"].width;
};

/*
 * When we click on a server, pop up a message box with
 * information about that server.
 */
var onCanvasClick = function(e) {
    for (var s in servers) {
        if (isOverNode(servers[s], e)) {
            var info = server_label(servers, s);
            info += "<br/>" + frames[current_frame]["servers"][s];
            info += "<br/>" + servers[s]["version"];
            formatInfoBox(info, e);
            return;
        }
    }
    for (var rs in replsets) {
        var repl = replsets[rs];
        if (isOverNode(repl, e)) {
            var info = "Replica set " + rs + "<br/>";
            info += "Members: <br/>";
            for (var i = 0; i < repl["members"].length; i++) {
                info += "&nbsp;&nbsp;&nbsp;";
                info += server_label(servers, repl["members"][i]) + "<br/>";
            }
            formatInfoBox(info, e);
            return;
        }
    }
    hideInfoBox();
    return;
};

/*
 * Fill the info box with this message and display at the
 * correct coordinates.
 */
var formatInfoBox = function(msg, e) {
    var offset = $("#shadow_layer").offset();
    var x = e.clientX - offset.left;
    var y = e.clientY - offset.top;
    $("#message_box").html(msg);
    $("#message_box").css({ left : x + 'px' });
    $("#message_box").css({ top : y + 'px' });
    showInfoBox();
};

/*
 * Show the info box.
 */
var showInfoBox = function() {
    $("#message_box").show();
};

/*
 * Hide the info box.
 */
var hideInfoBox = function() {
    $("#message_box").hide();
};

/*
 * Is the mouse over this node?
 */
var isOverNode = function(node, e) {
    var offset = $("#shadow_layer").offset();
    var x = e.clientX - offset.left;
    var y = e.clientY - offset.top;
    diffX = x - node["x"];
    diffY = y - node["y"];
    distance = Math.sqrt(Math.pow(diffX,2) + Math.pow(diffY,2));
    if (distance <= node["r"]) return true;
    return false;
};
