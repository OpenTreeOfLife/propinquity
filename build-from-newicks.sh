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

if test -z "$PEYOTL_ROOT" ; then
    PEYOTL_ROOT=$(bin/config_checker.py opentree.peyotl ~/.opentree)
fi

if test -z "$PEYOTL_ROOT" ; then
    echo "Currently you need to have PEYOTL_ROOT in your env set to your local clone of https://github.com/mtholder/peyotl.git"
    echo "Alternatively you can set 'peyotl=...' in section [opentree] in ~/.opentree"
    exit 1
fi

echo "[opentree]" > config
echo "ott=${ottdir}" >> config
echo >> config
echo "[synthesis]" >> config
echo "collections = " >> config
echo >> config
echo "[taxonomy]" >> config
echo "cleaning_flags = " >> config

touch phylo_input/rank_collection.json

if test -f phylo_input/study_tree_pairs.txt
then
    rm phylo_input/study_tree_pairs.txt
fi
set -x
for i in $(cat "${phyloranking}")
do
    if ! test -f "${i}"
    then
        echo "build-from-newicks: input newick ${i} does not refer to a file."
        exit 1
    fi
    fn="$(basename $i)"
    stem="$(echo $fn | sed -e 's/\.tre$//')"
    tree_id="$(echo $stem | sed -E 's/^.*_([^_]+)$/\1/')"
    echo $tree_id
    echo $stem >> phylo_input/study_tree_pairs.txt
    python "${PEYOTL_ROOT}/scripts/nexson/propinquity_newick_to_nexson.py" "--ids=${tree_id}" $i > phylo_snapshot/"${stem}.json"
done

echo > phylo_input/collections.txt
echo > phylo_input/rank_collection.json
echo > phylo_input/study_tree_pairs.txt

echo > phylo_snapshot/concrete_rank_collection.json
echo > cleaned_phylo/needs_updating.txt
otc-taxonomy-parser -R --config=config > cleaned_phylo/root_ott_id.txt
echo > cleaned_phylo/cleaning_flags.txt

echo 0 > phylo_snapshot/git_shas.txt
echo 0 > cleaned_ott/ott_version.txt
echo > cleaned_ott/cleaning_flags.txt
otc-taxonomy-parser -R --config=config > cleaned_ott/root_ott_id.txt
echo > cleaned_phylo/needs_updating.txt
cp $phyloranking cleaned_phylo/phylo_inputs_cleaned.txt
#cp $phyloranking phylo_input/study_tree_pairs.txt
#sed 's/\.tre/\.json/' $phyloranking > cleaned_phylo/needs_updating.txt
cp $phyloranking exemplified_phylo/args.txt

echo > cleaned_phylo/root_ott_id.txt
bin/fake-collection.py $(cat "${phyloranking}") > phylo_snapshot/concrete_rank_collection.json
