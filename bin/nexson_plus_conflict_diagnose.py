#!/usr/bin/env python3
import sys
import json
    

def main(nexson_fp, conflict_call_fp, tree_id):
    with open(conflict_call_fp, "r") as inp:
        conflict = json.load(inp)
    with open(nexson_fp, "r") as inp:
        tbi = json.load(inp)["nexml"]["treesById"]
    tree = None
    all_ids = []
    for trees_id, blob in tbi.items():
        tbi = blob["treeById"]
        tree = tbi.get(tree_id)
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
    assert root_id == tree["^ot:specifiedRoot"]
    ebsi = tree["edgeBySourceId"]
    indent_num = 0
    next_to_deal_with = (indent_num, root_id)
    deferred_stack = []
    while next_to_deal_with:
        next_tdw = next_to_deal_with
        idn, nd_id = next_tdw
        conflict = nd_2_conf.get(nd_id, '')
        istr = ' '*idn
        print(f"{istr}{nd_id} {conflict}")
        ebsi_el = ebsi.get(nd_id)
        if ebsi_el is None:
            if deferred_stack:
                next_to_deal_with = deferred_stack.pop(0)
            else:
                break
            continue
        nn = None
        for edge_id, eblob in ebsi_el.items():
            assert eblob["@source"] == nd_id
            tid = eblob["@target"]
            if nn is None:
                nn = tid
                next_to_deal_with = (1+idn, nn)
            else:
                deferred_stack.insert(0,(1+idn, tid))

    


if __name__ == "__main__":
    try:
        a, b, c = sys.argv[1], sys.argv[2], sys.argv[3]
    except:
        sys.exit('''Expecting 3 args:
  1. filepath to the phylo_snapshot nexson (or equivalent),
  2. filepath to a JSON returned by the conflict with OTT analysis,
  3. tree_id for the tree in the NexSON
''')
    main(a, b, c)
