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
    input: "subproblem_solutions/solution-degree-distributions.txt"
    log: "logs/subproblems"




rule calc_dd:
    input: otcconfig = "otc-config", \
           soln = "subproblem_solutions/{ottid}.tre"
    output: sol_dd = "subproblem_solutions/deg-dist-{ottid}.txt"
    run:
        calc_degree_dist(input.soln, output.sol_dd, CFG=CFG)

def aggregate_sdd(wildcards):
    solve_out = os.path.split(checkpoints.solved_ids.get(**wildcards).output[0])[0]
    solve_out = directory("subproblem_solutions")
    gw = glob_wildcards(os.path.join(solve_out, '{ottid}.tre'))
    return expand("subproblem_solutions/deg-dist-{ottid}.txt", ottid=gw.ottid)

rule concat_soln_deg_dist:
    input: aggregate_sdd
    output: "subproblem_solutions/solution-degree-distributions.txt"
    run:
        filepaths = list(input)
        filepaths.sort()
        lines = []
        ott_id_from_fp = re.compile(r".*deg-dist-ott([-0-9A-Za-z]+)\.txt")
        for fp in filepaths:
            with open(fp, "r") as inp:
                m = ott_id_from_fp.match(fp)
                if not m:
                    continue
                ott_id = m.group(1)
                lines.append("ott{}.tre".format(ott_id))
                lines.extend([i[:-1] for i in inp.readlines() if i])
        content = '\n'.join(lines)
        write_if_needed(fp=output[0], content=content, CFG=CFG)
