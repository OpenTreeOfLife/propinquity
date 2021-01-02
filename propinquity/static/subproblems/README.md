# subproblems

Requires that otcetera tools be in your PATH.

The artifacts are the subproblems and some related files

 * `ott#####.tre`: A list of newick trees, one per line.  Each tree is part of an input tree, while the last line
   is part of the taxonomy.
 * `ott#####-tree-names.txt`: The names of the trees leading to each line of `ott#####.tre`
 * `ott#####.md5`: MD5 digests for `ott#####.tre` and `ott#####.md5`
 * `subproblem-ids.txt`: The list of subproblem files.
 * `checksummed-subproblem-ids.txt`: ???
 * `contesting-trees.json`: A JSON representation of a summary of
 the contested taxa. The JSON object serialized has keys that correpsond
 to each contested taxon. For the each taxon key there is an object that
 maps the tree file (study@tree id form) to list of the node info for
 the parts of the tree that conflict with the taxon. This node info consists of an object with a "parent" field that identifies the parental
 node, and a list of children of that parent (in a "children_from_taxon"
 attribute) that identifies all of the children of that parent that consist
 only of members of this taxon.  The parents included are nodes that have
 some children that are consist of only members of the taxon and some 
 children that have members that are excluded from the taxon. If the tree 
 did not contest with the taxon, there would only be one such parent.
 Because this file only reports conflicting trees, there should be at least
 2 node info object for each tree.

Produced by `otc-uncontested-decompose`.

`otc-uncontested-decompose` finds taxonomy nodes that are not contested by any input tree.
Each such node with name `ott#####` leads to the creation of a subproblem `ott#####.tre`.

**TODO** documentation of how `otc-uncontested-decompose` fits into the pipeline