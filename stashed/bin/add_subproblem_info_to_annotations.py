#!/usr/bin/env python
from peyotl import read_as_json
import codecs
import json
import sys
try:
    subproblem_ids_file, in_annotations_file, out_annotations_file = sys.argv[1:]
except:
    sys.exit('Expecting 3 arguments:\n   subproblem_ids_file, in_annotations_file, out_annotations_file')
import os
bin_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
sys.path.append(os.path.join(bin_dir))
from document_outputs import stripped_nonempty_lines
subproblems = []
for s in stripped_nonempty_lines(subproblem_ids_file):
    assert s.endswith('.tre')
    subproblems.append(s[:-4])
jsonblob = read_as_json(in_annotations_file)
nodes_dict = jsonblob['nodes']
for ott_id in subproblems:
    d = nodes_dict.setdefault(ott_id, {})
    d['was_constrained'] = True
    d['was_uncontested'] = True
with codecs.open(out_annotations_file, 'w', encoding='utf-8') as out_stream:
    json.dump(jsonblob, out_stream, indent=2, sort_keys=True, separators=(',', ': '))
