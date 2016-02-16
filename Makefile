COLLECTIONS_ROOT := $(shell bin/config_checker.py --config=config --property=opentree.collections)
export COLLECTIONS_ROOT

PEYOTL_ROOT := $(shell bin/config_checker.py --config=config --property=opentree.peyotl)
export PEYOTL_ROOT

OTT_DIR := $(shell bin/config_checker.py --config=config --property=opentree.ott)
export OTT_DIR

PHYLESYSTEM_ROOT := $(shell bin/config_checker.py --config=config --property=opentree.phylesystem)
export PHYLESYSTEM_ROOT 

SYNTHESIS_COLLECTIONS := $(shell bin/config_checker.py --config=config --property=synthesis.collections)
export SYNTHESIS_COLLECTIONS

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
phylo_input/collections.txt: config
	bin/config_checker.py --config=config --property=synthesis.collections > phylo_input/.raw_collections.txt
	if ! diff phylo_input/collections.txt phylo_input/.raw_collections.txt 2>/dev/null ; then mv phylo_input/.raw_collections.txt phylo_input/collections.txt ; else rm phylo_input/.raw_collections.txt ; fi

phylo_input/rank_collection.json: phylo_input/collections.txt
	cd phylo_input ; \
	../bin/reaggregate-synth-collections.sh .raw_rank_collection.json
	if ! diff phylo_input/rank_collection.json phylo_input/.raw_rank_collection.json 2>/dev/null ; then mv phylo_input/.raw_rank_collection.json phylo_input/rank_collection.json ; else rm phylo_input/.raw_rank_collection.json ; fi

phylo_input/studies.txt: phylo_input/rank_collection.json

#phylo_input/rank_collection.json:
#	@echo "You must create the input file phylo_input/rank_collection.json "
#	@echo "  which holds the collection of trees that are used in synthesis."
#	@echo "If you do not have a collection that you want to use as an input you can run:"
#	@echo
#	@echo '   make phylo_input/fresh_synth_collection.json'
#	@echo '   cp phylo_input/fresh_synth_collection.json phylo_input/rank_collection.json'
#	@echo
#	@false

phylo_input/study_tree_pairs.txt: phylo_input/rank_collection.json
	$(PEYOTL_ROOT)/scripts/collection_export.py --export=studyID_treeID phylo_input/rank_collection.json >phylo_input/study_tree_pairs.txt

clean:
	rm -f $(ARTIFACTS)
	rm -f $(INPUT_PHYLO_ARTIFACTS)
	make -fMakefile.clean_inputs clean
	make -fMakefile.subproblems clean

exemplified_phylo/nonempty_trees.txt: phylo_input/study_tree_pairs.txt phylo_input/rank_collection.json
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
