from propinquity import (clean_contesting_tree_refs,
                         decompose_into_subproblems,
                         stripped_nonempty_lines,
                         validate_config,
                         write_if_needed)
from snakemake.logging import logger
import os

CFG = validate_config(config, logger)
include: "common_defs.smk"

checkpoint decompose:
    """Also makes subproblems/{ottid}-tree-names.txt."""
    input: config = "config", \
           otcconfig = "otc-config", \
           phylo_list_fp = "subproblems/scratch/args.txt", \
           taxonomy = "exemplified_phylo/taxonomy.tre"
    output: subprob_id = "subproblems/dumped_subproblem_ids.txt", \
            contesting = "subproblems/raw_contesting_trees.json", \
            subprob_link = "subproblems/subproblem-ids.txt"
    run:
        decompose_into_subproblems(tax_tree_fp=input.taxonomy,
                                   phylo_list_fp=input.phylo_list_fp,
                                   out_dir=os.path.split(output.subprob_id)[0],
                                   out_subprob_id_fp=output.subprob_id,
                                   out_contesting=output.contesting,
                                   CFG=CFG)
        if not os.path.exists(output.subprob_link):
            os.symlink("./" + os.path.split(output.subprob_id)[-1], output.subprob_link)

checkpoint cleancontest:
    input: config = "config", \
           otcconfig = "otc-config", \
           raw = "subproblems/raw_contesting_trees.json"
    output: contesting = "subproblems/contesting_trees.json", \
            contest_link = "subproblems/contesting-trees.json"
    run:
        clean_contesting_tree_refs(input.raw, output.contesting, CFG=CFG)
        if not os.path.exists(output.contest_link):
            os.symlink("./" + os.path.split(output.contesting)[-1], output.contest_link)

rule solved_ids:
    input: aggregate_trees
    output: "subproblem_solutions/solution-ids.txt"
    run:
        content = '\n'.join([os.path.split(i)[-1] for i in input])
        write_if_needed(fp=output[0], content=content, CFG=CFG)

rule rev_solved_ids:
    input: aggregate_rev_trees
    output: "reversed_subproblem_solutions/solution-ids.txt"
    run:
        content = '\n'.join([os.path.split(i)[-1] for i in input])
        write_if_needed(fp=output[0], content=content, CFG=CFG)

checkpoint reverse_subproblems_flag:
    input: config = "config", \
           otcconfig = "otc-config", \
           subprob_id = "subproblems/dumped_subproblem_ids.txt"
    output: "reversed_subproblems/flag.txt"
    run: write_if_needed(content="", fp=output[0])

rule reverse_subproblems:
    input: config = "config", \
           otcconfig = "otc-config", \
           subprob_id = "subproblems/dumped_subproblem_ids.txt", \
           subprob = "subproblems/{ottid}.tre", \
           flag = "reversed_subproblems/flag.txt"
    output: subprob="reversed_subproblems/{ottid}.tre"
    run:
        # gen_reversed.py gist
        nl = list(stripped_nonempty_lines(input.subprob))
        if nl:
            if len(nl) > 1:
                nl, last = nl[:-1], nl[-1]
                nl.reverse()
                nl.append(last)
        write_if_needed(fp=output.subprob, content="\n".join(nl))
