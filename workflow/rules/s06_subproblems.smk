from propinquity import (calc_degree_dist,
                         decompose_into_subproblems,
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
    input: "subproblem_solutions/solution-ids.txt"
    log: "logs/subproblems"

rule expand_path_to_nonempty_phylo:
    input: config = "config", \
           phylo_list_fp = "exemplified_phylo/nonempty_trees.txt"
    output: "subproblems/scratch/args.txt"
    run:
        ph_li_fp = input.phylo_list_fp
        fn = [i.strip() for i in open(ph_li_fp, "r") if i.strip()]
        ap = os.path.abspath(os.path.split(ph_li_fp)[0])
        fp = [os.path.join(ap, i) for i in fn]
        fp.append('') # for the newline at the end of the file
        fpc = '\n'.join(fp)
        write_if_needed(fp=output[0],
                        content=fpc,
                        name="nonempty tree fullpaths",
                        CFG=CFG)

include: "common.smk"


rule solve:
    input: config = "config", \
           otcconfig = "otc-config", \
           subprob_id = "subproblems/dumped_subproblem_ids.txt", \
           incert = "exemplified_phylo/incertae_sedis.txt", \
           subprob = "subproblems/{ottid}.tre"
    output: soln = "subproblem_solutions/{ottid}.tre" #, sol_dd = "subproblem_solutions/deg-dist-{ottid}.txt"
    run:
        solve_subproblem(incert_sed_fp=input.incert,
                         subprob_fp=input.subprob,
                         out_fp=output.soln,
                         CFG=CFG)

