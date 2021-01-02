# phylo_input
Created from an input tree collection using `$(PEYOTL_ROOT)/scripts/collection_export.py`

  * `rank_collection.json` is the collection to use for synthesis with the trees

  * `studies.txt` is a view of `rank_collection.json`. One studyID per line in the ranked order
  study IDs can be repeated! Created in anticipation of needing to `cat` a file to get 
  the study list.

  * `study_tree_pairs.txt` is a view of `rank_collection.json`. Entries are the pair
  of study ID and tree ID in the form: studyID_treeID
  They appear in the ranked order.