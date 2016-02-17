# grafted_solution
Produced by `otc-graft-solutions`.
All subproblem solutions are read (`subproblem_solutions/ott######-solution.tre`)
and then assembled into a single tree.

The only artifact is:
 * `grafted_solution.tre`: A newick tree file containing a single tree

Requires that otcetera tools be on your PATH.

Here is some shell code to perform this:

```sh
otc-graft-solutions ../subproblem_solutions/*.tre > grafted_solution.tre
```

Also see documentation for `otc-graft-solution` in otcetera/README.md.