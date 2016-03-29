#!/usr/bin/env python
'''Merges 2 JSON objects into a single object that is written
to standard output.


There are two invocations supported a 2 argument form:

   merge-json.py first.json second.json

which merges all of the properties of the files.

And a four argument form

   merge-json.py first.json x/y/z second.json w

which only copies object valued first['x']['y']['z'] into
the body of object second['w']. This is a partial merge from
source to destination. The resulting object is still written
to standard output. Note that / is used a field separator here,
so this method will not work if one of the property names includes
a / anywhere.

'''
import codecs
import json
import sys
import re

if len(sys.argv) == 3:
    filename1, filename2 = sys.argv[1:]
    src_prop, dest_prop = None, None
else:
    if len(sys.argv) != 5:
        sys.exit('ERROR: Wrong number of arguments provided\n' + __doc__)
    filename1, src_prop, filename2, dest_prop = sys.argv[1:]
out = codecs.getwriter('utf-8')(sys.stdout)


dict1 = json.load(codecs.open(filename1, 'rU', encoding='utf-8'))
merged_dict = json.load(codecs.open(filename2, 'rU', encoding='utf-8'))
if src_prop is None:
    merged_dict.update(dict1)
else:
    src_address = src_prop.split('/')
    src_obj = dict1
    prev_address = []
    while src_address:
        next_key = src_address.pop(0)
        if next_key not in src_obj:
            f = 'Did not find requested key "{}" in {} object from {}'
            msg = f.format(next_key, '/'.join(prev_address), filename1)
            raise RuntimeError(msg)
        src_obj = src_obj[next_key]
        prev_address.append(next_key)
    prev_address = []
    dest_address = dest_prop.split('/')
    dest_obj = merged_dict
    if not isinstance(dest_obj, dict):
        raise RuntimeError('Expecting object read from {} to be a dict'.format(filename2))
    while len(dest_address) > 1:
        next_key = dest_address.pop(0)
        if next_key not in dest_obj:
            dest_obj[next_key] = {}
        dest_obj = dest_obj[next_key]
        if not isinstance(dest_obj, dict):
            f = 'Expecting {} from {} to be a dict.'
            raise RuntimeError(f.format('/'.join(prev_address), filename2))
        prev_address.append(next_key)
    assert isinstance(dest_obj, dict)
    next_key = dest_address.pop()
    dest_obj[next_key] = src_obj

# string dump of the merged dict
json.dump(merged_dict,
          out,
          indent=1,
          sort_keys=True,
          separators=(',', ': '))
out.write('\n')