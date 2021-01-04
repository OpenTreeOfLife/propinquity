from propinquity import (calc_degree_dist,
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
    input: "grafted_solution/grafted_solution_ottnames.tre"
    log: "logs/subproblems"


rule graft_solutions:
    input: aggregate_trees
    output: tree = "grafted_solution/grafted_solution.tre"
    run:
        content = '\n'.join(list(input))
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