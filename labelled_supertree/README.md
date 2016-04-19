# labelled_supertree

Requires that otcetera tools be in your PATH.

 * `labelled_supertree.tre`: A newick tree file containing a single tree. Labels are ottid

The `make extra` target builds four other forms of this tree:
 * `labelled_supertree_ottnames.tre`: This is the same tree as `labelled_supertree.tre` but more friendly to tree viewers because labels are of the form 'ottname ottid'.
 * `labelled_supertree_ottnames_without_monotypic.tre`: is like `labelled_supertree_ottnames.tre` but without any taxa that have only one child.
 * `labelled_supertree_simplified_ottnames.tre` and `labelled_supertree_simplified_ottnames_without_monotypic.tre` are
    versions of the previous two trees which also have had names simplified by running `otc-munge-names`. The log
    files for these munging steps will be in  `simplified_ottnames.log` and `simplified_ottnames_without_monotypic.log`respectively.

This tools currently just adds names for unnamed nodes in the tree.
