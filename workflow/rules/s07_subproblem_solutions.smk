from propinquity import (solve_subproblem, validate_config)
from snakemake.logging import logger
from snakemake.utils import min_version
import subprocess
import sys
import os

min_version("5.30.1")

CFG = validate_config(config, logger)

rule all:
    input: "subproblems/subproblem-ids.txt"
    log: "logs/subproblems"

rule solve:
    input: config = "config", \
           otcconfig = "otc-config", \
           subprob_id = "subproblems/dumped_subproblem_ids.txt", \
           incert = "exemplified_phylo/incertae_sedis.txt", \
           subprob = "subproblems/{ottid}.tre"
    output: soln = "subproblem_solutions/{ottid}.tre"
    run:
        solve_subproblem(incert_sed_fp=input.incert,
                         subprob_fp=input.subprob,
                         out_fp=output.soln,
                         CFG=CFG)

rule solved_ids:
    input: dynamic("subproblem_solutions/{ottid}.tre")
    output: "subproblem_solutions/solution-ids.txt"
    run:
        print(input)