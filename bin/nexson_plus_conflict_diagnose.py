#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
from dendropy import Tree
from propinquity import NexsonTreeWrapper, read_as_json

def ntw_preorder(ntw):
    nbi = ntw._node_by_id
    ebs = ntw._edge_by_source
    curr_nd_id = ntw.root_node_id
    nd_id_stack = []
    taboo_set = set()
    while True:
        taboo_set.add(curr_nd_id)
        curr_nd = nbi[curr_nd_id]
        yield curr_nd
        ebsi_el = ebs.get(curr_nd_id)
        pcni = curr_nd_id
        c_added = False
        curr_nd['children'] = []
        c = curr_nd['children']
        if ebsi_el:
            for idx, tup in enumerate(ebsi_el.items()):
                edge_id, eblob = tup
                assert eblob["@source"] == pcni
                tid = eblob["@target"]
                c.append(nbi[tid])
                if tid not in taboo_set:
                    if not c_added:
                        curr_nd_id = tid
                        c_added = True
                    else:
                        nd_id_stack.append(tid)
        if not c_added:
            if not nd_id_stack:
                break
            curr_nd_id = nd_id_stack.pop()
            






def main(nexson_fp, conflict_call_fp, tree_id, taxonomy_fp, root_at_id=None):
    nexson_blob = read_as_json(nexson_fp)
    ntw = NexsonTreeWrapper(nexson_blob, tree_id, log_obj=None, logger_msg_obj=None)
    ntw.prune_to_ingroup()
    ntw.prune_unmapped_leaves()
    ott_id_to_sortable_list = ntw.group_and_sort_leaves_by_ott_id()
    nex_preorder = [i for i in ntw_preorder(ntw)]
    print(f"len(ott_id_to_sortable_list) = {len(ott_id_to_sortable_list)}")
    

    # tax_tree.print_plot(show_internal_node_labels=True)
    print(f"ntw.root_node_id = {ntw.root_node_id}")
    sys.exit('early\n')

    tax_tree = Tree.get_from_path(taxonomy_fp, schema="newick")
    for nd in tax_tree.postorder_node_iter():
        if not nd.label:
            nd.label = nd.taxon.label
        nd.label = int(nd.label)
        children =nd.child_nodes()
        if children:
            nd.leaf_des = set()
            for c in children:
                nd.leaf_des.update(c.leaf_des)
        else:
            nd.leaf_des = set([nd.label])
        print(nd.label)
    for nd in tax_tree.preorder_node_iter():
        if nd is tax_tree.seed_node:
            nd.anc_id = tuple()
            continue
        par = nd.parent_node
        nd.anc_id = tuple(list(par.anc_id) + [par.label])
        print(nd.label, nd.anc_id)
    sys.exit('early\n')

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
        a, b, c, d = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
        e = None
        if len(sys.argv) > 5:
            e = sys.argv[5]
    except:
        sys.exit('''Expecting 4 or 5 args:
  1. filepath to the phylo_snapshot nexson (or equivalent),
  2. filepath to a JSON returned by the conflict with OTT analysis,
  3. tree_id for the tree in the NexSON
  4. path to newick taxonomy induced by tree
  5. (OPTIONAL) node ID to root on.
''')
    main(a, b, c, d, e)
