#!/usr/bin/env python
from peyotl import read_as_json, write_as_json
import csv
import sys
import os
import re

ott_id_from_str = re.compile(r'^ott(\d+)')

def parse_degree_dist(fn):
    header_pat = re.compile(r'Out-degree\S+Count')
    dd = []
    with open(fn, 'r') as inp:
        expecting_header = True
        for n, line in enumerate(inp):
            ls = line.strip()
            if not ls:
                continue
            if expecting_header:
                if header_pat.match(ls):
                    raise ValueError('expecting a header at line {}, but found "{}"'.format(1 + n, ls))
                expecting_header = False
            else:
                row = ls.split()
                assert len(row) == 2
                dd.append([int(i) for i in row])
    return dd

def parse_otc_taxonomy_parser_lost_taxa(fn):
    l = stripped_nonempty_lines(fn)
    ltrow_pat = re.compile(r"^depth=\d+\s+id=(\d+)\s+uniqname='.*'$")
    ois = set()
    for line in l:
        m = ltrow_pat.match(line)
        if not m:
            raise ValueError('lost_taxa file did not match pattern')
        i = int(m.group(1))
        assert i not in ois
        ois.add(i)
    return ois

def err(s):
    global num_errors
    num_errors += 1
    errstream.write('{} ERROR: {}\n'.format(prog_name, s))

