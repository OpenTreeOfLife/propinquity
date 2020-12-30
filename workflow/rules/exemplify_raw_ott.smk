from propinquity import (bump_or_link,
                         detect_extinct_taxa_to_bump,
                         validate_config,
                         write_if_needed)
from snakemake.logging import logger
from snakemake.utils import min_version
import sys
import os

min_version("5.30.1")

CFG = validate_config(config, logger)

rule all:
    input: "phylo_input/blob_shas.txt"
    log: "logs/snapshot"

rule create_extinct_bump_file:
    input: config = "config", \
           otcconfig = "otc-config", \
           phylo = "exemplified_phylo/args.txt", \
           ott_tree = "cleaned_ott/cleaned_not_updated_ott.tre", \
           phylo_clean = "cleaned_phylo/phylo_inputs_cleaned.txt", \
           ott_flag_json = "cleaned_ott/flagged_in_cleaned.json"
    output: "cleaned_ott/move_extinct_higher_log.json"
    run:
        detect_extinct_taxa_to_bump(ott_tree=input.ott_tree,
                                    phylo_input_fp=input.phylo,
                                    ott_flagged=input.ott_flag_json,
                                    out=output[0],
                                    CFG=CFG)

rule create_cleaned_bump_taxonomy:
    input: config = "config", \
           otcconfig = "otc-config", \
           bump = "cleaned_ott/move_extinct_higher_log.json"
    output: taxonomy = "bumped_ott/taxonomy.tsv", \
            synonyms = "bumped_ott/synonyms.tsv", \
            forwards = "bumped_ott/forwards.tsv", \
            version = "bumped_ott/version.txt"
    run:
        bump_or_link(src_ott_dir=CFG.ott_dir,
                     bump_json_fp=input.bump,
                     out_dir=os.path.split(output.taxonomy)[0],
                     CFG=CFG)

