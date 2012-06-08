#!/usr/bin/env

from pymongo import Connection
import datetime

# SETUP
# ================================================
# connect to a database B

def main():

    # (thank you http://pastebin.com/RbDqGDuV)
    c = Connection("localhost:27017", slave_okay=True)

    config = {
        '_id': 'foo',
        'members': [
            { '_id':0, 'host': 'localhost:27017'},
            { '_id':1, 'host': 'localhost:27018'},
            { '_id':2, 'host': 'localhost:27019', 'arbiterOnly':'true'}
            ]
        }

    c.admin.command("replSetInitiate", config)
    db = c.rollback

    # connect to db B                                                                    
    # do some inserts                                                                   
    writes(db, 10)

    # kill C
    raw_input("Please kill primary server C and press Enter to continue...")

    # more inserts to db B
    writes(db, 10)

    # kill B
    raw_input("Please kill primary server B and press Enter to continue...")

    # bring C back up
    raw_input ("Please bring server C back up and press Enter to continue...")

    # arbiter elects C as new master
    # so some inserts on C
    writes(db, 10)

    # bring B back up
    raw_input ("Please bring server B back up and press Enter to continue...")

    return

# ================================================

def writes(db, reps):
    x = 0
    while x < reps:
        doc = {}
        doc["value"] = x
        doc["date"] = datetime.datetime.now()
        db.rolldata.insert(doc)
        print 'inserted record {0}'.format(x)
        x += 1

# ================================================

if __name__ == "__main__":
    main()
