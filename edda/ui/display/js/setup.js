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
layers = new Array("background", "shadow", "link", "arrow", "server");
canvases = {};
globalServers = {};
contexts = {};
replsets = {};
mongos = {};

CANVAS_W = 0;
CANVAS_H = 0;

// batch information
current_frame = 0;
batch_size = 100;
half_batch = parseInt(batch_size/2, 10);
trigger = parseInt(batch_size/4, 10);
frame_top = 0;
frame_bottom = 0;

// stored information
frames = {};
admin = {};
total_frame_count = 0;

// call various setup functions
function edda_setup() {
    canvases_and_contexts();
    connect();  // see connection.js
    time_setup(size(frames));
    visual_setup();
    version_number();
    file_names();
    mouse_over_setup();
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
    canvases_and_contexts();

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
        $("#timestamp").html("<b>Time:</b> " + frame["date"].substring(0, 50));
        $("#summary").html(frame["summary"]);
        $("#log_message_box").html(frame["log_line"]);

        // erase pop-up box
        $("#message_box").attr("visibility", "hidden");

        renderFrame(ui.value);

        // print witnesses, as hostnames
        var w = "";
        var s;
        for (s in frame["witnesses"]) {
            if (w !== "") w += "<br/>";
            w += server_label(globalServers, [frame["witnesses"][s]]);
        }
        $("#witnesses").html(w);

        // print dissenters, as hostnames
        var d = "";
        for (s in frame["dissenters"]) {
            if (d !== "") d += "<br/>";
            d += server_label(globalServers, frame["dissenters"][s]);
        }
        $("#dissenters").html(d);
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
