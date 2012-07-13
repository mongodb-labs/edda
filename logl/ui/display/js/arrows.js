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


one_arrow = function(x1, y1, x2, y2, ctx) {

    ctx.beginPath();
    dx = Math.abs(x2 - x1);
    dy = Math.abs(y2 - y1);

    cx = x1 + dx/2 - dy/4;
    cy = y1 + dy/2 + dx/4;

    var h = Math.sqrt(Math.pow(dx, 2) + Math.pow(dy, 2));
    var h_prime = 75.0000;
    var ratio = h_prime / h;
    var x_difference, y_difference;

    x_difference = dx * ratio;
    y_difference = dy * ratio;


    //There are 4 cases for the adjustments that need to be made. Arrows going in each diagonal dirrection.
    if (x2 > x1) {
        if (y2 > y1) { //Case where arrow originates on the bottom left and goes toward the bottom right.
            x1 += x_difference;
            y1 += y_difference;

            x2 -= x_difference;
            y2 -= y_difference;
        }
        else { //Case where arrow originates on the top left and goes toward the bottom right.
            x1 += x_difference;
            y1 -= y_difference;

            x2 -= x_difference;
            y2 += y_difference;
        }
    }
    else {
        if (y2 > y1) { //Case where arrow originates on the bottom right and goes towards the top left
            x1 -= x_difference;
            y1 += y_difference;

            x2 += x_difference;
            y2 -= y_difference;
        }
        else {
            x1 -= x_difference;
            y1 -= y_difference;

            x2 += x_difference;
            y2 += y_difference;
        }
    }

    ctx.moveTo(x1, y1);
    ctx.strokeStyle = "#F0E92F";//3B1EOB
    ctx.lineWidth = 6;
    ctx.lineTo(x2, y2);
    ctx.lineCap = "butt";
    ctx.stroke();
    draw_arrow_head(x1, x2, y1, y2, ctx);
};

draw_arrow_head = function (fromx, tox, fromy, toy, ctx) {
     // adapted from http://stackoverflow.com/questions/808826/draw-arrow-on-canvas-tag
    ctx.beginPath();

    var headlen = 20;   // length of head in pixels
    var angle = Math.atan2(toy - fromy, tox - fromx);

    ctx.strokeStyle = "#F0E92F";
    ctx.fillStyle = "#F0E92F";
    ctx.lineWidth = 6;

    ctx.moveTo(tox, toy);
    ctx.lineTo(tox-headlen*Math.cos(angle-Math.PI/8),toy-headlen*Math.sin(angle-Math.PI/8));
    ctx.lineTo(tox-headlen*Math.cos(angle+Math.PI/8),toy-headlen*Math.sin(angle+Math.PI/8));
    ctx.lineTo(tox, toy);
    ctx.stroke();
    ctx.fill();
};
