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

