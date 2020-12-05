#!/bin/bash
if test -z $1
then
    echo "expecting a studyID_treeID as an argument"
    exit 1
fi
study_tree="$1"
bin/prune_to_clean_mapped.py \
  --ott-dir="${OTT_DIR}" \
  --out-dir=cleaned_phylo \
  --ott-prune-flags=major_rank_conflict,major_rank_conflict_direct,major_rank_conflict_inherited,environmental,viral,nootu,barren,not_otu,extinct_inherited,extinct_direct,hidden,tattered \
  phylo_snapshot/${study_tree}.json && \
cat cleaned_phylo/${study_tree}-taxonomy.tre && \
otc-degree-distribution cleaned_phylo/${study_tree}-taxonomy.tre
