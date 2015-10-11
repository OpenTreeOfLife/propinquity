# phylo_snapshot
This directory holds a cache of NexSON files for each tree used in the synthesis.

`$(PEYOTL_ROOT)/scripts/phylesystem/export_studies_from_collection.py` is the tool
that generates the study JSON files. Note that this tool only touches the snapshot
file if the existing file differs from the previous content of that file. So building
this snapshot does not necessarily touch all of the studies.

  * `concrete_rank_collection.json` is a copy fo the `phylo_input/rank_collection.json`
  collection, but with the current phylesystem SHA filled in for every empty SHA. This
  means that you should be able to recreate this set of phylogenetic inputs at any
  point by using this form of the collection.

  * `git_shas.txt` is the SHA of the head of phylesystem shards. It is used to tell whether
  or not the cached JSON might be out of date (if the phylesystem has not advanced, then 
  this cache should be up to date)

  * `stdouterr.txt` the standard err and out streams of the 
  `$(PEYOTL_ROOT)/scripts/phylesystem/export_studies_from_collection.py` processes.

  * `pg_*_tree*.json` and `ot_*_tree*.json` the snapshot of the studyID + treeID
  combination indicated by the file name. **TODO** perhaps we should add the SHA
  to the filename to make invalidation of the cache easier to detect.
