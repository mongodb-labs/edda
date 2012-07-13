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


one_line = function(x1, y1, x2, y2, ctx) {
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineWidth = 1;
    ctx.strokeStyle = "#1C0E0B";//3B1EOB
    ctx.lineTo(x2, y2);
    ctx.stroke();
};

broken_link = function(x1, y1, x2, y2, ctx) {
    // draw a dotted line from x1,y1 to x2,y2
    var dy = y2 - y1;
    var dx = x2 - x1;
    var slope = dy/dx;
    var l = 10;
    var x = x1;
    var y = y1;
    var distRemaining = Math.sqrt(dx*dx + dy*dy);
    var xStep = Math.sqrt(l*l / (1 + slope*slope));

    // set the sign of xStep:
    if (x1 > x2) { xStep = -xStep; }
    var yStep = slope * xStep;

    ctx.lineWidth = 1;
    ctx.strokeStyle = "#9D7E51";//3B1EOB
    ctx.beginPath();
    // adapted from http://stackoverflow.com/questions/4576724/dotted-stroke-in-canvas
    while (distRemaining >= 0.1) {
	ctx.moveTo(x, y);
	x += xStep;
	y += yStep;
	ctx.lineTo(x, y);
	x += xStep;
	y += yStep;
	distRemaining -= (2 * l);
    }
    ctx.stroke();
};