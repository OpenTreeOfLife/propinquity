from propinquity import (run_unhide_if_worked, 
                         validate_config,
                         write_if_needed)
from snakemake.logging import logger
import sys
import os

CFG = validate_config(config, logger)

rule all:
    input: "grafted_solution/grafted_solution_ottnames.tre"
    log: "logs/subproblems"


# include: "common.smk"
# include: "common.smk"
module common:
    snakefile: "common.smk"
    config: config

use rule * from common as common_*
include: "common_defs.smk"

def _dup_agg_trees_impl(wildcards, soln_dir):
    solve_out = os.path.split(common.checkpoints.decompose.get(**wildcards).output[0])[0]
    gw = glob_wildcards(os.path.join(solve_out, '{ottid}.tre'))
    template = soln_dir + "/{ottid}.tre"
    return expand(template, ottid=gw.ottid)

def dup_aggregate_trees(wildcards):
    return _dup_agg_trees_impl(wildcards, "subproblem_solutions")

def dup_aggregate_rev_trees(wildcards):
    return _dup_agg_trees_impl(wildcards, "reversed_subproblem_solutions")

rule graft_solutions:
    input: dup_aggregate_trees
    output: tree = "grafted_solution/grafted_solution.tre"
    run:
        content = '{}\n'.format('\n'.join(list(input)))
        tfp = "subproblem_solutions/.tmp_paths.txt"
        write_if_needed(fp=tfp, content=content, CFG=CFG)
        invocation = ["otc-graft-solutions", "-f{}".format(tfp)]
        run_unhide_if_worked(invocation,
                             CFG=CFG,
                             stdout_capture=output.tree)
        os.unlink(tfp)


rule relabel_grafted:
    input: config = "config", \
           otcconfig = "otc-config", \
           tree = "grafted_solution/grafted_solution.tre"
    output: "grafted_solution/grafted_solution_ottnames.tre"
    run:
        invocation = ["otc-relabel-tree",
                      input.tree,
                      "--taxonomy={}".format(CFG.ott_dir),
                      '--format-tax=%N ott%I',
                      "--del-monotypic"
                      ]
        run_unhide_if_worked(invocation,
                             CFG=CFG,
                             stdout_capture=output[0])