# exemplified_phylo
Produced by `otc-nonterminals-to-exemplars`
Reads the cleaned taxonomy (`cleaned_ott/cleaned_ott.tre`) and
cleaned phylogenetic inputs (`cleaned_phylo/*.tre`).
For tips of phylogenies that are mapped to higher taxa, 
    this tool picks terminal taxa with which to exemplify those clades.
Then the induced tree from the taxonomic input is produced.

The goal of this step is to remove tips that represent higher taxa and
produce smaller inputs for the subproblem identification.

The choice of which taxa are used to exemplify a higher taxon is made
    to fulfill the following requirements:

  1. the exemplars are always terminal taxa in OTT,

  2. If a descendant terminal taxon is used in any other tree, then
        that taxon will be in the set of examplars for all of its higher
        taxa. Note that "used in" means either:

    1. mapped to a taxon of a tip, OR

    2. chosen to exemplify a higher taxon that is mapped to a tip

  3. if a higher taxon is mapped to a tip, but no other input tree
    uses any descendant taxon, then the one exemplar is chosen
    arbitrarily (currently this chose relies on the branch rotation
    of the incoming newick - so clients should NOT rely on the
    same exemplar being chosen in every run in which semantically
    identical inputs are given).



Requires that otcetera tools be on your PATH.

**TODO** need to double check the behavior of `otc-nonterminals-to-exemplars`
to make sure that this documentation is correct.

  * `args.txt` a list of the cleaned phylogenetic inputs. Used as an argument
  to `otc-nonterminals-to-exemplars`.
  * `taxonomy.tre` the induced tree from of the taxonomy.
  * `pg_*.tre` and `ot_*.tre` - versions of the cleaned_phylo inputs with higher taxa exemplified.