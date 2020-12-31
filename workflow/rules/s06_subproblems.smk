from propinquity import (decompose_into_subproblems,
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

rule exemplify:
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

