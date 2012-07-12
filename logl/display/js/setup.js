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
var layers = new Array("background", "shadow", "link", "arrow", "server", "text", "message");
var canvases = {};
var contexts = {};
var servers = {};
var server_names;
var frames;
var slider = {};


// call various setup functions
function logl_setup() {
    canvases_and_contexts();
    mouse_over_setup();
    connect();  // see connection.js
    time_setup(frames.size);
    visual_setup();
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
    canvases["message"].addEventListener("mousemove", on_canvas_mouseover, false);
    canvases["message"].addEventListener("click", on_canvas_click, false);
}


// set up display-related things from frames
// generate coordinates
// set background to brown
function visual_setup() {
    var names = new Array();
    if (frames) {
        if (frames["0"]) {
            for (var name in frames["0"]["servers"]) {
                names.push(name);
            }
            generate_coords(names.length, names);
        }
    }

    // clear all layers
    for (var name in layers) {
    canvases[layers[name]].width = canvases[layers[name]].width;
    }

    // color background
    var b_cvs = canvases["background"];
    var b_ctx = contexts["background"];
    b_ctx.beginPath();
    b_ctx.rect(0, 0, b_cvs.width, b_cvs.height);
    b_ctx.fillStyle = "#4E3629";
    b_ctx.fill();

    // render first frame
    render("0");

}


// set up slider functionality
function time_setup(max_time) {

    $("#slider").slider({ slide: function(event, ui) {
		render(ui.value);
        console.log(ui.value);
        document.getElementById("timestamp").innerHTML = frames[ui.value]["date"];
        document.getElementById("summary").innerHTML = ui.value + ": " + frames[ui.value]["summary"];
        }});
    //$("#slider").slider( "option", "min", 0 );
    //$("#slider").slider( "option", "max", max_time );
    $("#slider").slider( "option", "step", 1 );
}


// define .size function for object
// thanks http://stackoverflow.com/questions/5223/length-of-javascript-object-ie-associative-array
Object.size = function(obj) {
    var size = 0, key;
    for (key in obj) {
    if (obj.hasOwnProperty(key)) size++;
    }
    return size;
};





