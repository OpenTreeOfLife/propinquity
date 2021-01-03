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

checkpoint decompose:
    input: config = "config", \
           otcconfig = "otc-config", \
           phylo_list_fp = "subproblems/scratch/args.txt", \
           taxonomy = "exemplified_phylo/taxonomy.tre"
    output: subprob_id = "subproblems/dumped_subproblem_ids.txt", \
            contesting = "subproblems/contesting_trees.json"
    run:
        decompose_into_subproblems(tax_tree_fp=input.taxonomy,
                                   phylo_list_fp=input.phylo_list_fp,
                                   out_dir=os.path.split(output.subprob_id)[0],
                                   out_subprob_id_fp=output.subprob_id,
                                   out_contesting=output.contesting,
                                   CFG=CFG)


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

def aggregate_trees(wildcards):
    solve_out = os.path.split(checkpoints.decompose.get(**wildcards).output[0])[0]
    gw = glob_wildcards(os.path.join(solve_out, '{ottid}.tre'))
    return expand("subproblem_solutions/{ottid}.tre", ottid=gw.ottid)

checkpoint solved_ids:
    input: aggregate_trees
    output: "subproblem_solutions/solution-ids.txt"
    run:
        tags = [os.path.split(i)[-1] for i in input]
        # print("input=", tags)
        content = '\n'.join(tags)
        write_if_needed(fp=output[0], content=content, CFG=CFG)


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
                    msg = "Expected filepath to match deg-dist-ott####.txt found {}"
                    raise RuntimeError(msg.format(fp))
                ott_id = m.group(1)
                lines.append("ott{}.tre".format(ott_id))
                lines.extend([i[:-1] for i in inp.readlines() if i])
        content = '\n'.join(lines)
        write_if_needed(fp=output[0], content=content, CFG=CFG)

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

