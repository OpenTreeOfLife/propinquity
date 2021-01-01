from propinquity import (decompose_into_subproblems,
                         OTT_FILENAMES,
                         run_unhide_if_worked, 
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
        hstdout = output.tree + ".hide"
        hjson = output.json + ".hide"
        invocation = ["otc-regraft-taxonomy-generator",
                      "--in-tree={}".format(input.tax),
                      "--config={}".format(input.config),
                      directory("bumped_ott"),
                      "--json={}".format(hjson),]
        unhide = [(hstdout, output.tree), (hjson, output.json)]
        run_unhide_if_worked(invocation,
                             unhide,
                             CFG=CFG,
                             stdout_capture=hstdout)

rule terse_labelled_tree:
    input: config = "config", \
           otcconfig = "otc-config", \
           grafted = "grafted_solution/grafted_solution.tre", \
           tax_tree = "exemplified_phylo/regraft_cleaned_ott.tre"
    output: "full_supertree/full_supertree.tre"
    run:
        hstdout = output[0] + ".hide"
        invocation = ["otc-unprune-solution",
                      input.grafted, 
                      input.tax_tree]
        run_unhide_if_worked(invocation,
                             [(hstdout, output[0])],
                             CFG=CFG,
                             stdout_capture=hstdout)
