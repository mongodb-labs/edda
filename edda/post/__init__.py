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

import os
import re

__all__ = []
dirList = os.listdir(os.path.dirname(os.path.abspath(__file__)))
pattern = re.compile(".py$")

for d in dirList:
    # ignore anything that isn't strictly .py
    m = pattern.search(d)
    if (m != None):
        d = d[0:len(d) - 3]
        __all__.append(d)
