# cleaned_phylo
This directory holds the newick trees for the phylogenetic inputs after problematically
mapped tips have been removed.
`bin/prune_to_clean_mapped.py` uses the OTT pruning flags,
OTT itself, and the [`phylo_snapshot`](../phylo_snapshot/README.md) files to populate
this directory.

## Procedure
  1. If the tree has `^ot:inGroupClade` set to a node, then that node and all of
  its descendants will be retained and the "outgroup" will be pruned off the tree. 
  **TODO** Should the presence of an inGroupClade be treated as mandatory?
  2. If the tree has any leaves connected to an `otu` that does not have a `ot:^ottId`
  property, these nodes are pruned as "unmapped"
  3. If the OTT Id for a leaf is not in OTT (or the forwarding file), the leaf is
  pruned as an "unrecognized_ott_id"
  4. If the OTT Id for a leaf is forwarded to a new OTT Id, but that Id is unrecognized,
  the the leaf is pruned as an "forwarded_to_unrecognized_ott_id"
  5. If the taxonomic ancestor of an OTT Id was flagged by one of the OTT prune flags,
  then the leaf is pruned as "flagged"
  6. If the OTT Id for a leaf is mapped to a taxon that is a taxonomic ancestor
  of another leaf in the tree, then the leaf is pruned as "mapped_to_taxon_containing_other_mapped_tips"
  7. If there are multiple leaves mapped to the same OTT Id, one is chosen as an 
  exemplar. Either because it had the `^ot:isTaxonExemplar` or because it had a node
  id that is "lower" in lexicographic sort than any other node Id. **TODO** could be locale-specific, I suppose.

## Artifacts
  1. `pg_*_tree*.tre` and `ot_*_tree*.tre` the cleaned tree in newick. The tip 
  names have the form: taxon name_nodeID_ottID

  1. `pg_*_tree*.json` and `ot_*_tree*.json` a log of the pruning actions that 
  took place for the corresponding tree. 
  The other properties names other than `EMPTY_TREE` and `revised_ingroup_node`
  hold object with a `nodes` array and an `edges` array
  that correspond to the nodeId and edgeIds of the pruned or suppressed nodes and
  edges. The property name indicates the reason for the pruning.
* `EMPTY_TREE` If all of the nodes were pruned object in this JSON will contain a 
`EMPTY_TREE`     : true` property. 
* `revised_ingroup_node` if the pruning of problematic node makes the ingroup
node trivial, then this node will hold the ID of the node that is root of the
emitted tree (otherwise the root node should agree be the ingroup node specified
in the NexSON).
* `became_trivial` for internal nodes/edges which have out degree=1 as a result
of a child/some children being pruned.
* `flagged` the OTT Id or one of its taxonomic ancestors had a flag indicating
that it should be pruned.
* `forwarded_to_unrecognized_ott_id` OTT Id was forwarded to an unknown Id
* `mapped_to_taxon_containing_other_mapped_tips` The tip was mapped to an
higher taxon, and taxonomic descendants of that taxon in OTT are mapped to
other leaves in this tree.
* `outgroup` the node was not a descendant of the ingroup node
* `replaced_by_arbitrary_node` - multiple leaves were mapped to the same
OTT Id, and none of them were flagged as being the exemplar for that taxon. 
The nodes were sorted by nodeId, and the smallest node Id was chosen as the
exemplar.
* `replaced_by_exemplar_node` - multiple leaves were mapped to the same
OTT Id, and at least one of them was flagged as being the exemplar for that taxon. 
(if there were multiple exemplar nodes, then the same sorting as described above
was chosen to choose among them)
* `unmapped_otu` - the OTU for the node had no OTT Id.
* `unrecognized_ott_id` - the OTT Id was not recognized by this version of 
the OTT.

  3. `cleaning_flags.txt` value of the `cleaning_flags` of the config file for
  the pipeline for the last build of the artifacts. These affect the pruning
  of OTT

  4. `needs_updating.txt` a list of studies for which the `.tre` file is older than
  the corresponding `../phylo_snapshot/*.json` file.

  5. `phylo_inputs_cleaned.txt` sentinel for successful execution of `prune_to_clean_mapped.py`
