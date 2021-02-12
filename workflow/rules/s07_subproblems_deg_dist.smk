from propinquity import (validate_config,
                         write_if_needed)
from snakemake.logging import logger
import os

CFG = validate_config(config, logger)

rule all:
    input: "subproblem_solutions/solution-degree-distributions.txt"
    log: "logs/subproblems"

include: "common.smk"

rule force_all_subr_dd:
    input: aggregate_probdd
    output: "subproblems/.all_deg_dist_calculated.txt"
    run:
        c = "{}\n".format('\n'.join([str(i) for i in input]))
        write_if_needed(fp=output[0], content=c, CFG=CFG)

def concatenate_deg_dist(filepaths, out_fp):
    filepaths = list(filepaths)
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
    write_if_needed(fp=out_fp, content=content, CFG=CFG)

rule concat_soln_deg_dist:
    input: aggregate_sdd
    output: "subproblem_solutions/solution-degree-distributions.txt"
    run: concatenate_deg_dist(input, output[0])


rule concat_rev_soln_deg_dist:
    input: aggregate_rsdd
    output: "reversed_subproblem_solutions/solution-degree-distributions.txt"
    run: concatenate_deg_dist(input, output[0])
