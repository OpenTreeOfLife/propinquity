#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
    

def main(nexson_fp, conflict_call_fp, tree_id, root_at_id=None):
    with open(conflict_call_fp, "r") as inp:
        conflict = json.load(inp)
    with open(nexson_fp, "r") as inp:
        nexml = json.load(inp)["nexml"]
        tbi = nexml["treesById"]
    tree = None
    otus_id = None
    all_ids = []
    for trees_id, blob in tbi.items():
        tbi = blob["treeById"]
        tree = tbi.get(tree_id)
        otus_id = blob["@otus"]
        if tree is not None:
            break
        all_ids.extend(list(tbi.keys()))
    if tree is None:
        sys.exit(f'Tree id "{tree_id}" not found. IDs: {all_ids}')

    nd_2_conf = {}
    for nd_id, blob in conflict.items():
        if blob.get("status", "") == "conflicts_with":
            w = blob.get("witness", [])
            wn = blob.get("witness_name", [])
            assert len(w) == len(wn)
            assert len(w) > 0
            nd_2_conf[nd_id] = (len(w), w, wn)

    root_id = tree["^ot:rootNodeId"]
    otus_obj  = nexml["otusById"][otus_id]["otuById"]

    assert root_id == tree["^ot:specifiedRoot"]
    ebsi = tree["edgeBySourceId"]
    nbi = tree["nodeById"]
    indent_num = 0
    if root_at_id is None:
        root_at_id = root_id
    next_to_deal_with = ('', root_at_id, '')
    deferred_stack = []
    while next_to_deal_with:
        next_tdw = next_to_deal_with
        curr_pref, nd_id, fall_back_pref = next_tdw
        conflict = nd_2_conf.get(nd_id, '')
        ebsi_el = ebsi.get(nd_id)
        if ebsi_el is None:
            node_obj = nbi[nd_id]
            otu_id = node_obj.get("@otu")
            if otu_id:
                otu_obj = otus_obj[otu_id]
                ott_id = otu_obj.get('^ot:ottId')
                ott_name = otu_obj.get('^ot:ottTaxonName')
                if ott_name:
                    print(f"{curr_pref}{nd_id} {ott_name} ({ott_id})")
                else:
                    print(f"{curr_pref}{nd_id} UNMAPPED TIP")
            if deferred_stack:
                next_to_deal_with = deferred_stack.pop(0)
            else:
                break
            continue
        else:
            print(f"{curr_pref}{nd_id} {conflict}")
        nn = None
        num_items = len(ebsi_el)
        if num_items > 0:
            curr_pref = fall_back_pref
            for idx, tup in enumerate(ebsi_el.items()):
                edge_id, eblob = tup
                assert eblob["@source"] == nd_id
                tid = eblob["@target"]
                corner = ' └' if ((idx + 1)  == num_items)else ' ├'
                pref = curr_pref + corner
                if nn is None:
                    nn = tid
                    next_to_deal_with = (pref, tid, curr_pref + ' │')
                else:
                    deferred_stack.insert(0,(pref, tid, curr_pref + '  '))

    


if __name__ == "__main__":
    try:
        a, b, c = sys.argv[1], sys.argv[2], sys.argv[3]
        d = None
        if len(sys.argv) > 4:
            d = sys.argv[4]
    except:
        sys.exit('''Expecting 3 args:
  1. filepath to the phylo_snapshot nexson (or equivalent),
  2. filepath to a JSON returned by the conflict with OTT analysis,
  3. tree_id for the tree in the NexSON
''')
    main(a, b, c, d)
