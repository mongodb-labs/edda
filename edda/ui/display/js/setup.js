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

// define program-wide global variables
var layers = new Array("background", "shadow", "link", "arrow", "server");
var canvases = {};
var contexts = {};
var servers = {};
var replsets = {};
var slider = {};

var CANVAS_W;
var CANVAS_H;

// batch information
var current_frame = 0;
var batch_size = 100;
var half_batch = parseInt(batch_size/2, 10);
var trigger = parseInt(batch_size/4, 10);
var frame_top;
var frame_bottom;

// stored information
var server_names;
var labels;
var frames;
var admin;
var total_frame_count;

// call various setup functions
function edda_setup() {
    canvases_and_contexts();
    mouse_over_setup();
    connect();  // see connection.js
    time_setup(size(frames));
    visual_setup();
    version_number();
    file_names();
}

/* set up canvases and associated contexts */
function canvases_and_contexts() {
    for (var i in layers) {
        canvases[layers[i]] = document.getElementById(layers[i] + "_layer");
        contexts[layers[i]] = canvases[layers[i]].getContext("2d");
    }
    CANVAS_W = canvases[layers[0]].width;
    CANVAS_H = canvases[layers[0]].height;
}

/* set up mouse-over functionality */
function mouse_over_setup() {
    canvases["server"].addEventListener("mousemove", onCanvasMouseover, false);
    canvases["server"].addEventListener("click", onCanvasClick, false);
}

// set up display-related things from frames
// generate coordinates
// set background to brown
function visual_setup() {
    var names = new Array();

    // clear all layers
    for (var name in layers) {
        canvases[layers[name]].width = canvases[layers[name]].width;
    }

    // color background
    var b_cvs = canvases["background"];
    var b_ctx = contexts["background"];
    b_ctx.beginPath();
    var w = b_cvs.width;
    var h = b_cvs.height;
    var grad = b_ctx.createRadialGradient(w/2, h/2, 180, w/2, h/2, h);
    grad.addColorStop(0, "#4E3629");
    grad.addColorStop(1, "#000000");
    b_ctx.rect(0, 0, w, h);
    b_ctx.fillStyle = grad;
    b_ctx.fill();

    // render first frame
    renderFrame("0");
}

