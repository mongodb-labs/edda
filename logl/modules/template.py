#!/usr/bin/env python
"""This filter processes WHICH types of log lines."""


def criteria(msg):
    """does the given log line fit the criteria for this filter?
    return an integer code if yes, -1 if no"""
    pass


def process(msg, date):
    """if the given log line fits the critera for this filter,
    processes the line and creates a document for it."""
    pass

