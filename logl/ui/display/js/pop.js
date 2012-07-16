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

// opens a popup div
function popUp(name) {
    document.getElementById("mask").style.visibility='visible';
    document.getElementById(name).style.visibility='visible';
}

// close the popup div
function popDown(name) {
    document.getElementById(name).style.visibility='hidden';
    document.getElementById("mask").style.visibility='hidden';
}