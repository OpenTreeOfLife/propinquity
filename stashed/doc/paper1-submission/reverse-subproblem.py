#!/usr/bin/python
import sys

lines = open(sys.argv[1]).readlines()
lastline = lines[-1];
del lines[-1];
for line in reversed(lines):
    print(line.rstrip())
print(lastline.rstrip())
