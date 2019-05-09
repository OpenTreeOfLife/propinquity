#!/usr/bin/env python
import codecs
import json
import sys
import os
usage = 'Expecting 1 argument (JSON edits) or 3: JSON, src_ott_tree, dest_ott_tree\n'
try:
    jfp = sys.argv[1]
    with codecs.open(jfp, mode='r', encoding='utf-8') as jinp:
        jout = json.load(jinp)
except:
    sys.stderr.write(usage)
    raise
if "edits" in jout:
    sys.exit('''Taxonomic changes need to be made in your version of OTT to move extinct taxa higher in the taxonomy!

Use:
    {}/bin/patch_taxonomy_by_bumping.py [PATH TO YOUR OTT DIR] {} [OUTPUT PATH FOR A PATCHED OTT DIR]
to create a modified version of OTT, then set that to be your OTT path for propinquity and rerun.

'''.format(os.path.abspath(os.curdir), os.path.abspath(jfp)))
if len(sys.argv) > 2:
    try:
        from shutil import copyfile
        copyfile(sys.argv[2], sys.argv[3])
    except:
        sys.stderr.write(usage)
        raise
