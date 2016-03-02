COLLECTIONS_ROOT := $(shell bin/config_checker.py --config=config --property=opentree.collections)
export COLLECTIONS_ROOT

PEYOTL_ROOT := $(shell bin/config_checker.py --config=config --property=opentree.peyotl)
export PEYOTL_ROOT

OTT_DIR := $(shell bin/config_checker.py --config=config --property=opentree.ott)
export OTT_DIR

OTT_FILENAMES=about.json \
	conflicts.tsv \
	deprecated.tsv \
	synonyms.tsv \
	taxonomy.tsv \
	version.txt
export OTT_FILENAMES

OTT_FILEPATHS := $(addprefix $(OTT_DIR)/, $(OTT_FILENAMES))
export OTT_FILEPATHS

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
	      grafted_solution/grafted_solution_ottnames.tre \
	      full_supertree/full_supertree.tre \
	      labelled_supertree/labelled_supertree.tre \
	      labelled_supertree_ottnames/labelled_supertree_ottnames.tre \
	      annotated_supertree/annotations.json

all: labelled_supertree/labelled_supertree.tre annotated_supertree/annotations.json

extra: labelled_supertree/labelled_supertree_ottnames.tre grafted_supertree/grafted_supertree_ottnames.tre


# phylo_input holds the lists of study+tree pairs to be used during the supertree construction
#phylo_input/collections.txt: config
#	bin/config_checker.py --config=config --property=synthesis.collections > phylo_input/.raw_collections.txt
#	if ! diff phylo_input/collections.txt phylo_input/.raw_collections.txt 2>/dev/null ; then mv phylo_input/.raw_collections.txt phylo_input/collections.txt ; else rm phylo_input/.raw_collections.txt ; fi

#phylo_input/rank_collection.json: phylo_input/collections.txt
#	cd phylo_input ; \
#	../bin/reaggregate-synth-collections.sh .raw_rank_collection.json
#	if ! diff phylo_input/rank_collection.json phylo_input/.raw_rank_collection.json 2>/dev/null ; then mv phylo_input/.raw_rank_collection.json phylo_input/rank_collection.json ; else rm phylo_input/.raw_rank_collection.json ; fi

phylo_input/studies.txt: phylo_input/rank_collection.json

clean: clean1 clean2
	rm -f $(ARTIFACTS)
	rm -f $(INPUT_PHYLO_ARTIFACTS)

include Makefile.clean_inputs
include Makefile.subproblems
