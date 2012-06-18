from logl.post import *
import pymongo
from datetime import timedelta

def test_server_clock_skew():
    pass


def test_detect():
    pass


def test_clock_skew_doc():
    """Simple tests of the clock_skew_doc() method
    in post.py"""
    doc = clock_skew_def("Samantha")
    assert doc
    assert doc["server_name"] == "Samantha"
    assert doc["type"] == "clock_skew"
    assert doc["partners"]
    pass


def test_server_matchup():
    pass
