#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals
import re, sys, argparse, codecs
from peyotl.ott import OTT
from peyotl.nexson_syntax import quote_newick_name

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='add ott names to newick string with ott ids')
    parser.add_argument('newick_file',
        help='path to the newick file containing OTT ids'
        )

    parser.add_argument('ott_dir',
        help='path to the open tree taxonomy file'
        )

    parser.add_argument('-i',
        dest='keep_ottids',
        action='store_true',
        default=False,
        help='use this flag to keep the OTT ids in addition to the names'
        )

    args = parser.parse_args()

    print("converting {f}".format(f=args.newick_file))
    print("using ott in {d}".format(d=args.ott_dir))
    if (args.keep_ottids):
        print("keeping OTT IDs in addition to names")
    else:
        print("replacing OTT IDs with names")

    # read pruned labelled synthesis tree
    ottpattern = re.compile(r"([(,)])(ott)(\d+)")
    mrcapattern = re.compile(r"([(,)])mrcaott(\d+)ott(\d+)")
    pos = 0
    ott = OTT(ott_dir=args.ott_dir)
    # load up the OTT dictionary...
    d = ott.ott_id_to_names
    outfile = codecs.open('ottnamelabelledtree.tre','w', encoding='utf-8')
    with open(args.newick_file,'r') as f:
        newick = f.read()
        for m in re.finditer(ottpattern,newick):
            ottid=int(m.group(3))
            ottresults = d[ottid]
            ottname=ottresults
            if isinstance(ottresults,tuple):
                ottname = ottresults[0]
            print(m.group(3), ottname)
            skippedchars = newick[pos:m.start()]
            outfile.write(skippedchars)
            outfile.write(m.group(1))
            if args.keep_ottids:
                label = quote_newick_name('{} ott{}'.format(ottname,ottid))
            else:
                label = quote_newick_name('{}'.format(ottname))
            outfile.write(label)
            pos=m.end()
        outfile.write(newick[pos:])
    f.close()
    outfile.close()
