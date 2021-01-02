# cleaned_ott
The primary artifact in this directory is `cleaned_ott.tre` which is
produced by `$(PEYOTL_ROOT)/scripts/ott/suppress_by_flag.py`

  * `cleaned_ott.tre` is a newick represenation of all taxa in OTT that
    do not have an ancestor that is flagged with any of the flags to prune.

  * `cleaned_ott.json` a provenance file contains the keys:
    * `flags_to_prune` value of the `cleaning_flags` of the config file
    * `version`  version of OTT
    * `num_monotypic_nodes`
    * `num_nodes`
    * `num_non_leaf_nodes`
    * `num_non_leaf_nodes_with_multiple_children`
    * `num_pruned_anc_nodes`
    * `num_tips`
    * `pruned` is an object with keys that are comma-separated lists of
        flags that caused pruning. For each key, the object holds:
        * `flags_causing_prune` which is a list of the flags that caused
            pruning (this is just the key split by a comma)
        * `anc_ott_id_pruned` is a list of OTT Ids that which had their
            subtrees excluded because of this set of flags. The prefix
            "anc_" here is just to emphasize that the set of Ids pruned
            is not all of the Ids that were excluded. If a genus OTT Id
            is pruned, then all of the species within the genus will
            also be pruned off the tree, but the species will not be listed
            in this field.

  * `ott_version.txt` copy of `version.txt` from the last version of OTT that was
  used to build the artifacts. So, if you change the version of OTT that you 
  are using, this file should be copied and trigger a rebuild of the pruned 
  taxonomy in cleaned_ott.tre

  * `cleaning_flags.txt` value of the `cleaning_flags` of the config file for
  the pipeline for the last build of the artifacts. These affect the pruning
  of OTT.  This setting is pulled out as a separate file to make it obvious
  when the "cleaned" taxonomy needs to be changed.

  * `root_ott_id.txt` value of the `root_ott_id` of the config file for
  the pipeline for the last build of the artifacts. These affect the pruning
  of OTT.  This setting is pulled out as a separate file to make it obvious
  when the "cleaned" taxonomy needs to be changed.


If you were to select `pruned/*/anc_ott_id_pruned` from `cleaned_ott.json`
you would get a set of nonoverlapping OTT Ids. If you were to cut the full
tree of OTT at the edges that connect these OTT Ids to their ancestors, then
the tree that is connected to the root of OTT should be identical to the
tree found in `cleaned_ott.tre`.

