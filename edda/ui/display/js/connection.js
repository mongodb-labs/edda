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

// without the async messing things up?
function connect() {

    // get first batch and first buffer
    get_batch(0, batch_size);
    frame_bottom = 0;
    frame_top = batch_size;
    if (frame_top > total_frame_count) { frame_top = total_frame_count; }

    // poll for additional setup data
    url_string = document.URL + "data.admin";
    //console.log(document.URL );
    $.ajax({
        async: false,
        url: url_string,
        dataType: "json",
        success: function(data) {
        admin = data;
        total_frame_count = data["total_frame_count"];
        }
    });

    // poll for the server names
    url_string = document.URL + "data.servers";
    $.ajax({
        async: false,
        url: url_string,
        dataType: "json",
        success: function(data) {
        server_names = data;
        }
    });

}

// this function is not finished
function get_batch(a, b) {
    // poll for a batch of frames
    var s = document.URL + a + "-" + b + ".batch";
    $.ajax({
        async: false,
        url: s,
        dataType: "json",
        success: function(data) {
        frames = data;
        }
    });
}
