# exemplified_phylo
Produced by `otc-nonterminals-to-exemplars`
Reads the cleaned taxonomy (`cleaned_ott/cleaned_ott.tre`) and
cleaned phylogenetic inputs (`cleaned_phylo/*.tre`).
For tips of phylogenies that are mapped to higher taxa, 
    this tool picks terminal taxa with which to exemplify those clades.
Then the induced tree from the taxonomic input is produced.

The goal of this step is to remove tips that represent higher taxa and
produce smaller inputs for the subproblem identification.

Requires that otcetera tools be on your PATH.

**TODO** need to double check the behavior of `otc-nonterminals-to-exemplars`
to make sure that this documentation is correct.

  * `args.txt` a list of the cleaned phylogenetic inputs. Used as an argument
  to `otc-nonterminals-to-exemplars`.
  * `taxonomy.tre` the induced tree from of the taxonomy.
  * `pg_*.tre` and `ot_*.tre` - versions of the cleaned_phylo inputs with higher taxa exemplified.