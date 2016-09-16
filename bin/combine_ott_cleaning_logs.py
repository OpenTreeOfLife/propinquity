#!/usr/bin/env python
'''Writes html files that explains the synthesis run that was completed
'''

from __future__ import absolute_import, division, print_function, unicode_literals
from peyotl import read_as_json, write_as_json
import sys

if __name__ == '__main__':
    import argparse
    import os
    bin_dir, SCRIPT_NAME = os.path.split(__file__)
    propinquity_dir = os.path.dirname(bin_dir)
    parser = argparse.ArgumentParser(prog=SCRIPT_NAME, description='Simple tool to combine the logs from pruning via flags and pruning via higher-level taxa that have become tips')
    parser.add_argument('flag_pruned_json', nargs=1, metavar='F', type=str)
    parser.add_argument('higher_taxon_pruned_json', metavar='H', nargs=1, type=str)
    parser.add_argument('combined_json', nargs=1, metavar='O', type=str)
    args = parser.parse_args()
    fj_fn = args.flag_pruned_json[0]
    htj_fn = args.higher_taxon_pruned_json[0]
    out_fn = args.combined_json[0]
    blob = read_as_json(fj_fn)
    higher_taxon_blob = read_as_json(htj_fn)
    p = blob['pruned']
    httk = 'higher-taxon-tip'
    intk = 'empty-after-higher-taxon-tip-prune'
    high_tax_tip_pruned = higher_taxon_blob.get(httk, {})
    internal_high_tax_tip_pruned = higher_taxon_blob.get(intk, {})
    p[httk] = high_tax_tip_pruned
    p[intk] = internal_high_tax_tip_pruned
    n_ht_in_pruned = len(internal_high_tax_tip_pruned)
    n_ht_pruned = len(high_tax_tip_pruned)
    blob['num_non_leaf_nodes'] -= n_ht_in_pruned
    blob['num_pruned_anc_nodes'] += n_ht_in_pruned
    blob['num_tips'] -= n_ht_pruned
    blob['num_nodes'] -= (n_ht_pruned + n_ht_in_pruned)
    del blob['num_monotypic_nodes']
    del blob['num_non_leaf_nodes_with_multiple_children']
    blob['pruning_keys_not_from_flags'] = [httk, intk]
    write_as_json(blob, out_fn)
