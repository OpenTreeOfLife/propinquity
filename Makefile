# Parent of output defaults to .
PROPINQUITY_OUT_DIR ?= .
export PROPINQUITY_OUT_DIR

# filepath to the run config file
CONFIG_FILENAME=$(PROPINQUITY_OUT_DIR)/config

# The directory holding a shards directory with the collections repo(s)
#   Obtained from the union of the user-wide config and the run config
COLLECTIONS_ROOT := $(shell bin/config_checker.py opentree.collections $(CONFIG_FILENAME))
export COLLECTIONS_ROOT

# Reads the filepath to a clone of the peyotl repo
#   Obtained from the union of the user-wide config and the run config
PEYOTL_ROOT := $(shell bin/config_checker.py opentree.peyotl $(CONFIG_FILENAME))
export PEYOTL_ROOT

# Reads the filepath to the directory that holds a taxonomy in Open Tree Taxonomy interim format
#   obtained from the union of the user-wide config and the run config
OTT_DIR := $(shell bin/config_checker.py opentree.ott $(CONFIG_FILENAME))
export OTT_DIR

# The value [opentree]/script-managed-trees specifies the location of the script-managed-trees
# repo.  This repo contains trees newick trees that have ottids in their tip labels.
# We could convert these trees to nexson, and import them directly, but we do not.
SCRIPT_MANAGED_TREES := $(shell bin/config_checker.py opentree.script-managed-trees $(CONFIG_FILENAME))
export SCRIPT_MANAGED_TREES

# This list of files for each OTT release are used below to create the
#	full paths to the OTT inputs
OTT_FILENAMES=forwards.tsv \
	synonyms.tsv \
	taxonomy.tsv \
	version.txt

# Full paths of the relevant files that make up OTT
OTT_FILEPATHS := $(addprefix $(OTT_DIR)/, $(OTT_FILENAMES))
export OTT_FILEPATHS

# The directory holding a shards directory with the phyleystem-# repo(s)
#   obtained from the union of the user-wide config and the run config
PHYLESYSTEM_ROOT := $(shell bin/config_checker.py opentree.phylesystem $(CONFIG_FILENAME))
export PHYLESYSTEM_ROOT

# The [synthesis]/collections var specifies WHICH collections (format: owner/name) should be
#   used to create the synthesis. The order of these collections determines the ranking.
#   Obtained from the union of the run config and the user-wide config.
SYNTHESIS_COLLECTIONS := $(shell bin/config_checker.py synthesis.collections $(CONFIG_FILENAME))
export SYNTHESIS_COLLECTIONS

ASSESSMENT_ARTIFACTS = $(PROPINQUITY_OUT_DIR)/assessments/supertree_degree_distribution.txt \
	$(PROPINQUITY_OUT_DIR)/assessments/taxonomy_degree_distribution.txt \
	$(PROPINQUITY_OUT_DIR)/assessments/lost_taxa.txt \
	$(PROPINQUITY_OUT_DIR)/assessments/summary.json \
	$(PROPINQUITY_OUT_DIR)/assessments/log.txt


all: $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree.tre \
	 $(PROPINQUITY_OUT_DIR)/annotated_supertree/annotations.json

extra: $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree_ottnames.tre \
	   $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree_ottnames_without_monotypic.tre \
	   $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree_simplified_ottnames.tre \
	   $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree_simplified_ottnames_without_monotypic.tre \
	   $(PROPINQUITY_OUT_DIR)/grafted_solution/grafted_solution_ottnames.tre

