Edda, a log visualizer for MongoDB
==================================

Edda © 2014 MongoDB, Inc.

Authors: Samantha Ritter, Kaushal Parikh

INSTALL
-------

You must have the following installed as prerequisites for running Edda.

+ Pip:

  http://www.pip-installer.org/en/latest/installing.html#

+ MongoDB

  see http://www.mongodb.org/downloads

+ Install Edda:

  $ pip install edda

RUN
---

In order to run edda you must first have a mongod running:

    $ mongod

Give the log files from your servers as command-line
arguments to edda.  Please provide only log files from the same server cluster!

	$ python edda/run_edda.py --options filename1 filename2 ...
	(see python run_edda.py --help for options)

After each run, edda generates a '.json' file that contains all of the information required to recreate the current run. Run the '.json' file just as you would a '.log'. 
If you've run edda before, you can pass in a .json file to skip the processing step and go straight to visualization:

    $ python edda/run_edda.py previous_edda_data.json

There are some sample log files in edda/sample_logs you can run
if you don't have any log files of your own yet.

ADDITIONAL
----------

If you'd like to report a bug or request a new feature,
please file an issue on our github repository:
https://github.com/10gen-labs/edda/issues/new
