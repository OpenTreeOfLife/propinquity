FIGURES = Figures__cleaned_ott__cleaned_ott.tre.pdf \
          Figures__cleaned_phylo__ex_2@tree1.tre.pdf \
          Figures__cleaned_phylo__ex_2@tree2.tre.pdf \
          Figures__exemplified_phylo__ex_2@tree1.tre.pdf \
          Figures__exemplified_phylo__ex_2@tree2.tre.pdf \
          Figures__exemplified_phylo_taxonomy_uncontested.tre.pdf \
          Figures__grafted_solution__grafted_solution_ottnames.tre.pdf \
          Figures__labelled_supertree__labelled_supertree_only_taxon_names.tre.pdf \
          Figures__subproblems__14__1.tre.pdf \
          Figures__subproblems__14__2.tre.pdf \
          Figures__subproblems__14__3.tre.pdf \
          Figures__subproblems__17__1.tre.pdf \
          Figures__subproblems__17__2.tre.pdf \
          Figures__subproblems__17__3.tre.pdf \
          Figures__subproblem_solutions__ott14.tre.pdf \
          Figures__subproblem_solutions__ott17.tre.pdf \
          Figures__toy_ambig__abcd.pdf \
          Figures__toy_ambig__bcde.pdf \
          Figures__toy_ambig__soln1.pdf \
          Figures__toy_ambig__soln2.pdf \
          Figures__toy_pairwise_compat__abc.pdf \
          Figures__toy_pairwise_compat__acd.pdf \
          Figures__toy_pairwise_compat__bcd.pdf \
          Figures__toy_pairwise_compat__s12.pdf \
          Figures__toy_pairwise_compat__s13.pdf \
          Figures__toy_pairwise_compat__s23.pdf \
          Figures__uncontested_worsens_score__ab1c.pdf \
          Figures__uncontested_worsens_score__acb2.pdf \
          Figures__uncontested_worsens_score__opt.pdf \
          Figures__uncontested_worsens_score__returned.pdf \
          Figures__uncontested_worsens_score__tax.pdf


all: figures paper5.pdf

figures:
	bash ./copy_figures.sh


paper5.pdf: paper5.tex $(FIGURES)
	pdflatex paper5.tex
	bibtex paper5
	pdflatex paper5.tex
	pdflatex paper5.tex
