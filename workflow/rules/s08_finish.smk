from propinquity import (analyze_lost_taxa,
                         annotate_1_tree, 
                         annotate_2_tree, 
                         calc_degree_dist, 
                         combine_ott_cleaning_logs,
                         merge_annotations,
                         run_assessments,
                         validate_config)
from snakemake.logging import logger
from snakemake.utils import min_version
import subprocess
import sys
import os

min_version("5.30.1")

CFG = validate_config(config, logger)

rule all:
    input: "subproblems/subproblem-ids.txt"
    log: "logs/unprune"

rule annotate_1:
    input: nonempty = "exemplified_phylo/nonempty_trees.txt", \
           subpr = "subproblems/dumped_subproblem_ids.txt", 
           tree = "labelled_supertree/labelled_supertree.tre"
    output: "annotated_supertree/annotations1.json"
    run:
        in_phylo_fps = []
        with open(input.nonempty, "r") as inp:
            for line in inp:
              if not line.strip():
                  continue
              in_phylo_fps.append(os.path.join("exemplified_phylo", line.strip()))
        annotate_1_tree(input.tree, in_phylo_fps, input.subpr, output[0], CFG=CFG)

rule annotate_2:
    input: tax_dd = "exemplified_phylo/pruned_taxonomy_degree_distribution.txt", \
           annot_1 = "annotated_supertree/annotations1.json"
    output: "annotated_supertree/annotations2.json"
    run: annotate_2_tree(input.annot_1, input.tax_dd, output[0], CFG=CFG)

rule annotate:
    input: annot_1 = "annotated_supertree/annotations1.json", \
           annot_2 = "annotated_supertree/annotations2.json"
    output: "annotated_supertree/annotations.json"
    run: merge_annotations(input.annot_1, input.annot_2, output[0], CFG=CFG)

rule combine_ott_logs:
    input: clean_ott = "cleaned_ott/cleaned_ott_1.json", \
           pruned = "cleaned_ott/cleaned_ott_pruned_nonflagged.json"
    output: "cleaned_ott/cleaned_ott.json"
    run: combine_ott_cleaning_logs(input.clean_ott, input.pruned, output[0], CFG=CFG)

rule tax_deg_dist:
    input: "exemplified_phylo/regraft_cleaned_ott.tre"
    output: "assessments/taxonomy_degree_distribution.txt"
    run: calc_degree_dist(input[0], output[0], CFG=CFG)

rule supertree_deg_dist:
    input: "labelled_supertree/labelled_supertree.tre"
    output: "assessments/supertree_degree_distribution.txt"
    run: calc_degree_dist(input[0], output[0], CFG=CFG)

rule assess_lost_taxa:
    input: tax = "exemplified_phylo/regraft_cleaned_ott.tre", \
           soln = "labelled_supertree/labelled_supertree.tre"
    output: "assessments/lost_taxa.txt"
    run: analyze_lost_taxa(input.tax, input.soln, "bumped_ott", output[0], CFG=CFG)

rule assess:
    input: annot = "annotated_supertree/annotations.json", \
           tax_dd = "assessments/taxonomy_degree_distribution.txt", \
           tree_dd = "assessments/supertree_degree_distribution.txt", \
           lost = "assessments/lost_taxa.txt", \
           clean_ott_tree = "exemplified_phylo/regraft_cleaned_ott.tre", \
           cleaned_ott_json = "cleaned_ott/cleaned_ott.json"
    output: "assessments/summary.json"
    run: run_assessments(CFG=CFG)



rule html:
    input: "assessments/summary.json"
    output: "index.html"
    run: document_outputs(input[0], CFG)

