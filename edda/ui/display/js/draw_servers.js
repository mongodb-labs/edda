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

var ICON_RADIUS = 20; // one radius to rule them all!
var ICON_STROKE = ICON_RADIUS > 18 ? 12 : 6;
var ICONS = {
    // state  : [ fill color, stroke color, dotted(bool) ]
    "PRIMARY" : ["#24B314", "#F0E92F", false],
    "SECONDARY" : ["#24B314", "#196E0F", false],
    "MONGOS-UP" : ["#DB9EBD", "#C969A8", false],
    "ROLLBACK" : ["#3F308F", "#1D0C37", false],
    "REMOVED" : ["#1C0E0B", "#9D7E51", true],
    "STALE" : ["#6E6134", "#4C4725", false],
    "FATAL" : ["#722714", "#722714", false],
    "RECOVERING" : ["#3FA5A9", "#2B4E66", false],
    "UNKNOWN" : ["#4E3629", "#9D7E51", true],
    "SHUNNED" : ["#706300", "403902", false],
    "UNDISCOVERED" : ["#4E3629", "#3B1E0B", false],
    "STARTUP1" : ["#4E3629", "#E1E2E5", false],
    "STARTUP2" : ["#85807D", "#E1E2E5", false],
    "ARBITER" : ["#BFB1A4", "#1A1007", false],
    "DOWN" : ["#4E3629", "#9D7E51", true],
    "MONGOS-DOWN" : ["#4E3629", "#9D7E51", true],
    "CONFIG-UP" : ["#706300", "403902", false],
    "CONFIG-DOWN" : ["#706300", "403902", false]
};

/* Render all server icons for a single point in time */
var drawServers = function(serverCoordinates, frame, ctx) {
    add_topology(serverCoordinates.clusterType, serverCoordinates.coordinates);

    for (var s in frame.servers) {
        if (frame.servers.hasOwnProperty(s)) {
            var coordinates = serverCoordinates.coordinates[s];
            
            /* Coords only calculated for servers present in this frame. */
            if (coordinates) {
                drawSingleServer(
                    coordinates.x,
                    coordinates.y,
                    frame.servers[s],
                    ctx);
            }
        }
    }
};

/* Render a single server icon for a point in time */
var drawSingleServer = function(x, y, type, ctx) {
    // parse out .LOCKED.
    var n = type.split(".");
    var state = n[0];

    // is it dotted?
    if (ICONS[state][2]) {
        drawCircle(x, y, ICON_RADIUS, ICONS[state][0], ICONS[state][0], ctx);
        drawDottedCircle(x, y, ICON_RADIUS, ICONS[state][1], ICON_STROKE, ctx);
    }
    else {
        drawCircle(x, y, ICON_RADIUS, ICONS[state][0], ICONS[state][1], ctx);
    }

    // if a special type, add details
    if (state == "PRIMARY") drawIconCrown(x, (y - 0.22*ICON_RADIUS),
                                          0.6*ICON_RADIUS, 0.5*ICON_RADIUS, ctx);
    else if (state == "ARBITER") drawIconStripes(x, y, ICON_RADIUS, ctx);
    else if (state == "UNKNOWN") drawIconQuestionMark(x, y, ICON_RADIUS, ctx);

    // if we had a lock, add a lock
    if (n.length > 1) {
        drawIconLock(x, y, ICON_RADIUS, ctx);
    }
};

function calculateServerCoordinates(frame) {
    var server_groups = frame["server_groups"];
    var serverCoordinates = {clusterType: null, coordinates: []};

    // first, figure out if this is a sharded cluster
    if (server_groups.length == 1) {
        serverCoordinates.clusterType = "replset";
        $("#clustername").html(server_groups[0]["name"]);
        ICON_RADIUS = 30;
        serverCoordinates.coordinates = generateIconCoords(
            frame,
            server_groups[0]["members"],
            CANVAS_W/2,
            CANVAS_H/2,
            CANVAS_H/2 - 60);
    }
    else {
        serverCoordinates.clusterType = "sharded";
        $("#clustername").html("Sharded Cluster");
        ICON_RADIUS = 15;
        // how many shards do we have?
        var shards = [];
        for (var k in server_groups) {
            var group = server_groups[k]
            if (group["type"] == "replSet") {
                rs = { "n" : group["name"] };
                shards.push(rs);
            }
        }
        // get center points for each shard
        // these will be in a dictionary with key "name".
        var shard_coords = generateIconCoords(
            frame,
            shards,
            CANVAS_W/2,
            CANVAS_H/2,
            CANVAS_H/2 - 70);

        // get coords for each server
        for (var g in server_groups) {
            var group = server_groups[g];
            var group_info = {};
            if (group["type"] == "replSet") {
                group_info = generateIconCoords(
                    frame,
                    group["members"],
                    shard_coords[group["name"]]["x"],
                    shard_coords[group["name"]]["y"],
                    50);

                // format replsets entry
                var members = [];
                for (var s in group["members"]) members.push(group["members"][s]["server_num"]);
                var rs = { "members" : members,
                           "x" : shard_coords[group["name"]]["x"],
                           "y" : shard_coords[group["name"]]["y"],
                           "r" : 50,
                           "on" : false };
                replsets[group["name"]] = rs;
                }
            else if (group["type"] == "mongos") {
                var mongos = generateIconCoords(
                    frame,
                    group["members"],
                    CANVAS_W/2,
                    CANVAS_H/2,
                    30);
                
                $.extend(serverCoordinates.coordinates, mongos);
            }
            // handle configs?
            else if (group["type"] == "config") {
                group_info = generateIconCoords(
                    frame,
                    group["members"],
                    CANVAS_W/2,
                    CANVAS_H/2,
                    CANVAS_W);
            }
            // merge into parent servers dictionary
            for (var s in group_info) {
                serverCoordinates[s] = group_info[s];
            }
        }
    }
    ICON_STROKE = ICON_RADIUS > 18 ? 12 : 6; // TODO:
    return serverCoordinates;
}

