# grafted_solution

Requires that otcetera tools be on your PATH.

Two artifacts:
 * `grafted_solution.tre`: A newick tree file containing a single tree. Labels are ottid. 
 * `grafted_solution_ottnames.tre`: A newick tree file containing a single tree. This is the same tree as `grafted_solution.tre` but more friendly to tree viewers. Monotypic nodes have been removed and Labels are 'ottname ottid'.

All subproblem solutions are read (`subproblem_solutions/ott######-solution.tre`)
and then assembled into a single tree.

Here is some shell code to perform this:

```sh
otc-graft-solutions ../subproblem_solutions/*.tre > grafted_solution.tre
```
Also see documentation for `otc-graft-solution` in otcetera/README.md.
