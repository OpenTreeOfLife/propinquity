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
    id_to_par_id = {}
    while True:
        taboo_set.add(curr_nd_id)
        curr_nd = nbi[curr_nd_id]
        ebsi_el = ebs.get(curr_nd_id)
        pcni = curr_nd_id
        c_added = False
        curr_nd['children'] = []
        otu_id = curr_nd.get('@otu')
        if otu_id:
            otu_obj = ntw.otus[otu_id]
            ott_id = otu_obj.get('^ot:ottId')
            curr_nd['ott_id'] = ott_id
            if ott_id is not None:
                curr_nd['ott_name'] = otu_obj['^ot:ottTaxonName']
        else:
            curr_nd['ott_id'] = None
        par_id = id_to_par_id.get(curr_nd_id)
        if par_id is None:
            assert curr_nd_id == ntw.root_node_id
        curr_nd['par_id'] = par_id
        yield curr_nd
        c = curr_nd['children']
        if ebsi_el:
            for idx, tup in enumerate(ebsi_el.items()):
                edge_id, eblob = tup
                assert eblob["@source"] == pcni
                tid = eblob["@target"]
                c.append(tid)
                assert tid not in id_to_par_id
                id_to_par_id[tid] = pcni
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

def common_anc_prefix(lap):
    non_none = [i for i in lap if i is not None]
    if len(non_none) == 0:
        return None
    if len(non_none) == 1:
        return non_none[0]
    fnn = non_none[0]
    rest = non_none[1:]
    common = []
    idx = 0
    while True:
        try:
            fid = fnn[idx]
            for nn in rest:
                if nn[idx] != fid:
                    return tuple(common)
            common.append(fid)
            idx += 1
        except IndexError:
            return tuple(common)

def get_parent(nd, nbi):
    par_id = nd['par_id']
    if par_id is None:
        return None
    return nbi[par_id]

def get_par_and_grandparent(nd, nbi):
    par = get_parent(nd, nbi)
    return (None, None) if par is None else (par, get_parent(par, nbi))

def calc_len_par_anc_list_skipping(curr_nd, par_nd, gpar_nd, nbi):
    curr_nd_id = curr_nd["@id"]
    sibs = [i for i in par_nd['children'] if i != curr_nd_id]
    pmai = common_anc_prefix([nbi[i]['anc_tup'] for i in sibs])
    real_par_ai = par_nd['anc_tup']
    if (not pmai) or (not real_par_ai):
        par_shortened = 0
    else:
        par_shortened = len(pmai) - len(real_par_ai)
    assert par_shortened >= 0
    if gpar_nd is None:
        return par_shortened, 0, pmai, None, None
    par_nd_id = par_nd["@id"]
    aunts = [i for i in gpar_nd['children'] if i != par_nd_id]
    aunts_ai = [nbi[i]['anc_tup'] for i in aunts]
    par_gen_ai = aunts_ai + [pmai]
    gpmai = common_anc_prefix(par_gen_ai)
    real_gpar_ai = gpar_nd['anc_tup']
    if (not gpmai) or (not real_gpar_ai):
        gpar_shortened = 0
    else:
        gpar_shortened = len(gpmai) - len(real_gpar_ai)
    assert gpar_shortened >= 0
    return par_shortened, gpar_shortened, pmai, real_gpar_ai, gpmai
    

def detect_problem_mapping(ntw, nex_preorder, to_tax_nd):
    nbi = ntw._node_by_id
    for nd in reversed(nex_preorder):
        children = nd['children']
        if children:
            nd['anc_tup'] = common_anc_prefix([nbi[i]['anc_tup'] for i in children])
            # print(f"{nd['@id']} -> {nd['anc_tup']}")
        else:
            ott_id = nd.get('ott_id')
            nd['anc_tup'] = None
            if ott_id is None:
                sys.stderr.write(f'  Node {nd["@id"]} is UNMAPPED\n')
            else:
                tax_nd = to_tax_nd.get(ott_id)
                if tax_nd is None:
                    sys.stderr.write(f'  Node {nd["@id"]} is mapped to a taxon {ott_id} not in the induced taxonomy\n')
                else:
                    nd['anc_tup'] = tax_nd.anc_tup

    sortable = []
    for nd in reversed(nex_preorder):
        score_list = [0, 0, 0, 0]
        par, gpar = get_par_and_grandparent(nd, nbi)
        if par is None:
            continue
        nat = nd['anc_tup']
        pat, pmai, gpat, gpmai = None, None, None, None
        if nat is not None:
            pat = par['anc_tup']
            if pat is None:
                items_lost = len(nat)
            else:
                items_lost = len(nat) - len(pat)
            assert items_lost >= 0
            score_list[1] = items_lost
            par_missing, gpar_missing, pmai, gpat, gpmai = calc_len_par_anc_list_skipping(nd, par, gpar, nbi)
            score_list[2] = par_missing
            score_list[3] = gpar_missing
        score_list[0] = sum(score_list[1:])
        nd_id = nd["@id"]
        sortable_val = tuple(score_list + [nd_id, nd, pat, pmai, gpat, gpmai])
        sortable.append(sortable_val)
    sortable.sort(reverse=True)
    return sortable

          

def main(nexson_fp, conflict_call_fp, tree_id, taxonomy_fp, root_at_id=None):
    nexson_blob = read_as_json(nexson_fp)
    ntw = NexsonTreeWrapper(nexson_blob, tree_id, log_obj=None, logger_msg_obj=None)
    ntw.prune_to_ingroup()
    ntw.prune_unmapped_leaves()
    ott_id_to_sortable_list = ntw.group_and_sort_leaves_by_ott_id()
    nex_preorder = [i for i in ntw_preorder(ntw)]
    
    
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
    
    ott_id2_tax_nd = {}
    for nd in tax_tree.preorder_node_iter():
        ott_id2_tax_nd[nd.label] = nd
        if nd is tax_tree.seed_node:
            nd.anc_tup = tuple()
            continue
        par = nd.parent_node
        nd.anc_tup = tuple(list(par.anc_tup) + [par.label])
    
    x = detect_problem_mapping(ntw, nex_preorder, ott_id2_tax_nd)
    for idx, sv in enumerate(x):
        nd_id, nd, pat, pmai, gpat, gpmai = sv[-6:]
        ott_id = nd.get('ott_id')
        if ott_id is None:
            print(sv)
        else:
            ott_name = nd.get('ott_name')
            nat = nd['anc_tup']
            print(f"Node {nd_id} mapped to {ott_name} ({ott_id}): {sv[:-6]}")
            print(f"  node_anc_tup = {nat}")
            print(f"  par_anc_tup  = {pat}")
            print(f"  par if del   = {pmai}")
            print(f"  gpar if del  = {gpat}")
            print(f"  gpar if del  = {gpmai}")
        if idx > 40:
            break
    

    return

    z = """with open(conflict_call_fp, "r") as inp:
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
    """
    


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
