#!/bin/bash
ottdir="${OTT_DIR}"
phyloranking="${1}"
if ! test -d "${ottdir}"
then
    echo "build-from-newicks.sh: expecting OTT_DIR to be in your environment and to specify the taxonomy directory"
    exit 1
fi
if ! test -f "${phyloranking}"
then
    echo "build-from-newicks.sh: expecting the second argument to be a file listing the path to the newick files"
    exit 1
fi
if test -z "$PEYOTL_ROOT"
then
    echo "currently you need to have PEYOTL_ROOT in your env set to your local clone of https://github.com/mtholder/peyotl.git"
    exit 1
fi

touch phylo_input/rank_collection.json

if test -f phylo_input/study_tree_pairs.txt
then
    rm phylo_input/study_tree_pairs.txt
fi

for i in $(cat "${phyloranking}")
do
    if ! test -f "${i}"
    then
        echo "build-from-newicks: input newick ${i} does not refer to a file."
        exit 1
    fi
    fn="$(basename $i)"
    stem="$(echo $fn | sed -e 's/\.tre$//')"
    echo $stem >> phylo_input/study_tree_pairs.txt
    python "${PEYOTL_ROOT}/scripts/nexson/propinquity_newick_to_nexson.py" $i > phylo_snapshot/"${stem}.json"
done

