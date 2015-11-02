# full_supertree
TBA: a tool for using the full taxonomy in [`cleaned_ott/cleaned_ott.tre`](../cleaned_ott/README.md) and
the (sparser) grafted tree in [`grafted_solution`](../grafted_solution/README.md)

This tool should add in the "missing" taxa in the optimal position: if a taxon
    that was pruned maps to a branch in the grafted tree, it should go there. But
    if the branch does not occur in the grafted tree, the taxon should be attached 
    in a polytomy with the MRCA of its sibling taxa.

```sh
otc-unprune-solution ../grafted_solution/grafted_solution.tre ../cleaned_ott/cleaned_ott.tre
```