# full_supertree

Requires that otcetera tools be in your PATH.

The only artifact is:
 * `full_supertree.tre`: A newick tree file containing a single tree

This tool adds in the "missing" taxa in the optimal position: if a taxon
    that was pruned maps to a branch in the grafted tree, it should go there. But
    if the branch does not occur in the grafted tree, the taxon should be attached 
    in a polytomy with the MRCA of its sibling taxa.

```sh
otc-unprune-solution ../grafted_solution/grafted_solution.tre ../cleaned_ott/cleaned_ott.tre > full_supertree/full_supertree.tre
```