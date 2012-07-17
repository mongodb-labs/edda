Logl, a log visualizer for MongoDB
==================================

Logl c 2012 10gen, the MongoDB Company

Authors: Samantha Ritter, Kaushal Parikh

INSTALL
-------

You must have the following installed as prerequisites for running Logl.

+ Pip:

  http://www.pip-installer.org/en/latest/installing.html#

+ MongoDB (which you should do anyway because it is awesome)

  see http://www.mongodb.org/downloads

+ PyMongo, MongoDB's language driver for Python:

  $ pip install pymongo

+ argparse:

  $ pip install argparse

+ Install a non-text-based browser

  We recommend Google Chrome or Firefox.

+ Install Logl:

  $ pip install logl

RUN
---

Give the log files from your servers as command-line
arguments to the visualizer:

	  python logl.py --options filename1 filename2 ...
(see python logl.py --help for options)

Logl can read in multiple log files at once.

NOTE: please only give logl files from the same server cluster!


There are some sample log files in logl/test you can run
if you don't have any log files of your own yet.

ADDITIONAL
----------

If you'd like to report a bug or request a new feature,
please file an issue on our github repository:

https://github.com/kchodorow/logl/issues/new
