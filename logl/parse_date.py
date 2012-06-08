#!/usr/bin/env

from datetime import datetime
#from datetime import timedelta
import string

#--------------------------------------------------------

# extracts the date information from the given line.  If
# line contains incomplete or no date information, skip 
# and return None.
def efficientDateParser(message):
    newMessage  = str(parseMonth(message[4:7])) + message[7:19]
   # print 'current string: {0}'.format(newMessage)                                        
    time = datetime.strptime(newMessage, "%m %d %H:%M:%S")
    print 'date: {0}'.format(time)
    return time

#-------------------------------------------------------------                             

# tries to match the string to a month code, and returns                                   
# that month's integer equivalent.  If no month is found,
# return 0.                                                          
def parseMonth(month):
    return{
        'Jan':1,
        'Feb':2,
        'Mar':3,
        'Apr':4,
        'May':5,
        'Jun':6,
        'Jul':7,
        'Aug':8,
        'Sep':9,
        'Oct':10,
        'Nov':11,
        'Dec':12,
        }.get(month, 0)

