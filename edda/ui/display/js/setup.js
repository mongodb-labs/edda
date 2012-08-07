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

// A centralized file for all the JS setup details

// define program-wide global variables
var layers = new Array("background", "shadow", "link", "arrow", "server");
var canvases = {};
var contexts = {};
var servers = {};
var slider = {};

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

// set up canvases and associated contexts
function canvases_and_contexts() {
    for (var i in layers) {
    canvases[layers[i]] = document.getElementById(layers[i] + "_layer");
    contexts[layers[i]] = canvases[layers[i]].getContext("2d");
    }
}


// set up mouse-over functionality
function mouse_over_setup() {
    canvases["server"].addEventListener("mousemove", on_canvas_mouseover, false);
    canvases["server"].addEventListener("click", new_click, false);
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

    if (frames) {
        if (frames["0"]) {
            for (var name in frames["0"]["servers"]) {
                names.push(name);
            }
            generate_coords(names.length, names);
        }
    }

    // render first frame
    render("0");
}


// set up slider functionality
function time_setup(max_time) {

    $("#slider").slider({ slide: function(event, ui) {
        // handle frame batches
        if (ui.value >= current_frame) { direction = 1; }
        else { direction = -1; }
        current_frame = ui.value;
        handle_batches();
        document.getElementById(
            "timestamp").innerHTML = "Time: " + frames[ui.value]["date"].substring(5, 50);
        document.getElementById(
            "summary").innerHTML = "Event " + ui.value + ": " + frames[ui.value]["summary"];

        // erase pop-up box
        document.getElementById("message_box").style.visibility = "hidden";

        // print witnesses, as hostnames
        var w = "";
        var s;
        for (s in frames[ui.value]["witnesses"]) {
            if (w !== "") {
            w += "<br/>";
            }
            w += labels[frames[ui.value]["witnesses"][s]];
        }
        document.getElementById("witnesses").innerHTML = "Witnessed event:<br/>" + w;

        // print dissenters, as hostnames
        var d = "";
        for (s in frames[ui.value]["dissenters"]) {
            if (d !== "") {
            d += "<br/>";
            }
            d += labels[frames[ui.value]["dissenters"][s]];
        }
        document.getElementById("dissenters").innerHTML = "Blind to event:<br/>" + d;

        }});
    $("#slider").slider( "option", "max", total_frame_count - 2);
}

// handle frame batches
function handle_batches() {

    // do we even have to batch?
    if (total_frame_count <= batch_size) {
    render(current_frame);
    return;
    }

    // handle case where user clicked entirely outside
    // aka load frames and then render
    if (current_frame > frame_top ||
    current_frame < frame_bottom) {
    // force some garbage collection?
    slide_batch_window();
    render(current_frame);
    }

    // handle case where use is still within frame buffer
    // but close enough to edge to reload
    else if ((frame_top - current_frame < trigger && frame_top !== total_frame_count) ||
         (current_frame - frame_bottom < trigger && frame_bottom !== 0)) {
    render(current_frame);
    // force some garbage collection?
    slide_batch_window();
    }

    // otherwise, just render
    else { render(current_frame); }
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
    document.getElementById("version").innerHTML = "Version " + admin["version"];
    return;
}

function file_names() {
    var final_string = "";
    for (var i = 0; i < admin["file_names"].length; i++) {
        final_string += admin["file_names"][i];
        final_string += "<br/>";
    }
    document.getElementById("log_files").innerHTML = final_string;
}
