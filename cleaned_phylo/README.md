# cleaned_phylo

  * `pg_*_tree*.tre` and `ot_*_tree*.tre` the cleaned tree in newick. The tip 
  names have the form: taxon name_nodeID_ottID


  * `pg_*_tree*.json` and `ot_*_tree*.json` a log of the pruning actions that 
  took place for the corresponding tree. 
    * `EMPTY_TREE` If all of the nodes were pruned object in this JSON will contain a 
    `EMPTY_TREE: true` property. 
    * `revised_ingroup_node` if the pruning of problematic node makes the ingroup
    node trivial, then this node will hold the ID of the node that is root of the
    emitted tree (otherwise the root node should agree be the ingroup node specified
    in the NexSON).
  The other properties
  in this object can hold and object with a `nodes` array and an `edges` array
  that correspond to the nodeId and edgeIds of the pruned or suppressed nodes and
  edges. The property name indicates the reason for the pruning. The possible
  property names are:
    * `became_trivial` for internal nodes/edges which have out degree=1 as a result
    of a child/some children being pruned.
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

  * `cleaning_flags.txt` value of the `cleaning_flags` of the config file for
  the pipeline for the last build of the artifacts. These affect the pruning
  of OTT

  * `needs_updating.txt` a list of studies for which the `.tre` file is older than
  the corresponding `../phylo_snapshot/*.json` file.

  * `phylo_inputs_cleaned.txt`
