#!/usr/bin/env

import sys
import string
import re
import urllib
import pymongo
import datetime
from pymongo import Connection
from noOp import storeInDB
from datetime import timedelta

#------------------------------------------------------------    

# a main function, handles basic parsing and sends 
# to trafficControl for more advanced handling
def main():

    if (len(sys.argv) < 2):
        print "Missing argument: please give me a filename"
        return

    f = open(sys.argv[1], 'r')
    counter = 0 # this is mostly for debugging
    stored = 0

    connection = Connection('localhost', 27017)
    db = connection.log

    # drop the old collection
    db.drop_collection(db.loglines)
    loglines = db.loglines

    for line in f:
#        print ''
#        print "line {0}: ".format(counter)
        counter += 1
        if (string.find(line, '*****') >= 0):
            print 'handle restart message'
        # skip blank lines, parse other lines
        elif (len(line) > 1):
            date = dateParser(line)
#            if (date != None):
            if (trafficControl(line, date)):
                storeInDB(db, line, date)
                stored += 1

    print 'Finished running, stored {0} of {1} log lines'.format(stored, counter)

#-------------------------------------------------------------    

# this function will pass each line of code through a filter
# to determine if it is interesting, and what to do with it

# for now, returns True if interesting, False if not.
def trafficControl(msg, date):

    isExitMsg = False
    isInitMsg = False
    isConnMsg = False

    # it contains an exit message:
    if (string.find(msg, 'shutdown') >= 0): 
        isExitMsg = True
    elif (string.find(msg, 'exit') >= 0): 
        isExitMsg = True
    
    # it contains an init message:
    # if it contains a "MongoDB starting" line, can capture name of server
    if (string.find(msg, '[initandlisten]') >= 0): 
        isInitMsg = True
        handleInitMsg(msg)

    # if it contains an interesting "conn#' line
    if (string.find(msg, '[conn') >= 0): 
        isConnMsg = True

    # for now, simply return True if line is interesting at all
    if isExitMsg or isInitMsg or isConnMsg: return True
    return False

#-------------------------------------------------------------    

# for lack of a better place to put this...
# beginning to parse [listenandinit] messages
def handleInitMsg(msg):

    # is it this server starting up?  If yes try to capture host information
    if (string.find(msg, 'starting') >= 0):

        # isolate port number
        start = string.find(msg, 'port=')
        port = msg[start + 5:start + 10]
        
        # isolate host IP address
        start = string.find(msg, 'host=')
        hostip = msg[start + 5:len(msg) - 1]

        print 'this host starting up on port {0}, host {1}'.format(port, hostip)
        return

    # is it an incoming connection? If yes try to capture host information
    if (string.find(msg, 'connection accepted') >= 0):
        
        # first pattern screens for all numbers, not just <= 255.        
        # pattern = re.compile("[0-9]{1,3}(\.[0-9]{1,3}){3}")
        # second pattern screens for numbers <= 299...
        # pattern = re.compile("[0-2]?[0-9]{1,2}(\.[0-2]?[0-9]{1,2}){3}")
        # third should work on only valid IPs!
        pattern = re.compile("(([0|1]?[0-9]{1,2})|(2[0-4][0-9])|(25[0-5]))(\.([0|1]?[0-9]{1,2})|(2[0-4][0-9])|(25[0-5])){3}")
        m = pattern.search(msg)
        if (m == None): 
            return
        host = m.group(0)

        # isolate port number
        port = msg[m.end(0) + 1: m.end(0) + 6]
        
        # isolate connection number
        place = string.find(msg, '#')
        conn_number = msg[place + 1: len(msg) - 1] 

        print 'found beginning of connection #{0} with host at address {1}, port {2}'.format(conn_number, host, port)
        return

    return

#-------------------------------------------------------------    

# for lack of a better place to put this...
def handleConnMsg(msg):
    # is the connection # one that we already have information about?  If not, add new information
    # is this an end connection message?  If yes, capture host information and act accordingly
    return

#-------------------------------------------------------------    

# for lack of a better place to put this...
def handleExitMsg(msg):
    return

#-------------------------------------------------------------    

def dateParser(message):
    words = message.split(" ")
    dated = False
    dayFlag = False
    month = 0
    for thing in words:
        if dayFlag:
            dayFlag = False
            day = int(thing)
        if len(thing) == 3 and month == 0:
            month = parseMonth(thing)
            month = int(month)
            if month != 0:
                dayFlag = True
            
        if (dated == False):
            pattern = "(..):(..):(..)"
            compiled = re.compile(pattern)
            if compiled.search(thing):
                dated = True
                parts = thing.split(":")
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = int(parts[2])
#                print 'hours: {0} minutes: {1} seconds: {2}'.format(hours, minutes, seconds)
#    print 'MONTH: {0}'.format(month)           
    
    # need a way to catch malformed lines with no/incomplete date information
    if (dayFlag == False) or (month == 0) or (dated == False): 
        return None 
    
    date = datetime.datetime(2012, month, day, hours, minutes, seconds)
    return date

#------------------------------------------------------------

# tries to match the string to a month code, and returns 
# that month's integer equivalent
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

#-------------------------------------------------------------    

# tries to match the string to a day code, and returns that day's 
# integer equivalent
# ?? Is this a necessary thing to do?
def parseDay(day):
    return{
        'Mon':1,
        'Tue':2,
        'Wed':3,
        'Thu':4,
        'Fri':5,
        'Sat':6,
        'Sun':7,
        }.get(day, 0)

#-------------------------------------------------------------    

if __name__ == "__main__":
    main()
