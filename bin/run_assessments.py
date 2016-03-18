#!/usr/bin/env python
import subprocess
import sys
import os
import re

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

if __name__ == '__main__':
    top_dir = sys.argv[1]
    sys.path.append(os.path.join(top_dir, 'bin'))
    from document_outputs import stripped_nonempty_lines
    assessments_dir = os.path.join(top_dir, 'assessments')
    assert os.path.isdir(top_dir)
    cleaned_taxonomy = os.path.join(top_dir, 'cleaned_ott', 'cleaned_ott.tre')
    final_tree = os.path.join(top_dir, 'labelled_supertree', 'labelled_supertree.tre')
    tax_dd_file = os.path.join(assessments_dir, 'taxonomy_degree_distribution.txt')
    supertree_dd_file = os.path.join(assessments_dir, 'supertree_degree_distribution.txt')
    tdd = parse_degree_dist(tax_dd_file)
    sdd = parse_degree_dist(supertree_dd_file)
    if tdd[0] != sdd[0]:
        raise ValueError('The number of leaves differed between the taxonomy and supertree')
    lt_file = os.path.join(assessments_dir, 'lost_taxa.txt')
    lt_dict = parse_otc_taxonomy_parser_lost_taxa(lt_file)
