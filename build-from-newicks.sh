#!/bin/bash

# Usage (example):
#  $ export PROPINQUITY_OUT_DIR=~/example2
#  $ export OTT_DIR=$(pwd)/examples/2/taxonomy/
#  $ make clean && ./build-from-newicks.sh examples/2/three-phylo-rankings.txt
#  $ make -j2 all extra
#
#  -- Continuing with this does not work: --
#  $ make clean
#  $ make -j2 all extra
#
#  -- It doesn't work because `make clean` removes the fake files.
#     If we make a fake phylesystem and collections, then it could work.
#
# * Right now we hardcode the cleaning flags to "major_rank_conflict,major_rank_conflict_inherited,environmental,unclassified_inherited,unclassified,viral,barren,not_otu,incertae_sedis,incertae_sedis_inherited,extinct_inherited,extinct,hidden,unplaced,unplaced_inherited,was_container,inconsistent,hybrid,merged"
#   + We could perhaps put a cleaning_flags file in the example directories...
#   + Should we then just have a single phylo-rankings.txt file per directory?
phyloranking="${1}"
PROPINQUITY_OUT_DIR=${PROPINQUITY_OUT_DIR:-.}
if ! test -d "${PROPINQUITY_OUT_DIR}"
then
    mkdir "${PROPINQUITY_OUT_DIR}" || exit
fi
ottdir="${OTT_DIR}"
if test -z "${ottdir}" && test -f "$HOME/.opentree"
then 
    ottdir=$(bin/config_checker.py opentree.ott ~/.opentree)
    echo "OTT_DIR set toot set, using '${ottdir}' from ~/.opentree"
fi
if test -z "${ottdir}"; then
    echo "OTT directory not set, quitting."
    exit 1
fi
if test -z "${ottdir}"
then
    echo "build-from-newicks.sh: expecting OTT_DIR to be in your environment and to specify the taxonomy directory"
    exit 1
fi
if ! test -d "${ottdir}"
then
    echo "build-from-newicks.sh: OTT_DIR is set, but is not a directory:"
    echo "  OTT_DIR=${ottdir}"
    exit 1
fi
if ! test -f "${phyloranking}"
then
    echo "build-from-newicks.sh: expecting the first argument to be a file listing the path to the newick files"
    exit 1
fi
if test -z "$PEYOTL_ROOT" ; then
    PEYOTL_ROOT=$(bin/config_checker.py opentree.peyotl ~/.opentree)
    if test -z "$PEYOTL_ROOT" ; then
        echo "Currently you need to have PEYOTL_ROOT in your env set to your local clone of https://github.com/mtholder/peyotl.git"
        echo "Alternatively you can set 'peyotl=...' in section [opentree] in ~/.opentree"
        exit 1
    fi
fi
CONFIG=$PROPINQUITY_OUT_DIR/config
echo -n "Generating ${PROPINQUITY_OUT_DIR}/config ... "
echo "[opentree]" > $CONFIG
echo "ott=${ottdir}" >> $CONFIG
echo >> $CONFIG
echo "[synthesis]" >> $CONFIG
echo "collections = " >> $CONFIG
echo >> $CONFIG
echo "[taxonomy]" >> $CONFIG
echo "cleaning_flags = major_rank_conflict,major_rank_conflict_inherited,environmental,unclassified_inherited,unclassified,viral,barren,not_otu,incertae_sedis,incertae_sedis_inherited,extinct_inherited,extinct,hidden,unplaced,unplaced_inherited,was_container,inconsistent,hybrid,merged" >> $CONFIG
echo "done."

mkdir -p "$PROPINQUITY_OUT_DIR/phylo_snapshot"
mkdir -p "$PROPINQUITY_OUT_DIR/phylo_input"

echo -n "Generating nexson tree files from newick files ... "
phyloranking_dir=$(dirname ${phyloranking})
for filename in $(cat "${phyloranking}")
do
    if ! test -f "${filename}"
    then
        echo "build-from-newicks: input newick ${filename} does not refer to a file."
        exit 1
    fi
    fn="$(basename $filename)"
    stem="$(echo $fn | sed -e 's/\.tre$//')"
    tree_id="$(echo $stem | sed -E 's/^.*@(.+)$/\1/')"
    echo $stem >> "$PROPINQUITY_OUT_DIR/phylo_input/study_tree_pairs.txt"
    python "${PEYOTL_ROOT}/scripts/nexson/propinquity_newick_to_nexson.py" "--ids=${tree_id}" "${filename}" > "$PROPINQUITY_OUT_DIR/phylo_snapshot/${stem}.json"
done
echo "done."

# Fake export_studies_from_collection
echo -n "Generating collection JSON for supplied newicks ... "
cat "${phyloranking}" | bin/fake-collection.py  > $PROPINQUITY_OUT_DIR/phylo_snapshot/concrete_rank_collection.json

make fakephylesystem
