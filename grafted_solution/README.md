# grafted_solution
Produced by `otc-graft-solutions`.
All subproblem solutions are read (`subproblem_solutions/ott######-solution.tre`)
and then assembled into a single tree.

The only artifact is:
    * `grafted_solution.tre`: A newick tree file containing a single tree

If the sub-problems do not connect into a single component, the program will exit
with error code 1.  It will write multiple trees, where each tree is a connected
component whose root is not found in the other trees.

Requires that otcetera tools be on your PATH.

```sh
otc-graft-solutions ../subproblem_solutions/*.tre > grafted_solution.tre
```

The `-n` argument can be used to name the root if desired:

```sh
otc-graft-solutions ../subproblem_solutions/*tre -nlife > grafted_solution.tre
```
