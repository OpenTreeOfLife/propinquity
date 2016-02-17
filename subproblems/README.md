# subproblems

Requires that otcetera tools be in your PATH.

The artifacts are the subproblems and some related files

 * `ott#####.tre`: A list of newick trees, one per line.  Each tree is part of an input tree, while the last line
   is part of the taxonomy.
 * `ott#####-tree-names.txt`: The names of the trees leading to each line of `ott#####.tre`
 * `ott#####.md5`: MD5 digests for `ott#####.tre` and `ott#####.md5`
 * `subproblem-ids.txt`: The list of subproblem files.
 * `checksummed-subproblem-ids.txt`: ???

Produced by `otc-uncontested-decompose`.

`otc-uncontested-decompose` finds taxonomy nodes that are not contested by any input tree.
Each such node with name `ott#####` leads to the creation of a subproblem `ott#####.tre`.

**TODO** documentation of how `otc-uncontested-decompose` fits into the pipeline