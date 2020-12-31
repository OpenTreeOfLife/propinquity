from propinquity import (exemplify_taxa, validate_config, write_inc_sed_ids)
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

rule write_inc_sed:
    input: config = "config", \
           otcconfig = "otc-config", \
           tax_tree = "exemplified_phylo/taxonomy.tre",
           taxonomy = "bumped_ott/taxonomy.tsv", \
           synonyms = "bumped_ott/synonyms.tsv", \
           forwards = "bumped_ott/forwards.tsv", \
           version = "bumped_ott/version.txt", \
           ott_version = "bumped_ott/ott_version.txt"
    output: "exemplified_phylo/incertae_sedis.txt"
    run:
        mod_ott_dir = os.path.split(input.taxonomy)[0]
        write_inc_sed_ids(tax_tree=input.tax_tree,
                          ott_dir=mod_ott_dir,
                          config_fp=input.config,
                          out_inc_sed_id_fp=output[0],
                          CFG=CFG)

