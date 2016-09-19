# Parent of output defaults to .
PROPINQUITY_OUT_DIR ?= .
export PROPINQUITY_OUT_DIR

# filepath to the run config file
CONFIG_FILENAME=$(PROPINQUITY_OUT_DIR)/config

# The directory holding a shards directory with the collections repo(s)
#   obtained from the union of the ~/.opentree user-wide config and the run config
COLLECTIONS_ROOT := $(shell bin/config_checker.py opentree.collections $(CONFIG_FILENAME))
export COLLECTIONS_ROOT

# Reads the filepath to a clone of the peyotl repo
#   obtained from the union of the ~/.opentree user-wide config and the run config
PEYOTL_ROOT := $(shell bin/config_checker.py opentree.peyotl $(CONFIG_FILENAME))
export PEYOTL_ROOT

# Reads the filepath to the directory that holds a taxonomy in Open Tree Taxonomy interim format
#   obtained from the union of the ~/.opentree user-wide config and the run config
OTT_DIR := $(shell bin/config_checker.py opentree.ott $(CONFIG_FILENAME))
export OTT_DIR

OTT_FILENAMES=about.json \
	conflicts.tsv \
	deprecated.tsv \
	synonyms.tsv \
	taxonomy.tsv \
	version.txt
export OTT_FILENAMES

# Full paths of the relevant files that make up OTT
OTT_FILEPATHS := $(addprefix $(OTT_DIR)/, $(OTT_FILENAMES))
export OTT_FILEPATHS

# The directory holding a shards directory with the phyleystem-# repo(s)
#   obtained from the union of the ~/.opentree user-wide config and the run config
PHYLESYSTEM_ROOT := $(shell bin/config_checker.py opentree.phylesystem $(CONFIG_FILENAME))
export PHYLESYSTEM_ROOT

# The value [synthesis]/collections var which collections (owner/name format) should be
#   used to create the synthesis. The order of these collections determines the ranking
#   obtained from the union of the ~/.opentree user-wide config and the run config
SYNTHESIS_COLLECTIONS := $(shell bin/config_checker.py synthesis.collections $(CONFIG_FILENAME))
export SYNTHESIS_COLLECTIONS


INPUT_PHYLO_ARTIFACTS=$(PROPINQUITY_OUT_DIR)/phylo_input/study_tree_pairs.txt

ARTIFACTS=$(PROPINQUITY_OUT_DIR)/cleaned_ott/cleaned_ott.tre \
	  $(PROPINQUITY_OUT_DIR)/cleaned_phylo/phylo_inputs_cleaned.txt \
	  $(PROPINQUITY_OUT_DIR)/exemplified_phylo/nonempty_trees.txt \
	  $(PROPINQUITY_OUT_DIR)/subproblems/subproblem-ids.txt \
	  $(PROPINQUITY_OUT_DIR)/grafted_solution/grafted_solution_ottnames.tre \
	  $(PROPINQUITY_OUT_DIR)/full_supertree/full_supertree.tre \
	  $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree.tre \
	  $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree_ottnames.tre \
	  $(PROPINQUITY_OUT_DIR)/annotated_supertree/annotations.json

ASSESSMENT_ARTIFACTS = $(PROPINQUITY_OUT_DIR)/assessments/supertree_degree_distribution.txt \
	$(PROPINQUITY_OUT_DIR)/assessments/taxonomy_degree_distribution.txt \
	$(PROPINQUITY_OUT_DIR)/assessments/lost_taxa.txt \
	$(PROPINQUITY_OUT_DIR)/assessments/summary.json

HTML_ARTIFACTS = $(PROPINQUITY_OUT_DIR)/annotated_supertree/index.html \
	$(PROPINQUITY_OUT_DIR)/annotated_supertree/index.json \
	$(PROPINQUITY_OUT_DIR)/assessments/index.html \
	$(PROPINQUITY_OUT_DIR)/cleaned_ott/index.html \
	$(PROPINQUITY_OUT_DIR)/cleaned_ott/index.json \
	$(PROPINQUITY_OUT_DIR)/cleaned_phylo/index.json \
	$(PROPINQUITY_OUT_DIR)/cleaned_phylo/index.html \
	$(PROPINQUITY_OUT_DIR)/exemplified_phylo/index.html \
	$(PROPINQUITY_OUT_DIR)/exemplified_phylo/index.json \
	$(PROPINQUITY_OUT_DIR)/grafted_solution/index.html \
	$(PROPINQUITY_OUT_DIR)/grafted_solution/index.json \
	$(PROPINQUITY_OUT_DIR)/index.html \
	$(PROPINQUITY_OUT_DIR)/index.json \
	$(PROPINQUITY_OUT_DIR)/labelled_supertree/index.html \
	$(PROPINQUITY_OUT_DIR)/labelled_supertree/index.json \
	$(PROPINQUITY_OUT_DIR)/phylo_input/index.json \
	$(PROPINQUITY_OUT_DIR)/phylo_input/index.html \
	$(PROPINQUITY_OUT_DIR)/subproblems/index.html \
	$(PROPINQUITY_OUT_DIR)/subproblems/index.json \
	$(PROPINQUITY_OUT_DIR)/subproblem_solutions/index.html \
	$(PROPINQUITY_OUT_DIR)/subproblem_solutions/index.json \
	$(PROPINQUITY_OUT_DIR)/phylo_snapshot/index.html \
	$(PROPINQUITY_OUT_DIR)/phylo_snapshot/index.json

all: $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree.tre \
	 $(PROPINQUITY_OUT_DIR)/annotated_supertree/annotations.json

extra: $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree_ottnames.tre \
	   $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree_ottnames_without_monotypic.tre \
	   $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree_simplified_ottnames.tre \
	   $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree_simplified_ottnames_without_monotypic.tre \
	   $(PROPINQUITY_OUT_DIR)/grafted_solution/grafted_solution_ottnames.tre

clean: cleanottproducts cleanphyloproducts clean2 cleanpre
	rm -f $(ARTIFACTS)
	rm -f $(INPUT_PHYLO_ARTIFACTS)
	rm -f $(ASSESSMENT_ARTIFACTS)
	rm -f $(HTML_ARTIFACTS)

realclean: clean realcleanottproducts
	# No op

include Makefile.specify_inputs   # contains cleanpre: target
include Makefile.clean_ott   # contains cleanottproducts: target
include Makefile.clean_phylo   # contains cleanphyloproducts: target
include Makefile.subproblems    # contains clean2: target
include Makefile.docs           # contains html: and check: targets
