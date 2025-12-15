#!/bin/bash
PHYLESYSTEM_PAR="../phylesystem/shards"
if ! test -d "${PHYLESYSTEM_PAR}/phylesystem-1/study" ; then
	echo need to generalize this script. Did not find dir at "${PHYLESYSTEM_PAR}/phylesystem-1/study"
	exit 1
fi
cd "${PHYLESYSTEM_PAR}/phylesystem-1/" || exit
git pull origin || exit
cd - || exit

if ! test -d cruft ; then
	echo need to generalize this script. Did not find dir at cruft for storing temp files
	exit 1
fi

grep -r -P "^\\\"\^ot[:]ottId" "${PHYLESYSTEM_PAR}/phylesystem-1/study" \
  | sed -E "s/.*(.._[0-9]+\.json)/\1/" \
  | sed -E "s/..ot.ottId..//" \
  | sed -E 's/,//' > cruft/mapped-ot-ids.txt

wc -l cruft/mapped-ot-ids.txt
