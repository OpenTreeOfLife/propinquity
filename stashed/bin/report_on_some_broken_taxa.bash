#!/bin/bash
# A simple helper script to report on a set of higher taxa ott IDs
# takes 2 arguments:
#    file path to a tree file that has the higher taxa of interest (with names + an _ott#### suffix)
#    the propinquity OUTPUT directory for a synthesis run
d="$(dirname $0)"
treefile="$1"
outdir="$2"
if ! test -f "${treefile}" ; then
    echo "\"${treefile}\" does not exist"
    exit 1
fi
btf="${outdir}/labelled_supertree/broken_taxa.json"
if ! test -f "${btf}" ; then
    echo "\"${btf}\" does not exist"
    exit 1
fi
fn=".tmp-scratch-ott-ids-of-interest.txt"
grep -E -o  "[)]['A-Za-z][^,)(]+ott[0-9]+" "${treefile}"  | sed -E "s/^[)]'?//" > "${fn}"
python "${d}/report_on_broken_taxa.py" "${fn}" "${outdir}"