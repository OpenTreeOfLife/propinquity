from propinquity import (OTT_FILENAMES,
                         suppress_by_flag,
                         validate_config,
                         subset_ott,
                         write_if_needed)
from snakemake.logging import logger

CFG = validate_config(config, logger)

rule all:
    input: "cleaned_ott/cleaned_not_updated_ott.tre"
    log: "logs/snapshot"

# End snapshot inputs
################################################################################
# OTT cleaning
rule subset_ott:
    input: "config"
    output: expand("subott_dir/{filename}", filename=OTT_FILENAMES), \
            subott_dir=directory("subott_dir")
    run:
        subset_ott(CFG.ott_dir, output.subott_dir, CFG.root_ott_id, CFG)

rule write_ott_root:
    """Serialize root_ott_id to "cleaned_ott/root_ott_id.txt", if changed."""
    input: "config"
    output: "cleaned_ott/root_ott_id.txt"
    run:
        if not write_if_needed(fp=output[0], content=CFG.root_ott_id, CFG=CFG):
            logger.info("root id has not changed.")

rule write_ott_cleaning_flags:
    """Serialize cleaning_flags to "cleaned_ott/cleaning_flags.txt", if changed."""
    input: "config"
    output: "cleaned_ott/cleaning_flags.txt"
    run:
        if not write_if_needed(fp=output[0], content=CFG.cleaning_flags, CFG=CFG):
            logger.info("cleaning_flags have not changed.")

rule write_ott_version:
    """Copy "$subott_dir/version.txt" to "cleaned_ott/ott_version.txt", if changed."""
    input: "subott_dir/version.txt"
    output: "cleaned_ott/ott_version.txt"
    run:
        ott_version = open(input[0], "r").read().strip() + "\n"
        if not write_if_needed(fp=output[0], content=ott_version, CFG=CFG):
            logger.info("ott version has not changed.")

rule clean_ott_based_on_flags:
    """Writes a pruned version of OTT based on cleaning flags."""
    input: expand("subott_dir/{filename}", filename=OTT_FILENAMES), \
           version="cleaned_ott/ott_version.txt", \
           cleaning_flags="cleaned_ott/cleaning_flags.txt", \
           root="cleaned_ott/root_ott_id.txt"
    output: with_deg_2_tree="cleaned_ott/cleaned_ott_with_hiddenbarren.tre", \
            nonredundant_tree="cleaned_ott/cleaned_not_updated_ott.tre", \
            log="cleaned_ott/cleaned_ott_1.json", \
            prune_log="cleaned_ott/cleaned_ott_pruned_nonflagged.json", \
            flagged="cleaned_ott/flagged_in_cleaned.json"
    run:
        suppress_by_flag(ott_dir="subott_dir",
                         flags=CFG.cleaning_flags,
                         root=CFG.root_ott_id,
                         out_nonredundanttree_fp=output.nonredundant_tree,
                         out_with_deg2_tree_fp=output.with_deg_2_tree,
                         log_fp=output.log,
                         prune_log=output.prune_log,
                         flagged_fp=output.flagged)

