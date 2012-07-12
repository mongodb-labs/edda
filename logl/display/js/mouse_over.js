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

        // text box over
        /*var message = contexts["message"];
        message.fillStyle = "black";
        message.rect(x, y, 120, 200);
        message.fill();*/
        }
    }

    // if not in radius:
    else if (servers[server]["on"] === true){
        servers[server]["on"] = false;
        canvases["shadow"].width = canvases["shadow"].width;
        canvases["message"].width = canvases["message"].width;
        canvases["text"].width = canvases["text"].width;
    }
    }
};

on_canvas_click = function(e) {
    var offset = $("#shadow_layer").offset();
    var x = e.clientX - offset.left;
    var y = e.clientY - offset.top;

    console.log("I am in the clicking method.");
    console.log(x);
    console.log(y);
    // check if mouse was over server
    for (server in servers) {

    // calculate distance from click
    diffX = x - servers[server]["x"];
    diffY = y - servers[server]["y"];
    distance = Math.sqrt(Math.pow(diffX,2) + Math.pow(diffY,2));
    // is it within radius?
    if (distance <= servers[server]["r"]) {
        console.log("I am in the clicking method.");
        // check if that server is set to "true" for mouseover
        // make a shadow under server, and a sound
        servers[server]["on"] = true;
        var shadow = contexts["shadow"];

        // draw the drop shadow


        // text box over
        var message = contexts["text"];
        message.fillStyle = "#1C0E0B";
        message.rect(x, y, 120, 200);
        message.fill();
        console.log("I am in the clicking method.");
        }
    }

    // if not in radius:
    //else if (servers[server]["on"] === true){
        //servers[server]["on"] = false;
        //canvases["shadow"].width = canvases["shadow"].width;
        //canvases["message"].width = canvases["message"].width;
    //}

};
on_canvas_clicks = function(e) {
    var offset = $("#shadow_layer").offset();
    var x = e.clientX - offset.left;
    var y = e.clientY - offset.top;
    // check if mouse was over server
    console.log("I am in the clicking method.");
    console.log(x);
    console.log(y);
    for (server in servers) {

    // calculate distance from click
    diffX = x - servers[server]["x"];
    diffY = y - servers[server]["y"];
    distance = Math.sqrt(Math.pow(diffX,2) + Math.pow(diffY,2));
    // is it within radius?
    if (distance <= servers[server]["r"]) {
        // check if that server is set to "true" for mouseover
        console.log("I am in this loop.");
        if (!servers[server]["on"]) {
            servers[server]["on"] = true;
        // make a shadow under server, and a sound
        console.log("I am within the radius of a circle. ");
        var message = contexts["message"];
        message.fillStyle = "black";
        message.rect(x, y, 120, 200);
        message.fillStyle = "rgba(0, 0, 200, 0.75)";
        //setOpacity (message, .5);
        message.fill();
        }
    }

    // if not in radius:
    else if (servers[server]["on"] === true){
        servers[server]["on"] = false;
        canvases["shadow"].width = canvases["shadow"].width;
        canvases["message"].width = canvases["message"].width;
    }
    }

};

function setOpacity (myElement, opacityValue) {
    if (window.ActiveXObject) {
        myElement.style.filter = "alpha(opacity=" + opacityValue*100 + ")"; // IE
    } else {
        myElement.style.opacity = opacityValue; // Gecko/Opera
    }
}
