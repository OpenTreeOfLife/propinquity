from propinquity import (gen_config_content,
                         gen_otc_config_content,
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

def set_tag_to_study_tree_pair(wildcards):
    sp = os.path.join(CFG.out_dir, "phylo_input", "study_tree_pairs.txt")
    if os.path.exists(sp):
        template = "phylo_snapshot/tree_{tag}.json"
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

rule clean_phylo_tre:
    """Clean phylogenetic inputs from snapshot to cleaned_phylo"""
    input: config="config", \
           ott_pruned="cleaned_ott/cleaned_ott_pruned_nonflagged.json", \
           stp="phylo_input/study_tree_pairs.txt", \
           trees=set_tag_to_study_tree_pair
    output: trees="cleaned_phylo/{tag}.tre"
    run:
        od = os.path.join(CFG.out_dir, "cleaned_phylo")
        clean_phylo_input(ott_dir,
                          study_tree_pairs=input.stp,
                          tree_filepaths=input.trees,
                          output_dir=od,
                          cleaning_flags=CFG.cleaning_flags,
                          pruned_from_ott_json_fp=input.ott_pruned,
                          root_ott_id=CFG.root_ott_id)

rule create_exemplify_full_path_args:
    input: pairs="phylo_input/study_tree_pairs.txt", \
           trees=set_tag_to_study_tree_pair
    output: "exemplified_phylo/args.txt"
    run:
        clean_phy = os.path.join(out_dir, "cleaned_phylo", '{tag}.tre')
        tags = [i.strip() for i in open(input.pairs, "r").readlines() if i.strip()]
        paths = [cleaned_phylo.format(tag=i) for i in tags] 
        c = '\n'.join(paths)
        write_if_needed(fp=output[0],
                        content=c,
                        name="cleaned phylo filepaths", CFG=CFG)

