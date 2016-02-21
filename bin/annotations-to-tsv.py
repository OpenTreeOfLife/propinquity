#!/usr/bin/env python
import json
import sys
headers = ['id', 'supported by', 'compatible with', 'conflicts with', 'is trivial in']
int_keys = [u'supported_by', u'partial_path_of', u'conflicts_with', u'terminal']
internal_rows = []
terminal_rows = []
def url_for(study, tree, node):
    fmt = 'node {n} for https://tree.opentreeoflife.org/curator/study/view/{s}/?tab=trees&tree={t}'
    return fmt.format(s=study, t=tree, n=node)
try:
    annotations_fn = sys.argv[1]
except:
    sys.exit('''Pass in the annotated_supertree/annotations.json file from the propinquity-based synthesis.
This script will create a tab separated view of the annotations file.
''')

with open(annotations_fn, 'rU') as inp:
    d = json.load(inp)
    source_id_map = d['source_id_map']
    #print source_id_map
    n = d['nodes']
    vs = set()
    for node_id, supp_conf in n.items():
        if ('terminal' not in supp_conf) or (len(supp_conf) > 1):
            for n, ik in enumerate(int_keys):
                for v in supp_conf.get(ik, []):
                    nr = [node_id, '', '', '', '']
                    study_tree_key = v[0]
                    blob = source_id_map[study_tree_key]
                    study_id, tree_id = blob['study_id'], blob['tree_id']
                    nr[1 + n] = url_for(study_id, tree_id, v[1])
                    internal_rows.append(nr)
        else:
            for v in supp_conf['terminal']:
                nr = [node_id, '']
                study_tree_key = v[0]
                blob = source_id_map[study_tree_key]
                study_id, tree_id = blob['study_id'], blob['tree_id']
                nr[1] = url_for(study_id, tree_id, v[1])
                terminal_rows.append(nr)

internal_rows.sort()
out = sys.stdout

out.write('{}\n'.format('\t'.join(headers)))
for row in internal_rows:
    out.write('{}\n'.format('\t'.join(row)))
out.write('{}\n'.format('\t'.join(['Terminal node id', 'included in'])))
for row in terminal_rows:
    out.write('{}\n'.format('\t'.join(row)))