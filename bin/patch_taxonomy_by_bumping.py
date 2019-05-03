#!/usr/bin/env python
import codecs
from shutil import copyfile

import json
import sys
import os
from peyotl.ott import OTT
from peyotl import write_as_json

def write_modified_taxonomy_tsv(inf, outf, uid_id_to_new_parent):
    m = {}
    for line in inf:
        ls = line.split('\t')
        uid = ls[0]
        new_par = uid_id_to_new_parent.get(uid)
        if new_par is None:
            outf.write(line)
            continue
        assert ls[1] == '|'
        old_par = ls[2]
        ls[2] = new_par
        m[uid] = {'old_parent': old_par, 'new_parent': new_par}
        outf.write('\t'.join(ls))
    return m

def main(ott_dir, move_json_filepath, out_dir):
    assert os.path.isdir(ott_dir)
    with codecs.open(move_json_filepath, mode='r', encoding='utf-8') as jinp:
        jout = json.load(jinp)
    move_edit_dict = jout["edits"]
    fossil_id_to_parent = {}
    for mk, mv in move_edit_dict.items():
        assert mk.startswith('ott')
        k = mk[3:].strip()
        np = mv["new_parent"]
        assert np.startswith('ott')
        v = np[3:].strip()
        fossil_id_to_parent[k] = v
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    needs_taxonomy = True
    if fossil_id_to_parent:
        infp = os.path.join(ott_dir, 'taxonomy.tsv')
        outfp = os.path.join(out_dir, 'taxonomy.tsv')
        needs_taxonomy = False
        with codecs.open(infp, 'rU', encoding='utf-8') as inp:
            with codecs.open(outfp, 'w', encoding='utf-8') as outp:
                m = write_modified_taxonomy_tsv(inp, outp, fossil_id_to_parent)
        outfp = os.path.join(out_dir, 'patched_by_bumping.json')
        write_as_json(m, outfp)
    for fn in OTT.FILENAMES:
        if (not needs_taxonomy) and fn == 'taxonomy.tsv':
            continue
        infp = os.path.join(ott_dir, fn)
        outfp = os.path.join(out_dir, fn)
        copyfile(infp, outfp)

if __name__ == '__main__':
    try:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
    except:
        sys.stderr.write('exiting due to an exception...\n')
        raise
