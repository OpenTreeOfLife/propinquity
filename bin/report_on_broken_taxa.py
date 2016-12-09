#!/usr/bin/env python

# creates an html broken taxon report that can be used for diagnosing
# which input trees break which taxa

# input file can be created with:
# grep -E -o  "[)]['A-Za-z][^,)(]+ott[0-9]+" cleaned_ott/cleaned_ott.tre  | sed -E 's/.*ott//'

from cStringIO import StringIO
import codecs
import argparse
import json, sys, os, re

def read_broken_taxa(out_dir):
    # check that the broken taxa file exists in the output directory; read
    # if present
    btf = os.path.join(out_dir, "labelled_supertree", "broken_taxa.json")
    if not os.path.isfile(btf):
        sys.exit('The file "{}" was not found\n'.format(btf))
    with codecs.open(btf, 'r', encoding='utf-8') as inp:
        data = json.load(inp)['non_monophyletic_taxa']
    return data

def read_contesting_trees(out_dir):
    # check that the contesting trees file exists in the output directory; read
    # if present
    ctf = os.path.join(out_dir, "subproblems", "contesting-trees.json")
    if not os.path.isfile(ctf):
        sys.exit('The file "{}" was not found\n'.format(ctf))
    with codecs.open(ctf, 'r', encoding='utf-8') as inp:
        data = json.load(inp)
    return data

def update_tree_counts(tree,tree_dict):
    if tree in tree_dict:
        tree_dict[tree] += 1
    else:
        tree_dict[tree] = 1
    return tree_dict

# output the html to stdout
def write_output(hels,tree_counts,ntaxa):
    hels.sort()
    li_els = [i[1] for i in hels]
    out = sys.stdout
    out.write("""<html>
    <head>
      <title>Report on Broken taxa</title>
      </head>
    <body>
    <p>This is a report on the handling of the {n} taxa broken (non-monophyletic)
    in opentree8.0 but in not the previous version (i.e. the newly-broken taxa).
    Scroll to the bottom to see a list of input trees and the number of taxa
    broken by each tree.
    </p>
    """.format(n=ntaxa))

    # print detail about each non-monophyletic taxa
    out.write("<ul>")
    for li in li_els:
        out.write(li)
    out.write("</ul>")

    # print info about how many taxa broken by various studies
    out.write("""<p><strong>Effect of input trees</strong></p>""")
    out.write("""<p>The offending trees (and number of taxa broken by each) are:</p><ul>""")
    for i in sorted(tree_counts, key=tree_counts.get, reverse=True):
    #for i in sorted(tree_counts.items(), key=lambda x: x[1]):
    #for k in tree_counts.keys():
        out.write("""<li>{n} broken taxa because of {t}</li>""".format(
            n=tree_counts[i],
            t=i))
    out.write("</ul>")

    # close the body and html tags
    out.write("""</body>
    </html>
    """)

if __name__ == "__main__":
    # get command line arguments (the list of taxa and the output dir)
    parser = argparse.ArgumentParser(description='write broken taxa report')
    parser.add_argument('id_list_file',
        help='file with a list of taxa to summarize in format name_ott###'
        )
    parser.add_argument('out_dir',
        help='path to the PROPINQUITY_OUT_DIR'
        )
    parser.add_argument('-a',
        dest='print_all',
        action='store_true',
        help='print results for all taxa in input file; default = only broken taxa'
        )
    args = parser.parse_args()

    # read info from propinquity output
    broken_taxa = read_broken_taxa(args.out_dir)
    contesting_trees = read_contesting_trees(args.out_dir)

    taxon_pat = re.compile(r'^(.*)([ _]ott)(\d+)\s*$')

    pref = 'https://devtree.opentreeoflife.org/opentree/argus/opentree8.0'
    tax_url = 'https://tree.opentreeoflife.org/taxonomy/browse?id='
    hels = []
    non_monophyletic = 0
    tree_counts = {}
    with open(args.id_list_file, 'r') as inp:
        for line in inp:
            ls = line.strip()
            if not ls:
                continue
            m = taxon_pat.match(ls)
            if not m:
                sys.exit('ID file entry "{}" does not end with ott[0-9]+\n'.format(ls))
            ott_id = m.group(3)
            name = m.group(1)

            # link to taxonomy browser; display taxon name
            label = '<a target="_blank" href="{t}{i}">{n}</a>'.format(
                t=tax_url,
                i=ott_id,
                n=name)
            idstr = 'ott{}'.format(ott_id)
            blob = broken_taxa.get(idstr)
            fragout = StringIO()
            if blob is None: # if this is not a broken taxa
                if args.print_all: # if we are printing info on all taxa
                    fragout.write('  <li>{l} recovered as monophyletic at <a target="_blank" href="{p}@{n}">{n}</a>.</li>\n'.format(l=label, p=pref, n=idstr))
            else:
                ct = contesting_trees.get(unicode(idstr), {})
                non_monophyletic += 1
                fragout.write('  <li>{} was not monophyletic. It was contested by <ol>\n'.format(label))
                for tfn in ct.keys():
                    assert tfn.endswith('.tre')
                    k = tfn[:-4]
                    tmpl = 'the study@tree pair <a target="_blank" href="https://tree.opentreeoflife.org/curator/study/view/{s}/?tab=trees&tree={t}">{i}</a>'
                    s, t = k.split('@')
                    treelink = tmpl.format(s=s, t=t, i=k)
                    fragout.write('      <li>{}</li>\n'.format(treelink))
                    update_tree_counts(k,tree_counts)
                fragout.write("    </ol>\n")
                fragout.write("    Members of the taxon are attached to the full tree at<ol>\n")
                for x in blob.get('attachment_points', {}).keys():
                    tmpl = 'synth node <a target="_blank" href="{p}@{n}">{n}</a>'
                    s, t = k.split('@')
                    treelink = tmpl.format(p=pref, n=x)
                    fragout.write('      <li>{}</li>\n'.format(treelink))
                fragout.write("    </ol>\n")
            hels.append([ls, fragout.getvalue()])
        inp.close()
        write_output(hels,tree_counts,non_monophyletic)
