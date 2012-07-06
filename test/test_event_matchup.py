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

# testing file for logl/post/event_matchup.py


def test_event_matchup_empty():
    """Test event_matchup on an empty database"""
    pass


# -----------------------------
# test the next_event() method
# -----------------------------

def test_next_event_one_server():
    """Test next_event() on lists from just one server"""
    pass


def test_next_event_all_empty():
    """Test next_event() on all empty lists, but with
    server names present (i.e. we ran out of entries)"""
    pass


def test_next_event_all_empty_but_one():
    """Test next_event() on input on many servers, but with
    all servers' lists empty save one (i.e. we went through
    the other servers' entries already)"""
    pass


def test_next_event_one():
    """Test next_event() on lists from two servers
    with one matching entry in each server's list"""
    pass


def test_next_event_two():
    """Test next_event() on lists from two servers
    with entries that do not match"""
    pass


# -------------------------------------
# test the target_server_match() method
# -------------------------------------


def test_target_server_match_both_self():
    """Test method on two entries whose info.server
    field is 'self'"""
    pass


def test_target_server_match_both_same():
    """Test method on two entries with corresponding
    info.server fields"""
    pass


def test_target_server_match_both_different():
    """Test method on two entries with different
    info.server fields"""
    pass


def test_target_server_match_IP():
    """Test method on entries where one cites 'self',
    other cites IP address"""
    pass


def test_target_server_match_hostname():
    """Test method on entries where one cites 'self',
    other cites hostname"""
    pass


def test_target_server_match_unknown_IP():
    """Test method on entries where one cites 'self',
    other cites first server's true IP, but IP is not yet
    recorded in the .servers collection"""
    pass


def test_target_server_match_unknown_hostname():
    """Test method on entries where one cites 'self',
    other cites first server's true hostname, but
    hostname is not yet recorded in the .servers collection"""
    pass


# -------------------------------------
# test the resolve_dissenters() method
# -------------------------------------


