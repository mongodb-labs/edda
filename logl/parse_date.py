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

#!/usr/bin/env python

from datetime import datetime


def date_parser(message):
    """extracts the date information from the given line.  If
line contains incomplete or no date information, skip
and return None."""
    try:
        newMessage = str(parse_month(message[4:7])) + message[7:19]
        time = datetime.strptime(newMessage, "%m %d %H:%M:%S")
        return time
    except ValueError:
        return None


def parse_month(month):
    """tries to match the string to a month code, and returns
that month's integer equivalent.  If no month is found,
return 0."""
    return{
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12,
        }.get(month, 0)
