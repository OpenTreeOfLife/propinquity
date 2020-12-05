#!/usr/bin/python

import sys
import re

for line in sys.stdin:
    line = re.sub(r'_ott\d+','',line)
    print(line)
    
