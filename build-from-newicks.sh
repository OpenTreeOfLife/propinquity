#!/bin/bash
ottdir="${1}"
phyloranking="${2}"
if ! test -d "${ottdir}"
then
    echo "build-from-newicks.sh: expecting the first argument to be an argument to the taxonomy directory"
    exit 1
fi
if ! test -f "${phyloranking}"
then
    echo "build-from-newicks.sh: expecting the second argument to be a file listing the path to the newick files"
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
    cp "${i}" "phylo_snapshot" 
done

