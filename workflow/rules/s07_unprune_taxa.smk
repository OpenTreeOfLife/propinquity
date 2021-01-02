from propinquity import (annotate_1_tree, 
                         annotate_2_tree, 
                         calc_degree_dist, 
                         decompose_into_subproblems,
                         merge_annotations,
                         OTT_FILENAMES,
                         relabel_tree, 
                         run_unhide_if_worked,
                         simplify_tax_names,
                         solve_subproblem,
                         validate_config,
                         write_if_needed)
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

rule ott_for_regraft:
    input: expand("bumped_ott/{filename}", filename=OTT_FILENAMES), \
           tax = "exemplified_phylo/taxonomy.tre", \
           config = "config"
    output: tree = "exemplified_phylo/regraft_cleaned_ott.tre", \
            json = "exemplified_phylo/pruned_for_regraft_cleaned_ott.json"
    run:
        hjson = output.json + ".hide"
        invocation = ["otc-regraft-taxonomy-generator",
                      "--in-tree={}".format(input.tax),
                      "--config={}".format(input.config),
                      directory("bumped_ott"),
                      "--json={}".format(hjson),]
        run_unhide_if_worked(invocation,
                             [(hjson, output.json)],
                             CFG=CFG,
                             stdout_capture=output.tree)

rule terse_labelled_tree:
    input: config = "config", \
           otcconfig = "otc-config", \
           grafted = "grafted_solution/grafted_solution.tre", \
           tax_tree = "exemplified_phylo/regraft_cleaned_ott.tre"
    output: "full_supertree/full_supertree.tre"
    run:
        invocation = ["otc-unprune-solution",
                      input.grafted, 
                      input.tax_tree, ]
        run_unhide_if_worked(invocation, CFG=CFG, stdout_capture=output[0])

rule full_labelled_tree:
    input: config = "config", \
           otcconfig = "otc-config", \
           grafted = "grafted_solution/grafted_solution.tre", \
           tax_tree = "exemplified_phylo/regraft_cleaned_ott.tre", \
           inc_sed = "exemplified_phylo/incertae_sedis.txt"
    output: tree = "labelled_supertree/labelled_supertree.tre", \
            broken = "labelled_supertree/broken_taxa.json", \
            io_stats = "labelled_supertree/input_output_stats.json"
    run:
        bth = output.broken + ".hide"
        ios = output.io_stats + ".hide"
        invocation = ["otc-unprune-solution-and-name-unnamed-nodes",
                      input.grafted, 
                      input.tax_tree,
                      "-i{}".format(input.inc_sed),
                      "-j{}".format(bth),
                      "-s{}".format(ios), ]
        run_unhide_if_worked(invocation,
                             [(bth, output.broken), (ios, output.io_stats)], 
                             CFG=CFG,
                             stdout_capture=output.tree)

rule full_deg_dist:
    input: "labelled_supertree/labelled_supertree.tre"
    output: "labelled_supertree/labelled_supertree_out_degree_distribution.txt"
    run: calc_degree_dist(input[0], output[0], CFG=CFG)

rule relabel_full_tree:
    input: expand("bumped_ott/{filename}", filename=OTT_FILENAMES), \
           tree = "labelled_supertree/labelled_supertree.tre"
    output: tree = "labelled_supertree/labelled_supertree_ottnames.tre"
    run:
        relabel_tree(input.tree, directory("bumped_ott"),
                     output.tree, del_monotypic=False, CFG=CFG)

rule simplify_full_tree_labels:
    input: "labelled_supertree/labelled_supertree_ottnames.tre"
    output: tree = "labelled_supertree/labelled_supertree_simplified_ottnames.tre", \
            log = "labelled_supertree/simplified_ottnames.log"
    run: simplify_tax_names(input[0], output.tree, output.log, CFG=CFG)

rule remove_monotypic:
    input: expand("bumped_ott/{filename}", filename=OTT_FILENAMES), \
           tree = "labelled_supertree/labelled_supertree.tre"
    output: tree = "labelled_supertree/labelled_supertree_ottnames_without_monotypic.tre"
    run:
        relabel_tree(input.tree, "bumped_ott",
                     output.tree, del_monotypic=True, CFG=CFG)
        
rule simplify_sans_monotypic_labels:
    input: "labelled_supertree/labelled_supertree_ottnames_without_monotypic.tre"
    output: tree = "labelled_supertree/labelled_supertree_simplified_ottnames_without_monotypic.tre", \
            log = "labelled_supertree/simplified_ottnames_without_monotypic.log"
    run: simplify_tax_names(input[0], output.tree, output.log, CFG=CFG)


rule pruned_tax_dd:
    input: "exemplified_phylo/taxonomy.tre"
    output: "exemplified_phylo/pruned_taxonomy_degree_distribution.txt"
    run: calc_degree_dist(input[0], output[0], CFG=CFG)

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