/*
 * Fill the #topology div with the structure of this cluster.
 */
function add_topology(clusterType, servers) {
    var topology = "";
    // standalone
    if (servers.length == 1) {
        topology = server_label(servers, servers.keys[0]);
    }
    // repl set
    else if (clusterType == "replset") {
        for (var server in servers) {
            topology += "- " + server_label(servers, server) + "<br/>";
        }
    }
    // sharded cluster
    else {
        for (var repl in replsets) {
            topology += repl + "<br/>";
            var replset = replsets[repl];
            for (var m in replset["members"]) {
                topology += "&nbsp;&nbsp;&nbsp; - ";
                topology += server_label(servers, replset["members"][m]) + "<br/>";
            }
        }
        topology += "Mongos<br/>";
        for (var server in mongos) {
            topology += "&nbsp;&nbsp;&nbsp; - ";
            topology += server_label(servers, server) + "<br/>";
        }
    }
    $("#topology").html(topology);
}

/*
 * Generate a label for this server, in most cases, the network name.
 */
function server_label(servers, num) {
    if (servers[num]) {
        if (servers[num]["network_name"] != "unknown")
            return servers[num]["network_name"];
        if (servers[num]["self_name"] != "unknown")
            return servers[num]["self_name"];
    }
    
    /* This server was not up at the time, no entry in frame. */
    return "";
}

/*
 * Generate coordinates for this group of servers.
 * "frame" is the current frame,
 * "group" is an array of server config documents by server_num,
 * "cx" and "cy" are the coordinates of the center of the
 * group, and "r" is the radius of the group.
 */
var generateIconCoords = function(frame, group, cx, cy, r) {
    var filteredGroup = {};
    var filteredIndex = 0;
    for (var serverNum in group) {
        if (frame.servers[parseInt(serverNum) + 1] != "UNDISCOVERED") {
            filteredGroup[filteredIndex] = group[serverNum];
            filteredIndex++;
        }
    }
    
    var count = Object.keys(filteredGroup).length;
    var all = {};

    switch(count) {
    case 0:
        return;
    case 1:
        var server = filteredGroup[0];
        server["x"] = cx;
        server["y"] = cy;
        server["on"] = false;
        server["type"] = "UNDISCOVERED";
        server["r"] = ICON_RADIUS;
        all[server["n"]] = server;
        return all;
    case 2:
        var s1 = filteredGroup[0];
        s1["x"] = cx + r;
        s1["y"] = cy;
        s1["on"] = false;
        s1["r"] = ICON_RADIUS;
        s1["type"] = "UNDISCOVERED";

        var s2 = filteredGroup[1];
        s2["x"] = cx - r;
        s2["y"] = cy;
        s2["on"] = false;
        s2["r"] = ICON_RADIUS;
        s2["type"] = "UNDISCOVERED";
        
        all[s1["n"]] = s1;
        all[s2["n"]] = s2;
        return all;
    }

    // all other numbers of servers are drawn on a circular pattern
    var xVal = 0;
    var yVal = 0;
    var start_angle = (count % 2 == 0) ? -45 : -90;
//    start_angle += Math.floor(Math.random()*90);

    for (var i = 0; i < count; i++) {
        xVal = (r * Math.cos(start_angle * (Math.PI)/180)) + cx;
        yVal = (r * Math.sin(start_angle * (Math.PI)/180)) + cy;
        var s = filteredGroup[i];
        s["x"] = xVal;
        s["y"] = yVal;
        s["on"] = false;
        s["r"] = ICON_RADIUS;
        s["type"] = "UNDISCOVERED";
        // TODO: why is it n or server_num??  
        if (s.hasOwnProperty("server_num"))
            all[s["server_num"]] = s;
        else all[s["n"]] = s;
        start_angle += 360/count;
    }
    return all;
};