// take the config from the server and parse it out
function parse_config(config) {
    // this is the format we want:
    // servers = {
    //    "1" : { "self_name" : "",
    //            "network_name" : "",
    //            "version" : "",
    //            "x" : x-coord,
    //            "y" : y-coord,
    //            "r" : ICON_RADIUS }
    // }

    // for replica sets:
    // replsets = {
    //     "name" : { 
    //            "members" : [ array of server_nums ],
    //            "x" : x-coord,
    //            "y" : y-coord,
    //            "r" : radius,
    //            "on" : boolean
    //            }
    // }

    // TODO: in the main server, protect against silly configurations
    // that may bother us here.

    // first, figure out if this is a sharded cluster
    if (config["groups"].length == 1) {
        $("#clustername").html(config["groups"][0]["name"]);
        ICON_RADIUS = 30;
        servers = generateIconCoords(config["groups"][0]["members"],
                                     CANVAS_W/2,
                                     CANVAS_H/2,
                                     CANVAS_H/2 - 60);
    }
    else {
        $("#clustername").html("Sharded Cluster");
        ICON_RADIUS = 15;
        // how many shards do we have?
        var shards = [];
        for (var k in config["groups"]) {
            var group = config["groups"][k]
            if (group["type"] == "replSet") {
                rs = { "n" : group["name"] };
                shards.push(rs);
            }
        }
        // get center points for each shard
        // these will be in a dictionary with key "name".
        shard_coords = generateIconCoords(shards,
                                    CANVAS_W/2,
                                    CANVAS_H/2,
                                    CANVAS_H/2 - 70);
        // get coords for each server
        servers = {};
        for (var g in config["groups"]) {
            var group = config["groups"][g];
            var group_info = {};
            if (group["type"] == "replSet") {
                console.log(group);
                group_info = generateIconCoords(group["members"],
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
                group_info = generateIconCoords(group["members"],
                                                CANVAS_W/2,
                                                CANVAS_H/2, 
                                                30);
                }
            // handle configs?
            else if (group["type"] == "config") {
                group_info = generateIconCoords(group["members"],
                                                CANVAS_W/2,
                                                CANVAS_H/2,
                                                CANVAS_W);
            }
            // merge into parent servers dictionary
            for (var s in group_info) {
                servers[s] = group_info[s]; 
            }
        }
    }
    console.log(replsets);
    console.log(servers);
    ICON_STROKE = ICON_RADIUS > 18 ? 12 : 6;
}

// set up slider functionality
function time_setup(max_time) {

    $("#slider").slider({ slide: function(event, ui) {
        // handle frame batches
        if (ui.value >= current_frame) { direction = 1; }
        else { direction = -1; }
        current_frame = ui.value
        frame = frames[current_frame];
        handle_batches();

        // set info divs
        $("#timestamp").html("<b>Time:</b> " + frame["date"].substring(5, 50));
        $("#summary").html(frame["summary"]);
        $("#log_message_box").html(frame["log_line"]);

        // erase pop-up box
        $("#message_box").attr("visibility", "hidden");

        // print witnesses, as hostnames
        var w = "";
        var s;
        for (s in frame["witnesses"]) {
            if (w !== "") w += "<br/>";
            w += server_label([frame["witnesses"][s]]);
        }
        $("#witnesses").html(w);

        // print dissenters, as hostnames
        var d = "";
        for (s in frame["dissenters"]) {
            if (d !== "") d += "<br/>";
            d += server_label(frame["dissenters"][s]);
        }
        $("#dissenters").html(d);

        renderFrame(ui.value);
    }});
    $("#slider").slider( "option", "max", total_frame_count - 2);
}

// handle frame batches
function handle_batches() {

    // do we even have to batch?
    if (total_frame_count <= batch_size) {
        return;
    }

    // handle case where user clicked entirely outside
    // aka load frames and then render
    if (current_frame > frame_top ||
    current_frame < frame_bottom) {
    // force some garbage collection?
        slide_batch_window();
    }

    // handle case where user is still within frame buffer
    // but close enough to edge to reload
    else if ((frame_top - current_frame < trigger && frame_top !== total_frame_count) ||
         (current_frame - frame_bottom < trigger && frame_bottom !== 0)) {
        // force some garbage collection?
        slide_batch_window();
    }
}

function slide_batch_window() {
    // get new frames
    frame_bottom = current_frame - half_batch;
    frame_top = current_frame + half_batch;

    // frame_bottom is less than 0
    if (frame_bottom < 0) {
        frame_bottom = 0;
        frame_top = batch_size;
    }

    // frame_top is past the last frame
    if (frame_top >= total_frame_count) {
        frame_top = total_frame_count - 1;
        frame_bottom = frame_top - batch_size;
    }
    get_batch(frame_bottom, frame_top);
}

// define .size function for object
// http://stackoverflow.com/questions/5223/length-of-javascript-object-ie-associative-array
function size(obj) {
    var len = 0, key;
    for (key in obj) {
        if(obj.hasOwnProperty(key))
            len++;
    }
    return len;
}

function version_number() {
    $("#version").html("Version " + admin["version"]);
    return;
}

function file_names() {
    var s = "";
    for (var i = 0; i < admin["file_names"].length; i++) {
        s += admin["file_names"][i];
        s += "<br/>";
    }
    $("#log_files").html(s);
}

/*
 * Generate a label for this server, in most cases, the network name.
 */
function server_label(num) {
    return servers[num]["network_name"] || 
           servers[num]["self_name"] ||
           "server " + num;
}
