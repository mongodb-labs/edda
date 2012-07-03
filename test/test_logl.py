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


from logl.logl import assign_address
import pymongo
from pymongo import Connection

def db_setup():
    """Set up a database for use by tests"""
    c = Connection()
    db = c["test"]
    servers = db["zoo.servers"]
    db.drop_collection(servers)
    return servers


def assert_doc_specs(doc, num, name, IP):
    """Assert various things about a .server doc"""
    assert doc
    assert doc["server_num"] == num
    assert doc["server_name"] == name
    assert doc["server_IP"] == IP


def test_assign_address_new_server_unknown():
    """Test assign_address() on a new server
    with unknown hostname/IP"""
    servers = db_setup()
    assign_address(1, "1", servers)
    assert_doc_specs(servers.find_one(), "1", "unknown", "unknown")


def test_assign_address_new_server_known_IP():
    """Test assign_address() on a new server
    with a known IP address"""
    servers = db_setup()
    assign_address(1, "1.2.3.4", servers)
    assert_doc_specs(servers.find_one(), "1", "unknown", "1.2.3.4")


def test_assign_address_new_server_known_hostname():
    """Test assign_address() on a new server with
    a known IP address"""
    servers = db_setup()
    assign_address(1, "zebra@the.zoo", servers)
    assert_doc_specs(servers.find_one(), "1", "zebra@the.zoo", "unknown")


def test_assign_address_new_hostname():
    """Test assign_address() on a known server with
    a new hostname and previously known IP"""
    servers = db_setup()
    assign_address(56, "5.6.7.8", servers)
    assert_doc_specs(servers.find_one(), "56", "unknown", "5.6.7.8")
    assign_address(56, "monkey@the.zoo", servers)
    assert servers.find().count() == 1
    assert_doc_specs(servers.find_one(), "56", "monkey@the.zoo", "5.6.7.8")


def test_assign_address_new_IP():
    """Test assign_address() on a known server with
    a new IP and previously known hostname"""
    servers = db_setup()
    assign_address(4, "lion@the.zoo", servers)
    assert_doc_specs(servers.find_one(), "4", "lion@the.zoo", "unknown")
    assign_address(4, "4.4.4.4", servers)
    assert servers.find().count() == 1
    assert_doc_specs(servers.find_one(), "4", "lion@the.zoo", "4.4.4.4")


def test_assign_address_duplicate_IP():
    """Test assign_address() on a known server with
    a duplicate IP and unknown hostname"""
    servers = db_setup()
    assign_address(1, "1.2.3.4", servers)
    assign_address(1, "1.2.3.4", servers)
    assert servers.find().count() == 1
    assert_doc_specs(servers.find_one(), "1", "unknown", "1.2.3.4")


def test_assign_address_duplicate_IP_known_hostname():
    """Test assign_address() on a known server with
    duplicate IP and known hostname"""
    servers = db_setup()
    assign_address(3, "1.3.9.27", servers)
    assign_address(3, "serpent@the.zoo", servers)
    assign_address(3, "1.3.9.27", servers)
    assert servers.find().count() == 1
    assert_doc_specs(servers.find_one(), "3", "serpent@the.zoo", "1.3.9.27")


def test_assign_address_duplicate_hostname():
    """Test assign_address() on a known server with
    a duplicate hostname"""
    servers = db_setup()
    assign_address(3, "1.3.9.27", servers)
    assign_address(3, "serpent@the.zoo", servers)
    assign_address(3, "serpent@the.zoo", servers)
    assert servers.find().count() == 1
    assert_doc_specs(servers.find_one(), "3", "serpent@the.zoo", "1.3.9.27")


def test_assign_address_conflicting_IP():
    """Test assign_address() on a known server with
    a conflicting new IP"""
    servers = db_setup()
    assign_address(6, "1.3.9.27", servers)
    assign_address(6, "elephant@the.zoo", servers)
    assign_address(6, "2.4.6.8", servers)
    assert servers.find().count() == 1
    assert_doc_specs(servers.find_one(), "6", "elephant@the.zoo", "1.3.9.27")


def test_assign_address_conflicting_hostname():
    """Test assign_address() on a known server with
    a conflicting new hostname"""
    servers = db_setup()
    assign_address(10, "0.0.0.0", servers)
    assign_address(10, "fish@the.zoo", servers)
    assign_address(10, "dolphin@the.zoo", servers)
    assert servers.find().count() == 1
    assert_doc_specs(servers.find_one(), "10", "fish@the.zoo", "0.0.0.0")
