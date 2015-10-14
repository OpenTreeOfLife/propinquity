# subproblem_solutions
Produced by `otc-solve-subproblem`.
Each subproblem is read separately (`subproblems/ott#######.tre`).

Requires that otcetera tools be on your PATH.

The artifacts are solutions to subproblems in the `subproblems/` directory:

 * `ott#####-solution.tre`: A newick tree file containing a solution to the subproblem
   in `subproblems/ott#####.tre`

Here is some shell code to perform this:

```sh
   for i in ../subproblems/*.tre ; do
       n=$(basename $i)
       id=${n%.tre}
       otc-solve-subproblem $i -n${id} > ${id}-solution.tre
   done
```

Here the `-n` argument specifies the name of the root node.  The correct
name for this node can be extracted from the name of the subproblem file,
as in the script above.
