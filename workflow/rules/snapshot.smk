from propinquity import (export_studies_from_collection,
                         pull_git_subdirs,
                         reaggregate_synth_collections,
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
    input: "phylo_input/blob_shas.txt"
    log: "logs/snapshot"

################################################################################
# sync with GitHub

rule phylesystem_pull:
    """Pulls all phylesystem shards from their origin and writes HEAD shas in output"""
    input: "config"
    log: "logs/phylesystem_pull"
    output: "phylo_snapshot/ps_shard_shas.txt"
    run:
        ps_shards_dir = os.path.join(CFG.phylesystem_dir, "shards")
        shas = pull_git_subdirs(ps_shards_dir, prefix='phylesystem-')
        write_if_needed(fp=output[0],
                        content="\n".join(shas),
                        name="phylesystem shards", CFG=CFG)

rule collections_pull:
    """Pulls all collections shards from their origin and writes HEAD shas in output"""
    input: "config"
    log: "logs/collections_pull"
    output: "phylo_snapshot/collections_shard_shas.txt"
    run:
        coll_shards_dir = os.path.join(CFG.collections_dir, "shards")
        shas = pull_git_subdirs(coll_shards_dir, prefix='collections-')
        write_if_needed(fp=output[0],
                        content="\n".join(shas),
                        name="collections shards", CFG=CFG)

# End sync with GitHub
################################################################################
# snapshot inputs

# create a pattern for the collections to be used in the input of copy_collections
_coll_json_pattern = os.path.join(CFG.collections_dir, "shards", "collections-1", "collections-by-owner", "{syncoll}.json")

rule copy_collections:
    """Copy each collection to the output dir.

    NOTE: assume "coll_dir/shards/collections-1/collections-by-owner/*.json" pattern.
    """
    input: shas="phylo_snapshot/collections_shard_shas.txt", \
           json_fp=expand(_coll_json_pattern, syncoll=CFG.collections.split(','))
    output: "phylo_input/rank_collection.json"
    run:
        reaggregate_synth_collections(input.json_fp, output[0])

rule snapshot_trees_and_collection_items:
    """Concatenate all input collections in order into one "concrete" copy.
    """
    input: "phylo_snapshot/collections_shard_shas.txt", \
           rank_coll="phylo_input/rank_collection.json"
    output: conc_coll="phylo_snapshot/concrete_rank_collection.json"
    run:
        ps_shards_dir = os.path.join(CFG.phylesystem_dir, "shards")
        snap_dir = os.path.join(CFG.out_dir, "phylo_snapshot")
        export_studies_from_collection(ranked_coll_fp=input.rank_coll,
                                       phylesystem_par=ps_shards_dir,
                                       script_managed_trees=CFG.script_managed_trees_dir,
                                       out_par=snap_dir,
                                       concrete_coll_out_fp=output.conc_coll,
                                       CFG=CFG)

rule concrete_tree_list:
    """Extracts the study_tree pairs from the concrete collection.

    Writes that file in a one-per-line format, and writes the git
    object SHAs for each study in the same order.
    """
    input: "phylo_snapshot/concrete_rank_collection.json"
    output: pairs="phylo_input/study_tree_pairs.txt", \
            blob_shas="phylo_input/blob_shas.txt"
    run:
        export_trees_list_and_shas(concrete_coll_json_fp=input[0],
                                   out_fp=output.pairs,
                                   obj_blob_shas_fp=output.blob_shas)
