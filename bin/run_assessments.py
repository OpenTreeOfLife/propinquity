#!/usr/bin/env python
from peyotl import read_as_json, write_as_json
import subprocess
import sys
import os
import re

ott_id_from_str = re.compile('^ott(\d+)')

def parse_degree_dist(fn):
    header_pat = re.compile(r'Out-degree\S+Count')
    dd = []
    with open(fn, 'rU') as inp:
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
    final_tree = os.path.join(top_dir, 'labelled_supertree', 'labelled_supertree.tre')
    # Check that we have the same # of leaves in the cleaned_ott and the final tree
    #
    tax_dd_file = os.path.join(assessments_dir, 'taxonomy_degree_distribution.txt')
    supertree_dd_file = os.path.join(assessments_dir, 'supertree_degree_distribution.txt')
    tdd = parse_degree_dist(tax_dd_file)
    sdd = parse_degree_dist(supertree_dd_file)
    if tdd[0] != sdd[0]:
        err('The number of leaves differed between the taxonomy and supertree')
        summary['num_tips'] = ['ERROR', [tdd[0][1], sdd[0][1]]]
    else:
        summary['num_tips'] = ['OK', tdd[0][1]]
    # Check that otc-taxonomy-parser and otc-unprune-solution-and-name-unnamed-nodes
    #   agree on the number of taxa that were lost
    #
    lt_file = os.path.join(assessments_dir, 'lost_taxa.txt')
    lt_name = 'otc-taxonomy-parser lost-taxon'
    lt_pair  = [lt_file, lt_name]
    lt_set = parse_otc_taxonomy_parser_lost_taxa(lt_file)
    bt_file = os.path.join(top_dir, 'labelled_supertree', 'broken_taxa.json')
    bt_name = 'otc-unprune-solution-and-name-unnamed-nodes broken_taxa.json'
    bt_pair  = [bt_file, bt_name]
    bt_dict = read_as_json(bt_file)['non_monophyletic_taxa']
    lte = {}
    for ott_id in lt_set:
        ott_id_str = 'ott{}'.format(ott_id)
        if ott_id_str not in bt_dict:
            err('{} was in {} but not {}'.format(ott_id_str, lt_name, bt_name))
            lte[ott_id_str] = {'listed': lt_pair, 'absent': bt_pair}
    if bool(lte) or len(lt_set) != len(bt_dict):
        for ott_id_str in bt_dict.keys():
            ott_id = int(ott_id_from_str.match(ott_id_str).group(1))
            if ott_id not in lt_set:
                err('{} was in {} but not {}'.format(ott_id_str, bt_name, lt_name))
                lte[ott_id_str] = {'listed': bt_pair, 'absent': lt_pair}
    summary['lost_taxa'] = ['ERROR', [len(lt_set), lte]] if bool(lte) else ['OK', len(lt_set)]
    # Check that 'supported_by' is not empty for any node in the tree
    #
    annot_file = os.path.join(top_dir, 'annotated_supertree', 'annotations.json')
    annotations = read_as_json(annot_file)
    nodes_annotations = annotations['nodes']
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
    summary['lost_taxa_included_in_tree'] = ['ERROR' if broken_taxa_inc else 'OK', broken_taxa_inc]
    summary['unsupported_nodes'] = ['ERROR' if unsup else 'OK', unsup]

    # serialize the summary
    #
    write_as_json(summary, os.path.join(assessments_dir, 'summary.json'), indent=2)
    sys.exit(num_errors)

