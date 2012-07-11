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
    ctx.lineWidth = 3;
    //ctx.quadraticCurveTo(cx, cy, x2, y2);
    ctx.strokeStyle = "#78561c";//3B1EOB
    ctx.lineTo(x2, y2);
    ctx.stroke();


};

broken_link = function(x1, y1, x2, y2, ctx){
    ctx.beginPath();
    ctx.moveTo(x1, y1);
    ctx.lineWidth = 3;
    ctx.strokeStyle = "#E9E9E9";//3B1EOB
    //ctx.quadraticCurveTo(cx, cy, x2, y2);
    ctx.lineTo(x2, y2);
    ctx.stroke();
};
