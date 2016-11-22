#!/usr/bin/env python
from cStringIO import StringIO
import codecs
import json
import sys
import os
import re
taxon_pat = re.compile(r'^(.*)([ _]ott)(\d+)\s*$')
try:
    id_list_file, out_dir = sys.argv[1:]
except:
    sys.exit('Expecting a file with a list of Names + ott### (encoding OTT Ids) as the first argument and a propinquity OUTPUT dir as the second argument.\n')
btf = os.path.join(out_dir, "labelled_supertree", "broken_taxa.json")
if not os.path.isfile(btf):
    sys.exit('The file "{}" was not found\n'.format(btf))
with codecs.open(btf, 'r', encoding='utf-8') as inp:
    broken = json.load(inp)['non_monophyletic_taxa']
ctf = os.path.join(out_dir, "subproblems", "contesting-trees.json")
if not os.path.isfile(ctf):
    sys.exit('The file "{}" was not found\n'.format(ctf))
with codecs.open(ctf, 'r', encoding='utf-8') as inp:
    contesting = json.load(inp)


pref = 'https://devtree.opentreeoflife.org/opentree/argus/opentree7.2'
hels = []
with open(id_list_file, 'r') as inp:
    for line in inp:
        ls = line.strip()
        if not ls:
            continue
        m = taxon_pat.match(ls)
        if not m:
            sys.exit('ID file entry "{}" does not end with ott[0-9]+\n'.format(ls))
        ott_id = m.group(3)
        name = m.group(1)
        label = '<a target="_blank" href="https://tree.opentreeoflife.org/taxonomy/browse?id={i}">{n}</a>'.format(i=ott_id, n=name)
        idstr = 'ott{}'.format(ott_id)
        blob = broken.get(idstr)
        fragout = StringIO()
        if blob is None:
            fragout.write('  <li>{l} recovered as monophyletic at <a target="_blank" href="{p}@{n}">{n}</a>.</li>\n'.format(l=label, p=pref, n=idstr))
        else:
            ct = contesting.get(unicode(idstr), {})
            fragout.write('  <li>{} was not monophyletic. It was contested by <ol>\n'.format(label))
            for tfn in ct.keys():
                assert tfn.endswith('.tre')
                k = tfn[:-4]
                tmpl = 'the study@tree pair <a target="_blank" href="https://tree.opentreeoflife.org/curator/study/view/{s}/?tab=trees&tree={t}">{i}</a>'
                s, t = k.split('@')
                treelink = tmpl.format(s=s, t=t, i=k)
                fragout.write('      <li>{}</li>\n'.format(treelink))
            fragout.write("    </ol>\n")
            fragout.write("    Members of the taxon are attached to the full tree at<ol>\n")
            for x in blob.get('attachment_points', {}).keys():
                tmpl = 'synth node <a target="_blank" href="{p}@{n}">{n}</a>'
                s, t = k.split('@')
                treelink = tmpl.format(p=pref, n=x)
                fragout.write('      <li>{}</li>\n'.format(treelink))
            fragout.write("    </ol>\n")
        hels.append([ls, fragout.getvalue()])

hels.sort()
li_els = [i[1] for i in hels]
out = sys.stdout
out.write("""<html>
<head>
  <title>Report on Broken taxa</title>
  </head>
<body>
<p>This is a report on the handling of the taxa within Cnidaria based on a draft of the Open Tree synthetic tree
that was built during a FuturePhy sponsored workshop.
This tree is currently deployed on Open Tree's "devtree" server. A downside of that is the fact that the "conflicts with"
and "supported by" links to most studies will be broken links (and the lists will rarely even list the appropriate studies).
Even though, there are still many problems with this tree, we may deploy it to the "production" site soon to make it easier
to diagnose problems.
If that happens, this file will be regenerated to fix the links.
</p>
<p>
See <a href="https://drive.google.com/drive/folders/0Bw-1ley90MKnZEdpUVJuOXVlN1k">the 
google drive folder</a> for other notes.</p>
<ul>
""")
for li in li_els:
    out.write(li)
out.write("""</ul>
</body>
</html>
""")