from propinquity import (exemplify_taxa, validate_config)
from snakemake.logging import logger
from snakemake.utils import min_version
import subprocess
import sys
import os

min_version("5.30.1")

CFG = validate_config(config, logger)

rule all:
    input: "exemplified_phylo/nonempty_trees.txt"
    log: "logs/snapshot"

rule exemplify:
    input: config = "config", \
           otcconfig = "otc-config", \
           phylo_fp = "exemplified_phylo/args.txt", \
           taxo = "bumped_ott/cleaned_ott.tre"
    output: nonempty = "exemplified_phylo/nonempty_trees.txt", \
            exlog = "exemplified_phylo/exemplified_log.json",
            taxonomy = "exemplified_phylo/taxonomy.tre"
    run:
        exemplify_taxa(in_tax_tree_fp=input.taxo,
                       in_phylo_fp=input.phylo_fp,
                       out_nonempty_tree_fp=output.nonempty,
                       out_log_fp=output.exlog,
                       CFG=CFG)