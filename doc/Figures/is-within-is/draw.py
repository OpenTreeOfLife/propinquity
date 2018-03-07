#!/usr/bin/python

import sys
from subprocess import call

filename = sys.argv[1]

call(["../../strip_ott_labels.py"], stdin=open(filename), stdout=open("temp","w"))
call(["../../drawtree","--input=temp","--output={}.svg".format(filename),"--format=svg"])
