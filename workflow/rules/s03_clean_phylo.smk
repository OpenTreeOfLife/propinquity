from propinquity import (clean_phylo_input,
                         gen_config_content,
                         gen_otc_config_content,
                         force_or_touch_file,
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

_st_pairs_fp = os.path.join(CFG.out_dir, "phylo_input", "study_tree_pairs.txt")

def write_full_path_for_inputs(x, y, z):
    pass

# rule snapshot_phylo:
#     input: "phylo_input/study_tree_pairs.txt", "phylo_input/blob_shas.txt"
#     output: trees=dynamic("phylo_snapshot/tree_{tag}.json")
#     run:
#         write_full_path_for_inputs(input[0],
#                                    phylesystem_dir,
#                                    os.path.join(out_dir, "phylo_snapshot"))

def set_tag_to_study_tree_pair(wildcards, snapshot=True):
    sp = os.path.join(CFG.out_dir, "phylo_input", "study_tree_pairs.txt")
    if os.path.exists(sp):
        if snapshot:
            template = "phylo_snapshot/tree_{tag}.json"
        else:
            template = "cleaned_phylo/tree_{tag}.tre"
        paths = []
        with open(sp, "r") as inp:
            for line in inp:
                ls = line.strip()
                if not ls:
                    continue
                paths.append(template.format(tag=ls))
        return paths
    CFG.error(sp + "does not exist!")
    raise RuntimeError(sp + "does not exist!")

def set_tag_to_cleaned_study_tree_pair(wildcards):
    return set_tag_to_study_tree_pair(wildcards, snapshot=False)

rule clean_phylo_tre:
    """Clean phylogenetic inputs from snapshot to cleaned_phylo"""
    input: config="config", \
           ott_pruned="cleaned_ott/cleaned_ott_pruned_nonflagged.json", \
           stp="phylo_input/study_tree_pairs.txt"
    output: signal="cleaned_phylo/phylo_inputs_cleaned.txt", \
            nonempty_out_fp="exemplified_phylo/args.txt"
    run:
        od = os.path.join(CFG.out_dir, "cleaned_phylo")
        trees = set_tag_to_study_tree_pair(None)
        c = clean_phylo_input(ott_dir=directory("subott_dir"),
                              study_tree_pairs=input.stp,
                              tree_filepaths=trees,
                              output_dir=od,
                              cleaning_flags=CFG.cleaning_flags,
                              pruned_from_ott_json_fp=input.ott_pruned,
                              root_ott_id=CFG.root_ott_id,
                              script_managed_dir=CFG.script_managed_trees_dir,
                              nonempty_out_fp=output.nonempty_out_fp,
                              CFG=CFG)
        force_or_touch_file(output.signal, c)


# rule create_exemplify_full_path_args:
#     input: pairs="phylo_input/study_tree_pairs.txt", \
#            signal="cleaned_phylo/phylo_inputs_cleaned.txt"
#     output: 
#     run:
#         clean_phy = os.path.join(CFG.out_dir, "cleaned_phylo", 'tree_{tag}.tre')
#         tags = [i.strip() for i in open(input.pairs, "r").readlines() if i.strip()]
#         paths = [clean_phy.format(tag=i) for i in tags] 
#         c = '\n'.join(paths)
#         write_if_needed(fp=output[0],
#                         content=c,
#                         name="cleaned phylo filepaths", CFG=CFG)