/* Generate a dotted circle outline, with no fill */
var drawDottedCircle = function(x, y, r, color, wt, ctx) {
    ctx.strokeStyle = color;
    ctx.lineWidth = wt;
    var a = 0;
    var b = 0.05;
    while (b <= 2) {
        ctx.beginPath();
        ctx.arc(x, y, r, a*Math.PI, b*Math.PI, false);
        ctx.stroke();
        a += 0.08;
        b += 0.08;
    }
};

/* Draw the stripes for an Arbiter icon */
var drawIconStripes = function(x, y, r, ctx) {
    // right stripe
    ctx.fillStyle = "#33312F";
    ctx.beginPath();
    ctx.arc(x, y, r, -0.4 * Math.PI, -0.25 * Math.PI, false);
    ctx.lineTo(x + r * Math.sin(0.25 * Math.PI), y + r * Math.sin(45));
    ctx.arc(x, y, r, 0.25 * Math.PI, 0.4 * Math.PI, false);
    ctx.lineTo(x + r * Math.cos(0.4 * Math.PI), y - r * Math.sin(0.4 * Math.PI));
    ctx.fill();

    // left stripe
    ctx.beginPath();
    ctx.arc(x, y, r, -0.6 * Math.PI, -0.75 * Math.PI, true);
    ctx.lineTo(x - r * Math.sin(0.25 * Math.PI), y + r * Math.sin(45));
    ctx.arc(x, y, r, -1.25*Math.PI, -1.4*Math.PI, true);
    ctx.lineTo(x - r * Math.cos(0.4 * Math.PI), y - r * Math.sin(0.4*Math.PI));
    ctx.fill();

    // top circle, just for outline
    ctx.beginPath();
    ctx.arc(x, y, r, 0, 360, false);
    ctx.lineWidth = (r > 30) ? 4 : 2;
    ctx.strokeStyle = "#1A1007";
    ctx.stroke();
};

/* Draw a fairly generic circle of radius r, centered at (x,y) */
var drawCircle = function(x, y, r, fill, stroke, ctx) {
    ctx.fillStyle = fill;
    ctx.beginPath();
    ctx.arc(x,y, r, 0, 360, false);
    ctx.strokeStyle = stroke;
    ctx.lineWidth = ICON_STROKE;
    ctx.stroke();
    ctx.fill();
};

/* Render ? for a server in an Unknown state */
var drawIconQuestionMark = function(x, y, r, ctx) {
    ctx.font = "45pt Georgia";
    ctx.fillStyle = "#9D7E51";
    ctx.fillText("?", x - r / 4, y + (0.4*r));
};

/* Render a lock, for a locked server */
var drawIconLock = function(x, y, r, ctx) {
    var w = r/4;
    var h = 0.7 * r;
    var radius = h/4;
    var theta = Math.PI/8; // radians

    // draw the top circle
    ctx.beginPath();
    ctx.lineWidth = 10;
    ctx.arc(x, y - radius, radius, 0.5 * Math.PI - theta, 0.5 * Math.PI + theta, true);
    y = y - h/2;
    ctx.moveTo(x + (radius*Math.sin(theta)), y + h/2 - (radius - radius*Math.cos(theta)));
    ctx.lineTo(x + w, y + h);
    ctx.lineTo(x - w, y + h);
    ctx.lineTo(x - (radius*Math.sin(theta)), y + h/2 - (radius - radius*Math.cos(theta)));
    ctx.stroke();
    ctx.fillStyle = "#2D1F1C";
    ctx.fill();
};

/* Draw the crown for a Primary server */
var drawIconCrown = function(x, y, w, h, ctx) {
    ctx.beginPath();
    ctx.moveTo(x, y);
    // right side
    ctx.lineTo(x + w/5, y + h/2);
    ctx.lineTo(x + (2*w/5), y + h/5);
    ctx.lineTo(x + (3*w/5), y + (0.55)*h);
    ctx.lineTo(x + w, y + h/5);
    ctx.lineTo(x + (2*w/3), y + h);
    // left side
    ctx.lineTo(x - (2*w/3), y + h);
    ctx.lineTo(x - w, y + h/5);
    ctx.lineTo(x - (3*w/5), y + 0.55*h);
    ctx.lineTo(x - (2*w/5), y + h/5);
    ctx.lineTo(x - w/5, y + h/2);
    ctx.lineTo(x, y);
    // set fills and line weights
    ctx.lineWidth = 2; // consider setting dynamically for scaling
    ctx.lineJoin = "miter";
    ctx.stroke();
    // fill yellow
    ctx.fillStyle = "#F0E92F";
    ctx.fill();
};
