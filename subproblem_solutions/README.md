# subproblem_solutions
Produced by `otc-solve-subproblem`.
Each subproblem is read separately (`subproblems/ott#######.tre`).

Requires that otcetera tools be on your PATH.

Each subproblem in `subproblems/` is solved, the solution written to a
corresponding file:

```sh
   for i in ../subproblems/* ; do
       n=$(basename $i)
       id=${n%.tre}
       otc-solve-subproblem $i -n${id} > ${id}-solution.tre
   done
```

Here the `-n` argument specifies the name of the root node.  The name
of this node is extracted from the name of the subproblem file.
