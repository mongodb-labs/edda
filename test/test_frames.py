# Copyright 2012 10gen, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from logl.post.frames import *
from datetime import datetime
from nose.plugins.skip import Skip, SkipTest
from logl.post.event_matchup import generate_summary
import string

#-------------------------
# helper methods for tests
#-------------------------


def generate_event(target, type, more, w, d):
    """Generate an event of the specified type.
    More will be None unless the type specified requires
    additional fields. w and d may be none."""
    e = {}
    e["type"] = type
    # set type-specific fields
    if type == "status":
        e["state"] = more["state"]
    elif type == "sync":
        e["sync_to"] = more["sync_to"]
    elif (string.find(type, "conn") >= 0):
        e["conn_IP"] = more["conn_IP"]
        e["conn_number"] = more["conn_number"]
    e["target"] = target
    if not w:
        e["witnesses"] = target
    else:
        e["witnesses"] = w
    e["dissenters"] = d
    return e


def new_frame(servers):
    """Generate a new frame, with no links, broken_links,
    syncs, or users, and all servers set to UNDISCOVERED
    does not set the 'summary' field"""
    f = {}
    f["date"] = datetime.now()
    f["server_count"] = len(servers)
    f["witnesses"] = []
    f["dissenters"] = []
    f["flag"] = False
    f["links"] = {}
    f["broken_links"] = {}
    f["syncs"] = {}
    f["users"] = {}
    f["servers"] = {}
    for s in servers:
        f["servers"][s] = "UNDISCOVERED"
        f["links"][s] = []
        f["broken_links"][s] = []
        f["users"][s] = []
        f["syncs"][s] = []
    return f


#---------------------
# test info_by_type()
#---------------------


def test_info_by_type_status():
    """Test method on status type event"""
    e = generate_event("3", "status", {"state": "PRIMARY"}, "3", None)
    f = info_by_type(new_frame(["3"]), e)
    assert f
    assert f["servers"]["3"] == "PRIMARY"


def test_info_by_type_reconfig():
    """Test method on reconfig type event"""
    e = generate_event("1", "reconfig", None, "1", None)
    f = info_by_type(new_frame(["1"]), e)
    assert f


def test_info_by_type_new_conn():
    """Test method on new_conn type event"""
    e = generate_event("1", "new_conn",
                       {"conn_IP": "1.2.3.4",
                        "conn_number": 14}, "1", None)
    f = info_by_type(new_frame(["1"]), e)
    assert f
    assert f["users"]["1"]
    assert len(f["users"]["1"]) == 1
    assert "1.2.3.4" in f["users"]["1"]


def test_info_by_type_end_conn():
    """Test method on end_conn type event"""
    # first, when there was no user stored
    e = generate_event("1", "end_conn",
                       {"conn_IP": "1.2.3.4",
                        "conn_number": 14}, "1", None)
    f = info_by_type(new_frame(["1"]), e)
    assert f
    assert not f["users"]["1"]
    # next, when there was a user stored
    f = new_frame(["1"])
    f["users"]["1"].append("1.2.3.4")
    f = info_by_type(f, e)
    assert f
    assert not f["users"]["1"]


def test_info_by_type_sync():
    """Test method on sync type event"""
    pass


def test_info_by_type_exit():
    """Test method on exit type event"""
    pass


def test_info_by_type_lock():
    """Test method on lock type event"""
    pass


def test_info_by_type_unlock():
    """Test method on unlock type event"""
    pass


def test_info_by_type_new():
    """Test method on a new type of event"""
    pass


def test_info_by_type_down_server():
    """Test that this method properly handles
    servers going down (removes any syncs or links)"""
    pass


#----------------------------
# test witnesses_dissenters()
#----------------------------


def test_w_d_no_dissenters():
    """Test method on an entry with no dissenters"""
    pass


def test_w_d_equal_w_d():
    """Test method an an entry with an
    equal number of witnesses and dissenters"""
    pass


def test_w_d_more_witnesses():
    """Test method on an entry with more
    witnesses than dissenters"""
    pass


def test_w_d_more_dissenters():
    """Test method on an entry with more
    dissenters than witnesses"""
    pass


def test_w_d_link_goes_down():
    """Test a case where a link was lost
    (ie a server was a dissenter in an event
    about a server it was formerly linked to)"""
    pass


def test_w_d_new_link():
    """Test a case where a link was created
    between two servers (a server was a witness to
    and event involving a server it hadn't previously
    been linked to"""
    pass


def test_w_d_same_link():
    """Test a case where an existing link
    is reinforced by the event's witnesses"""
    pass


#-----------------------
# test generate_frames()
#-----------------------


def test_generate_frames_empty():
    """Test generate_frames() on an empty list
    of events"""
    pass


def test_generate_frames_one():
    """Test generate_frames() on a list with
    one event"""
    pass


def test_generate_frames_all_servers_discovered():
    """Test generate_frames() on a list of events
    that defines each server with a status by the end
    (so when the final frame is generated, no servers
    should be UNDISCOVERED)"""
    pass


def test_generate_frames_all_linked():
    """Test generate_frames() on a list of events
    that defines links between all servers, by the
    final frame"""
    pass


def test_generate_frames_users():
    """Test generate_frames() on a list of events
    that involves a user connection"""
    pass


def test_generate_frames_syncs():
    """Test generate_frames() on a list of events
    that creates a chain of syncing by the last frame"""
    pass

