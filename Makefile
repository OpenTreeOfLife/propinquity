INPUT_PHYLO_ARTIFACTS=phylo_input/studies.txt \
	 phylo_input/study_tree_pairs.txt

ARTIFACTS= cleaned_ott/cleaned_ott.tre \
	      cleaned_phylo/phylo_inputs_cleaned.txt \
	      exemplified_phylo/nonempty_trees.txt \
	      subproblems/subproblem-ids.txt \
	      full_supertree/full_supertree.tre \
	      labelled_supertree/labelled_supertree.tre \
	      annotated_supertree/annotations.json

all: $(ARTIFACTS)


# phylo_input holds the lists of study+tree pairs to be used during the supertree construction
phylo_input/fresh_synth_collection.json: 
	cd phylo_input ; \
	rm -f \
	   fungi.json \
	   metazoa.json \
	   plants.json \
	   safe-microbes.json \
	   fresh_synth_collection.json ; \
	../bin/reaggregate-synth-collections.sh fresh_synth_collection.json

phylo_input/studies.txt: phylo_input/rank_collection.json

phylo_input/rank_collection.json:
	@echo "You must create the input file phylo_input/rank_collection.json "
	@echo "  which holds the collection of trees that are used in synthesis."
	@echo "If you do not have a collection that you want to use as an input you can run:"
	@echo
	@echo '   make phylo_input/fresh_synth_collection.json'
	@echo '   cp phylo_input/fresh_synth_collection.json phylo_input/rank_collection.json'
	@echo
	@false

phylo_input/study_tree_pairs.txt: phylo_input/rank_collection.json
	$(PEYOTL_ROOT)/scripts/collection_export.py --export=studyID_treeID phylo_input/rank_collection.json >phylo_input/study_tree_pairs.txt

clean:
	rm -f $(ARTIFACTS)
	rm -f $(INPUT_PHYLO_ARTIFACTS)
	make -fMakefile.clean_inputs clean
	make -fMakefile.subproblems clean

exemplified_phylo/nonempty_trees.txt:
	make -fMakefile.clean_inputs exemplified_phylo/nonempty_trees.txt

subproblems/subproblem-ids.txt:
	make -fMakefile.subproblems subproblems/subproblem-ids.txt

cleaned_phylo/phylo_inputs_cleaned.txt:
	make -fMakefile.clean_inputs cleaned_phylo/phylo_inputs_cleaned.txt

cleaned_ott/cleaned_ott.tre:
	make -fMakefile.clean_inputs cleaned_ott/cleaned_ott.tre

full_supertree/full_supertree.tre:
	make -f Makefile.subproblems full_supertree/full_supertree.tre

labelled_supertree/labelled_supertree.tre:
	make -f Makefile.subproblems labelled_supertree/labelled_supertree.tre

annotated_supertree/annotations.json:
	make -f Makefile.subproblems annotated_supertree/annotations.json
