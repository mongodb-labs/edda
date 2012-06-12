import os
import re
import string

__all__ = []
dirList = os.listdir(os.path.dirname(os.path.abspath(__file__)))
pattern = re.compile(".py$")
pattern2 = re.compile("#")
pattern3 = re.compile(".+\s+.+")
for d in dirList:
    # ignore anything that isn't strictly .py
    m = pattern.search(d)
    if (m != None):
        # ignore anything with # in its name
#        m = pattern2.search(d)
 #       if (m != None):
            # ignore anything with whitespace in its name
            #m = pattern3.search(d)
            #if (m != None):
        d = d[0:len(d) - 3]
        __all__.append(d)
        print d
