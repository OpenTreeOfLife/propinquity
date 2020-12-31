from propinquity import (bump_or_link,
                         cp_if_needed,
                         cp_or_suppress_by_flag, 
                         detect_extinct_taxa_to_bump,
                         OTT_FILENAMES,
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
    input: "bumped_ott/cleaned_ott.tre"
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
           bump = "cleaned_ott/move_extinct_higher_log.json", \
           taxonomy = "subott_dir/taxonomy.tsv", \
           synonyms = "subott_dir/synonyms.tsv", \
           forwards = "subott_dir/forwards.tsv", \
           version = "subott_dir/version.txt", \
           ott_version = "subott_dir/version.txt"
    output: taxonomy = "bumped_ott/taxonomy.tsv", \
            synonyms = "bumped_ott/synonyms.tsv", \
            forwards = "bumped_ott/forwards.tsv", \
            version = "bumped_ott/version.txt", \
            ott_version = "bumped_ott/ott_version.txt"
    run:
        bump_or_link(src_ott_dir="subott_dir",
                     bump_json_fp=input.bump,
                     out_dir=os.path.split(output.taxonomy)[0],
                     CFG=CFG)

rule clean_bumped_ott_based_on_flags:
    """Writes a pruned version of the bumped verstion OTT based on cleaning flags."""
    input: expand("bumped_ott/{filename}", filename=OTT_FILENAMES), \
           bump = "cleaned_ott/move_extinct_higher_log.json", \
           version="bumped_ott/ott_version.txt", \
           cleaning_flags="cleaned_ott/cleaning_flags.txt", \
           root="cleaned_ott/root_ott_id.txt", \
           with_deg_2_tree="cleaned_ott/cleaned_ott_with_hiddenbarren.tre", \
           nonredundant_tree="cleaned_ott/cleaned_not_updated_ott.tre", \
           log="cleaned_ott/cleaned_ott_1.json", \
           prune_log="cleaned_ott/cleaned_ott_pruned_nonflagged.json", \
           flagged="cleaned_ott/flagged_in_cleaned.json"
    output: with_deg_2_tree="bumped_ott/cleaned_ott_with_hiddenbarren.tre", \
            nonredundant_tree="bumped_ott/cleaned_not_updated_ott.tre", \
            log="bumped_ott/cleaned_ott_1.json", \
            prune_log="bumped_ott/cleaned_ott_pruned_nonflagged.json", \
            flagged="bumped_ott/flagged_in_cleaned.json"
    run:
        bump_ott_dir = os.path.split(output.flagged)[0]
        cp_or_suppress_by_flag(ott_dir=bump_ott_dir,
                               flags=CFG.cleaning_flags,
                               root=CFG.root_ott_id,
                               bump_json_fp=input.bump,
                               in_nonredundanttree_fp=input.nonredundant_tree,
                               in_with_deg2_tree_fp=input.with_deg_2_tree,
                               in_log_fp=input.log,
                               in_prune_log=input.prune_log,
                               in_flagged_fp=input.flagged,
                               out_nonredundanttree_fp=output.nonredundant_tree,
                               out_with_deg2_tree_fp=output.with_deg_2_tree,
                               out_log_fp=output.log,
                               out_prune_log=output.prune_log,
                               out_flagged_fp=output.flagged,
                               CFG=CFG)

rule link_bumped_clean_ott_tree:
    input: "bumped_ott/cleaned_not_updated_ott.tre"
    output: "bumped_ott/cleaned_ott.tre"
    run: os.symlink(os.path.split(input[0])[1], output[0])
