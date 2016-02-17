# grafted_solution

Requires that otcetera tools be on your PATH.

The only artifact is:
 * `grafted_solution.tre`: A newick tree file containing a single tree

All subproblem solutions are read (`subproblem_solutions/ott######-solution.tre`)
and then assembled into a single tree.

Here is some shell code to perform this:

```sh
otc-graft-solutions ../subproblem_solutions/*.tre > grafted_solution.tre
```
Also see documentation for `otc-graft-solution` in otcetera/README.md.