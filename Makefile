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

ARTIFACTS=cleaned_ott/cleaned_ott.tre \
	  cleaned_phylo/phylo_inputs_cleaned.txt \
	  exemplified_phylo/nonempty_trees.txt \
	  subproblems/subproblem-ids.txt \
	  grafted_solution/grafted_solution_ottnames.tre \
	  full_supertree/full_supertree.tre \
	  labelled_supertree/labelled_supertree.tre \
	  labelled_supertree_ottnames/labelled_supertree_ottnames.tre \
	  annotated_supertree/annotations.json

ASSESSMENT_ARTIFACTS = assessments/supertree_degree_distribution.txt \
	assessments/taxonomy_degree_distribution.txt \
	assessments/lost_taxa.txt \
	assessments/summary.json

HTML_ARTIFACTS = annotated_supertree/index.html \
	annotated_supertree/index.json \
	assessments/index.html \
	cleaned_ott/index.html \
	cleaned_ott/index.json \
	cleaned_phylo/index.json \
	cleaned_phylo/index.html \
	exemplified_phylo/index.html \
	exemplified_phylo/index.json \
	grafted_solution/index.html \
	grafted_solution/index.json \
	index.html \
	index.json \
	labelled_supertree/index.html \
	labelled_supertree/index.json \
	phylo_input/index.json \
	phylo_input/index.html \
	subproblems/index.html \
	subproblems/index.json \
	subproblem_solutions/index.html \
	subproblem_solutions/index.json \
	phylo_snapshot/index.html \
	phylo_snapshot/index.json \

all: labelled_supertree/labelled_supertree.tre annotated_supertree/annotations.json

extra: labelled_supertree/labelled_supertree_ottnames.tre grafted_supertree/grafted_supertree_ottnames.tre

clean: clean1 clean2
	rm -f $(ARTIFACTS)
	rm -f $(INPUT_PHYLO_ARTIFACTS)
	rm -f $(ASSESSMENT_ARTIFACTS)
	rm -f $(HTML_ARTIFACTS)

include Makefile.clean_inputs
include Makefile.subproblems


assessments/supertree_degree_distribution.txt: labelled_supertree/labelled_supertree.tre
	otc-degree-distribution labelled_supertree/labelled_supertree.tre > assessments/supertree_degree_distribution.txt

assessments/taxonomy_degree_distribution.txt: cleaned_ott/cleaned_ott.tre
	otc-degree-distribution cleaned_ott/cleaned_ott.tre > assessments/taxonomy_degree_distribution.txt

assessments/lost_taxa.txt: labelled_supertree/labelled_supertree.tre
	otc-taxonomy-parser \
	  $$(./bin/config_checker.py \
	  --config=config \
	  --property=opentree.ott) \
	  --report-lost-taxa \
	  labelled_supertree/labelled_supertree.tre \
	  -c config > assessments/lost_taxa.txt

assessments/summary.json: annotated_supertree/annotations.json \
						  assessments/taxonomy_degree_distribution.txt \
	                      assessments/supertree_degree_distribution.txt \
	                      assessments/lost_taxa.txt
	@rm -f assessments/summary.json 2>/dev/null
	./bin/run_assessments.py . assessments/summary.json 2>&1 | tee assessments/log.txt || true
	@ls assessments/summary.json >/dev/null


check: assessments/summary.json
	@if grep '"ERROR"' assessments/summary.json >/dev/null 2>/dev/null ; \
		then cat assessments/summary.json && echo 'Errors found' && false ; \
		else echo 'OK. Checks passed. A quirky listing of checks is in assessments/summary.json'; \
		fi

$(HTML_ARTIFACTS): assessments/summary.json
	bin/document_outputs.py
	@echo 'Documentation created'

html: assessments/summary.json assessments/index.html
	@echo 'See index.html and linked files for documentation of output'