if __name__ == '__main__':
    prog_name = os.path.basename(sys.argv[0])
    summary = {}
    errstream = sys.stdout
    num_errors = 0
    top_dir = sys.argv[1]
    bin_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
    sys.path.append(os.path.join(bin_dir))
    from document_outputs import stripped_nonempty_lines
    assessments_dir = os.path.join(top_dir, 'assessments')
    assert os.path.isdir(top_dir)
    cleaned_taxonomy = os.path.join(top_dir, 'cleaned_ott', 'cleaned_ott.tre')
    cleaned_taxonomy_json = os.path.join(top_dir, 'cleaned_ott', 'cleaned_ott.json')
    final_tree = os.path.join(top_dir, 'labelled_supertree', 'labelled_supertree.tre')
    # Check that we have the same # of leaves in the cleaned_ott and the final tree
    #
    tax_dd_file = os.path.join(assessments_dir, 'taxonomy_degree_distribution.txt')
    supertree_dd_file = os.path.join(assessments_dir, 'supertree_degree_distribution.txt')
    tdd = parse_degree_dist(tax_dd_file)
    sdd = parse_degree_dist(supertree_dd_file)
    if tdd[0] != sdd[0]:
        err('The number of leaves differed between the taxonomy and supertree')
        nt = {'result':'ERROR', 'data':[tdd[0][1], sdd[0][1]]}
    else:
        nt = {'result':'OK', 'data': tdd[0][1]}
    nt['description'] = 'Check that the cleaned version of the taxonomy and the supertree have the same number of leaves'
    summary['num_tips'] = nt
    annot_file = os.path.join(top_dir, 'annotated_supertree', 'annotations.json')
    annotations = read_as_json(annot_file)
    nodes_annotations = annotations['nodes']
    # Check that otc-taxonomy-parser and otc-unprune-solution-and-name-unnamed-nodes
    #   agree on the number of taxa that were lost
    #
    if False:
        ltb = {'result': 'Skipped test - have not updated tests to deal with 2 layers of taxon filtering', 'data': []}
        btb = dict(ltb)
        ub = dict(ltb)
    else:
        lt_file = os.path.join(assessments_dir, 'lost_taxa.txt')
        lt_name = 'otc-taxonomy-parser lost-taxon'
        lt_pair  = [lt_file, lt_name]
        lt_set = parse_otc_taxonomy_parser_lost_taxa(lt_file)
        bt_file = os.path.join(top_dir, 'labelled_supertree', 'broken_taxa.json')
        bt_name = 'otc-unprune-solution-and-name-unnamed-nodes broken_taxa.json'
        bt_pair  = [bt_file, bt_name]
        bt_blob = read_as_json(bt_file)
        bt_dict = bt_blob['non_monophyletic_taxa']
        if not bt_dict:
            bt_dict = {}

        aliased_in_tree = bt_blob.get('taxa_matching_multiple_ott_ids')
        if not aliased_in_tree:
            aliased_in_tree = {}
        aliased_in_broken = {}
        for key_in_tree, v in aliased_in_tree.items():
            for in_broken in v:
                aliased_in_broken[str(in_broken)] = key_in_tree
        cleaned_ott_json_pruned = read_as_json(cleaned_taxonomy_json).get('pruned', {})
        # pruned because they became empty
        httip_key = 'higher-taxon-tip'
        int_key = 'empty-after-higher-taxon-tip-prune'
        htpruned_ids = set()
        for key in [httip_key, int_key]:
            pl = set(cleaned_ott_json_pruned.get(key, []))
            htpruned_ids.update(pl)

        lte = {}
        for ott_id in lt_set:
            ott_id_str = 'ott{}'.format(ott_id)
            if (ott_id_str not in bt_dict) \
               and (ott_id not in htpruned_ids) \
               and (ott_id_str not in aliased_in_broken.keys()):
                err('{} was in {} but not {}'.format(repr(ott_id_str), lt_name, bt_name))
                lte[ott_id_str] = {'listed': lt_pair, 'absent': bt_pair}
        if bool(lte) or len(lt_set) != len(bt_dict):
            for ott_id_str in bt_dict.keys():
                ott_id = int(ott_id_from_str.match(ott_id_str).group(1))
                if (ott_id not in lt_set) and (ott_id_str not in aliased_in_tree):
                    err('{} was in {} but not {}'.format(ott_id_str, bt_name, lt_name))
                    lte[ott_id_str] = {'listed': bt_pair, 'absent': lt_pair}
        if lte:
            ltb = {'result': 'ERROR', 'data': [len(lt_set), lte]}
        else:
            ltb = {'result': 'OK', 'data': [len(lt_set)]}
        # Check that 'supported_by' is not empty for any node in the tree
        #
        unsup = {}
        broken_taxa_inc = []
        for node_id, supp in nodes_annotations.items():
            if node_id.startswith('ott'):
                if node_id in bt_dict:
                    err('Taxon {} found in tree but also in the list of "broken_taxa"'.format(node_id))
                    broken_taxa_inc.append(node_id)
            elif (('supported_by' not in supp) or (not supp['supported_by'])) \
               and (('terminal' not in supp) or (not supp['terminal'])):
                err('Unsupported node: {}'.format(node_id))
                unsup[node_id] = supp
        if broken_taxa_inc:
            btb = {'result': 'ERROR', 'data': broken_taxa_inc}
        else:
            btb = {'result': 'OK', 'data': broken_taxa_inc}
            if unsup:
                ub = {'result': 'ERROR', 'data':unsup}
            else:
                ub = {'result': 'OK', 'data':unsup}
    
    ltb['description'] = "Check that otcetera's tc-taxonomy-parser and otc-unprune-solution-and-name-unnamed-nodes tools agree about the number of taxa that are not present in the solution"
    btb['description'] = 'Check that none of the taxa listed as "lost" are in the annotations file'
    ub['description'] = 'Check that none of the nodes listed in the annotations file are completely unsuported'
    summary['lost_taxa'] = ltb
    summary['lost_taxa_included_in_tree'] = btb
    summary['unsupported_nodes'] = ub
    # Monophyly tests are env sensitive
    if 'MONOPHYLY_TEST_CSV_FILE' in os.environ:
        mp = []
        n_failures, n_passes, n_skipped = 0, 0, 0
        fn = os.environ['MONOPHYLY_TEST_CSV_FILE']
        with open(fn) as inp:
            for row in csv.reader(inp, delimiter=','):
                ott_id = 'ott{}'.format(row[1])
                if ott_id in nodes_annotations:
                    n_passes += 1
                elif ott_id in bt_dict:
                    n_failures += 1
                    err('Taxon {} from monophyly is not monophyletic in the tree'.format(ott_id))
                    mp.append(ott_id)
                else:
                    skip_msg = 'Monophyly test for {} treated as a skipped test because the taxon is not in the lost taxa or in the tree. (it could be the case that the synthesis was run on a subset of the full taxonomy)\n'
                    sys.stderr.write(skip_msg.format(ott_id))
                    n_skipped += 1
        if 'MONOPHYLY_TEST_SOURCE_NAME' in os.environ:
            src = os.environ['MONOPHYLY_TEST_SOURCE_NAME']
        else:
            src = fn
        if mp:
            mtb = {'result': 'ERROR', 'data': [n_passes, n_skipped, n_failures, mp]}
        else:
            mtb = {'result': 'OK', 'data': [n_passes, n_skipped, n_failures, mp]}
        mtb['description'] = 'Check that the taxa from the monophyly tests listed in {} are monophyletic in the tree.'.format(src)
        summary['monophyly'] = mtb
    else:
        sys.stderr.write('MONOPHYLY_TEST_CSV_FILE is not in the env, so no monophyly tests are being run\n')
    # serialize the summary
    #
    write_as_json(summary, os.path.join(assessments_dir, 'summary.json'), indent=2)
    sys.exit(num_errors)