clean: cleanpre \
	   cleanottproducts \
	   cleanphyloproducts \
	   cleansubproblems \
	   cleanfinal \
	   cleandoc
	rm -f $(ASSESSMENT_ARTIFACTS)

	rmdir $(PROPINQUITY_OUT_DIR)/phylo_input || true
	rmdir $(PROPINQUITY_OUT_DIR)/phylo_snapshot || true
	rmdir $(PROPINQUITY_OUT_DIR)/cleaned_ott || true
	rmdir $(PROPINQUITY_OUT_DIR)/cleaned_phylo || true
	rmdir $(PROPINQUITY_OUT_DIR)/exemplified_phylo || true
	rmdir $(PROPINQUITY_OUT_DIR)/subproblems/scratch || true
	rmdir $(PROPINQUITY_OUT_DIR)/subproblems || true
	rmdir $(PROPINQUITY_OUT_DIR)/subproblem_solutions || true
	rmdir $(PROPINQUITY_OUT_DIR)/grafted_solution || true
	rmdir $(PROPINQUITY_OUT_DIR)/labelled_supertree || true
	rmdir $(PROPINQUITY_OUT_DIR)/annotated_supertree || true
	rmdir $(PROPINQUITY_OUT_DIR)/logs || true
	# if test -d $(PROPINQUITY_OUT_DIR)/phylo_input ; then rmdir --ignore-fail-on-non-empty $(PROPINQUITY_OUT_DIR)/phylo_input ; fi
	# if test -d $(PROPINQUITY_OUT_DIR)/phylo_snapshot ; then rmdir --ignore-fail-on-non-empty $(PROPINQUITY_OUT_DIR)/phylo_snapshot ; fi
	# if test -d $(PROPINQUITY_OUT_DIR)/cleaned_ott ; then rmdir --ignore-fail-on-non-empty $(PROPINQUITY_OUT_DIR)/cleaned_ott ; fi
	# if test -d $(PROPINQUITY_OUT_DIR)/cleaned_phylo ; then rmdir --ignore-fail-on-non-empty $(PROPINQUITY_OUT_DIR)/cleaned_phylo ; fi
	# if test -d $(PROPINQUITY_OUT_DIR)/exemplified_phylo ; then rmdir --ignore-fail-on-non-empty $(PROPINQUITY_OUT_DIR)/exemplified_phylo ; fi
	# if test -d $(PROPINQUITY_OUT_DIR)/subproblems/scratch ; then rmdir --ignore-fail-on-non-empty $(PROPINQUITY_OUT_DIR)/subproblems/scratch ; fi
	# if test -d $(PROPINQUITY_OUT_DIR)/subproblems ; then rmdir --ignore-fail-on-non-empty $(PROPINQUITY_OUT_DIR)/subproblems ; fi
	# if test -d $(PROPINQUITY_OUT_DIR)/subproblem_solutions ; then rmdir --ignore-fail-on-non-empty $(PROPINQUITY_OUT_DIR)/subproblem_solutions ; fi
	# if test -d $(PROPINQUITY_OUT_DIR)/grafted_solution ; then rmdir --ignore-fail-on-non-empty $(PROPINQUITY_OUT_DIR)/grafted_solution ; fi
	# if test -d $(PROPINQUITY_OUT_DIR)/labelled_supertree ; then rmdir --ignore-fail-on-non-empty $(PROPINQUITY_OUT_DIR)/labelled_supertree ; fi
	# if test -d $(PROPINQUITY_OUT_DIR)/annotated_supertree ; then rmdir --ignore-fail-on-non-empty $(PROPINQUITY_OUT_DIR)/annotated_supertree ; fi
	# if test -d $(PROPINQUITY_OUT_DIR)/assessments ; then rmdir --ignore-fail-on-non-empty $(PROPINQUITY_OUT_DIR)/assessments ; fi
	# if test -d $(PROPINQUITY_OUT_DIR)/logs ; then rmdir --ignore-fail-on-non-empty $(PROPINQUITY_OUT_DIR)/logs ; fi

realclean: realcleanottproducts clean
	# No op

include Makefile.specify_inputs   # contains cleanpre target
include Makefile.clean_ott   # contains cleanottproducts target
include Makefile.clean_phylo   # contains cleanphyloproducts target
include Makefile.subproblems    # contains cleansubproblems target
include Makefile.regraft_and_label    # contains cleanfinal target
include Makefile.docs           # contains html and check targets
