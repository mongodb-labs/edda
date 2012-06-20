log-visualizer
==============

logl
c 2012 10gen, the MongoDB Company
info@10gen.com

All of this product's content was created by 10gen

==============
INSTALL

nothing to install!

==============
RUN

Give the log files from your servers as command-line
arguments to the visualizer:

python logl.py --options filename1 filename2 ...
(see python logl.py --help for options)

logl can read in multiple log files at once.
NOTE: please only give logl files from the same server cluster!
