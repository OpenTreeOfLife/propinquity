from propinquity import (analyze_lost_taxa,
                         annotate_1_tree, 
                         annotate_2_tree, 
                         calc_degree_dist, 
                         combine_ott_cleaning_logs,
                         create_indented_tip_count,
                         document_outputs,
                         format_subprob_size_json_as_tsv,
                         generate_subprob_size_summary,
                         get_template_text,
                         indented_taxon_count_to_json_for_ott,
                         merge_annotations,
                         run_assessments,
                         TEMPLATE_FNS, 
                         validate_config,
                         write_if_needed)
from snakemake.logging import logger
import os
import re

CFG = validate_config(config, logger)

rule all:
    input: "subproblems/dumped_subproblem_ids.txt"
    log: "logs/unprune"

rule templates:
    output: expand("logs/templates/{pt_file}", pt_file=TEMPLATE_FNS)
    run:
        for ptf in TEMPLATE_FNS:
            write_if_needed(fp="logs/templates/{}".format(ptf),
                            content = get_template_text(ptf),
                            CFG=CFG)

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

rule create_indented_tip_count:
    input: "labelled_supertree/labelled_supertree_simplified_ottnames.tre"
    output: "labelled_supertree/labelled-tree-tip-count-indented-table.txt"
    run: create_indented_tip_count(input[0], output[0], CFG=CFG)

rule calc_tips_for_ott_internals:
    input: "labelled_supertree/labelled-tree-tip-count-indented-table.txt"
    output: "labelled_supertree/num_tips_for_ott_internals_in_labelled_tree.json"
    run: indented_taxon_count_to_json_for_ott(input[0], output[0], CFG=CFG)

rule html:
    input: expand("logs/templates/{pt_file}", pt_file=TEMPLATE_FNS), \
           summ = "assessments/summary.json", \
           contesting = "subproblems/contesting_trees.json", \
           sub_id = "subproblems/dumped_subproblem_ids.txt", \
           num_tips_per_ott = "labelled_supertree/num_tips_for_ott_internals_in_labelled_tree.json"
    output: top = "index.html", \
            subproblems_ind_j = "subproblems/index.json" 
    run: document_outputs(input[0], CFG=CFG)

rule summarize_subpr_size:
    input: ind = "subproblems/index.json", \
           dd_flag = "subproblems/.all_deg_dist_calculated.txt", \
           num_tips_per_ott = "labelled_supertree/num_tips_for_ott_internals_in_labelled_tree.json", \
           dd_dir = "subproblems/deg-dist"
    output: "subproblems/subproblem_size_summary.json"
    run:
        generate_subprob_size_summary(input.ind,
                                      input.num_tips_per_ott,
                                      input.dd_dir,
                                      output[0],
                                      CFG=CFG)

rule format_subpr_size_as_table:
    input: "subproblems/subproblem_size_summary.json"
    output: "subproblems/subproblem_size_summary_table.tsv"
    run:
        format_subprob_size_json_as_tsv(input[0], output[0], CFG=CFG)
