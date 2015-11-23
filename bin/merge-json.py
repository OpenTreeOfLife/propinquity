#!/usr/bin/env python
from collections import Mapping
import json
import sys

filename1 = sys.argv[1]
filename2 = sys.argv[2]

json_data1=open(filename1).read()
dictA = json.loads(json_data1)
json_data2=open(filename2).read()
dictB = json.loads(json_data2)

merged_dict = {key: value for (key, value) in (dictA.items() + dictB.items())}

# string dump of the merged dict
print json.dumps(merged_dict)
