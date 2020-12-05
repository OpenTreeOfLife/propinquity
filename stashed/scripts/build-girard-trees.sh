#!/bin/bash
set -x
export PROPINQUITY_OUT_DIR="girard/propinquity-out"
export OTT_DIR="girard/percomorph"
export OTC_CONFIG="${PWD}/girard/config"
./build-from-newicks.sh "girard/phylo-rankings.txt" || exit
make || exit
#make ${PROPINQUITY_OUT_DIR}/annotated_supertree/annotations.json || exit
#make extra || exit
#make ${PROPINQUITY_OUT_DIR}/assessments/summary.json || exit
make html || exit
# make clean || exit
# rm -f "$PROPINQUITY_OUT_DIR/config"
