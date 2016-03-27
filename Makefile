PROPINQUITY_OUT_DIR ?= .
export PROPINQUITY_OUT_DIR
CONFIG_FILENAME=$(PROPINQUITY_OUT_DIR)/config

COLLECTIONS_ROOT := $(shell bin/config_checker.py --config=$(CONFIG_FILENAME) --property=opentree.collections)
export COLLECTIONS_ROOT

PEYOTL_ROOT := $(shell bin/config_checker.py --config=$(CONFIG_FILENAME) --property=opentree.peyotl)
export PEYOTL_ROOT

OTT_DIR := $(shell bin/config_checker.py --config=$(CONFIG_FILENAME) --property=opentree.ott)
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

PHYLESYSTEM_ROOT := $(shell bin/config_checker.py --config=$(CONFIG_FILENAME) --property=opentree.phylesystem)
export PHYLESYSTEM_ROOT

SYNTHESIS_COLLECTIONS := $(shell bin/config_checker.py --config=$(CONFIG_FILENAME) --property=synthesis.collections)
export SYNTHESIS_COLLECTIONS

INPUT_PHYLO_ARTIFACTS=$(PROPINQUITY_OUT_DIR)/phylo_input/studies.txt \
                      $(PROPINQUITY_OUT_DIR)/phylo_input/study_tree_pairs.txt

ARTIFACTS=$(PROPINQUITY_OUT_DIR)/cleaned_ott/cleaned_ott.tre \
	  $(PROPINQUITY_OUT_DIR)/cleaned_phylo/phylo_inputs_cleaned.txt \
	  $(PROPINQUITY_OUT_DIR)/exemplified_phylo/nonempty_trees.txt \
	  $(PROPINQUITY_OUT_DIR)/subproblems/subproblem-ids.txt \
	  $(PROPINQUITY_OUT_DIR)/grafted_solution/grafted_solution_ottnames.tre \
	  $(PROPINQUITY_OUT_DIR)/full_supertree/full_supertree.tre \
	  $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree.tre \
	  $(PROPINQUITY_OUT_DIR)/labelled_supertree_ottnames/labelled_supertree_ottnames.tre \
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
	$(PROPINQUITY_OUT_DIR)/phylo_snapshot/index.json \

all: $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree.tre \
	 $(PROPINQUITY_OUT_DIR)/annotated_supertree/annotations.json

extra: $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree_ottnames.tre \
	   $(PROPINQUITY_OUT_DIR)/grafted_supertree/grafted_supertree_ottnames.tre

clean: clean1 clean2
	rm -f $(ARTIFACTS)
	rm -f $(INPUT_PHYLO_ARTIFACTS)
	rm -f $(ASSESSMENT_ARTIFACTS)
	rm -f $(HTML_ARTIFACTS)

include Makefile.clean_inputs
include Makefile.subproblems


$(PROPINQUITY_OUT_DIR)/assessments/supertree_degree_distribution.txt: $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree.tre
	@if ! test -d $(PROPINQUITY_OUT_DIR)/assessments ; then mkdir -p $(PROPINQUITY_OUT_DIR)/assessments ; fi
	otc-degree-distribution \
		$(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree.tre \
		> $(PROPINQUITY_OUT_DIR)/assessments/supertree_degree_distribution.txt

$(PROPINQUITY_OUT_DIR)/assessments/taxonomy_degree_distribution.txt: $(PROPINQUITY_OUT_DIR)/cleaned_ott/cleaned_ott.tre
	@if ! test -d $(PROPINQUITY_OUT_DIR)/assessments ; then mkdir -p $(PROPINQUITY_OUT_DIR)/assessments ; fi
	otc-degree-distribution $(PROPINQUITY_OUT_DIR)/cleaned_ott/cleaned_ott.tre > $(PROPINQUITY_OUT_DIR)/assessments/taxonomy_degree_distribution.txt

$(PROPINQUITY_OUT_DIR)/assessments/lost_taxa.txt: $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree.tre
	@if ! test -d $(PROPINQUITY_OUT_DIR)/assessments ; then mkdir -p $(PROPINQUITY_OUT_DIR)/assessments ; fi
	otc-taxonomy-parser \
	  $$(./bin/config_checker.py \
	  --config=$(CONFIG_FILENAME) \
	  --property=opentree.ott) \
	  --report-lost-taxa \
	  $(PROPINQUITY_OUT_DIR)/labelled_supertree/labelled_supertree.tre \
	  -c $(CONFIG_FILENAME) > $(PROPINQUITY_OUT_DIR)/assessments/.lost_taxa.txt \
	  || rm $(PROPINQUITY_OUT_DIR)/assessments/.lost_taxa.txt
	mv $(PROPINQUITY_OUT_DIR)/assessments/.lost_taxa.txt $(PROPINQUITY_OUT_DIR)/assessments/lost_taxa.txt

$(PROPINQUITY_OUT_DIR)/assessments/summary.json: $(PROPINQUITY_OUT_DIR)/annotated_supertree/annotations.json \
						  $(PROPINQUITY_OUT_DIR)/assessments/taxonomy_degree_distribution.txt \
	                      $(PROPINQUITY_OUT_DIR)/assessments/supertree_degree_distribution.txt \
	                      $(PROPINQUITY_OUT_DIR)/assessments/lost_taxa.txt
	@if ! test -d $(PROPINQUITY_OUT_DIR)/assessments ; then mkdir -p $(PROPINQUITY_OUT_DIR)/assessments ; fi
	@rm -f $(PROPINQUITY_OUT_DIR)/assessments/summary.json 2>/dev/null
	./bin/run_assessments.py $(PROPINQUITY_OUT_DIR) $(PROPINQUITY_OUT_DIR)/assessments/summary.json 2>&1 | tee $(PROPINQUITY_OUT_DIR)/assessments/log.txt || true
	@ls $(PROPINQUITY_OUT_DIR)/assessments/summary.json >/dev/null


check: $(PROPINQUITY_OUT_DIR)/assessments/summary.json
	@if grep '"ERROR"' $(PROPINQUITY_OUT_DIR)/assessments/summary.json >/dev/null 2>/dev/null ; \
		then cat $(PROPINQUITY_OUT_DIR)/assessments/summary.json && echo 'Errors found' && false ; \
		else echo "OK. Checks passed. A quirky listing of checks is in $(PROPINQUITY_OUT_DIR)/assessments/summary.json"; \
		fi

$(HTML_ARTIFACTS): $(PROPINQUITY_OUT_DIR)/assessments/summary.json \
				   $(PROPINQUITY_OUT_DIR)/phylo_snapshot/collections_git_shas.txt
	bin/document_outputs.py --config=$(CONFIG_FILENAME) $(PROPINQUITY_OUT_DIR)
	@echo 'Documentation created'

html: $(PROPINQUITY_OUT_DIR)/assessments/summary.json $(PROPINQUITY_OUT_DIR)/assessments/index.html
	@echo "See $(PROPINQUITY_OUT_DIR)/index.html and linked files for documentation of output"