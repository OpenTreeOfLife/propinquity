from snakemake.utils import min_version
from snakemake.logging import logger
import subprocess
import sys
import os

min_version("5.30.1")
propinquity_dir = os.path.abspath(config.get("propinquity_dir", os.curdir))
if not os.path.isdir(propinquity_dir):
    sys.exit("propinquity_dir from config {pd} does not an existing directory.\n".format(pd=propinquity_dir))

include: os.path.join(propinquity_dir, "propinq_util.smk")


rule all:
    input:
        ("exemplified_phylo/regraft_cleaned_ott.tre",)
    log: "logs/config"

################################################################################
# configure

rule config:
    """Uses snakemake config to creat a config file for synthesis settings"""
    output: "config"
    log: "logs/config"
    run:
        write_if_needed(fp=output[0], content=gen_config_content())

rule otc_config:
    """Uses snakemake config to creat a config file for otcetera tools"""
    output: "otc-config"
    log: "logs/config"
    run:
        write_if_needed(fp=output[0], content=gen_otc_config_content())

# End configure
################################################################################
# sync with GitHub

rule phylesystem_pull:
    """Pulls all phylesystem shards from their origin and writes HEAD shas in output"""
    input: "config"
    log: "logs/phylesystem_pull"
    output: "phylo_snapshot/ps_shard_shas.txt"
    run:
        ps_shards_dir = os.path.join(phylesystem_dir, "shards")
        shas = pull_git_subdirs(ps_shards_dir, prefix='phylesystem-')
        write_if_needed(fp=output[0],
                        content="\n".join(shas),
                        name="phylesystem shards")

rule collections_pull:
    """Pulls all collections shards from their origin and writes HEAD shas in output"""
    input: "config"
    log: "logs/collections_pull"
    output: "phylo_snapshot/collections_shard_shas.txt"
    run:
        coll_shards_dir = os.path.join(collections_dir, "shards")
        shas = pull_git_subdirs(coll_shards_dir, prefix='collections-')
        write_if_needed(fp=output[0],
                        content="\n".join(shas),
                        name="collections shards")

# End sync with GitHub
################################################################################
# snapshot inputs

# create a pattern for the collections to be used in the input of copy_collections
_coll_json_pattern = os.path.join(collections_dir, "shards", "collections-1", "collections-by-owner", "{syncoll}.json")

rule copy_collections:
    """Copy each collection to the output dir.

    NOTE: assume "coll_dir/shards/collections-1/collections-by-owner/*.json" pattern.
    """
    input: shas="phylo_snapshot/collections_shard_shas.txt", \
           json_fp=expand(_coll_json_pattern, syncoll=collections.split(','))
    output: "phylo_input/rank_collection.json"
    run:
        reaggregate_synth_collections(input.json_fp, output[0])

rule snapshot_trees_and_collection_items:
    """Concatenate all input collections in order into one "concrete" copy.
    """
    input: "phylo_snapshot/collections_shard_shas.txt", \
           rank_coll="phylo_input/rank_collection.json"
    output: conc_coll="phylo_snapshot/concrete_rank_collection-{tag}.json", \
            trees="phylo_snapshot/tree_{tag}.json"
    run:
        ps_shards_dir = os.path.join(phylesystem_dir, "shards")
        snap_dir = os.path.join(out_dir, "phylo_snapshot")
        export_studies_from_collection(ranked_coll_fp=input.rank_coll,
                                       phylesystem_par=ps_shards_dir,
                                       script_managed_trees=script_managed_trees_dir,
                                       out_par=snap_dir)

rule concrete_tree_list:
    """Extracts the study_tree pairs from the concrete collection.

    Writes that file in a one-per-line format, and writes the git
    object SHAs for each study in the same order.
    """
    input: "phylo_snapshot/concrete_rank_collection.json"
    output: pairs="phylo_input/study_tree_pairs.txt",
            blob_shas="phylo_input/blob_shas.txt"
    run:
        export_trees_list_and_shas(concrete_coll_json_fp=input[0],
                                   out_fp=output.pairs,
                                   obj_blob_shas_fp=output.blob_shas)

# End snapshot inputs
################################################################################
# OTT cleaning
OTT_FILENAMES = ("forwards.tsv", 
                 "synonyms.tsv", 
                 "taxonomy.tsv", 
                 "version.txt", 
                 )

rule write_ott_root:
    """Serialize root_ott_id to "cleaned_ott/root_ott_id.txt", if changed."""
    input: "config"
    output: "cleaned_ott/root_ott_id.txt"
    run:
        if not write_if_needed(fp=output[0], content=root_ott_id):
            logger.info("root id has not changed.")

rule write_ott_cleaning_flags:
    """Serialize cleaning_flags to "cleaned_ott/cleaning_flags.txt", if changed."""
    input: "config"
    output: "cleaned_ott/cleaning_flags.txt"
    run:
        if not write_if_needed(fp=output[0], content=cleaning_flags):
            logger.info("cleaning_flags have not changed.")

rule write_ott_version:
    """Copy "${ott_dir}/version.txt" to "cleaned_ott/ott_version.txt", if changed."""
    input: os.path.join(ott_dir, "version.txt")
    output: "cleaned_ott/ott_version.txt"
    run:
        ott_version = open(input[0], "r").read().strip() + "\n"
        if not write_if_needed(fp=output[0], content=ott_version):
            logger.info("ott version has not changed.")

rule clean_ott_based_on_flags:
    """Writes a pruned version of OTT based on cleaning flags."""
    input: expand(ott_dir + "/{filename}", filename=OTT_FILENAMES), \
           version="cleaned_ott/ott_version.txt", \
           cleaning_flags="cleaned_ott/cleaning_flags.txt", \
           root="cleaned_ott/root_ott_id.txt"
    output: with_deg_2_tree="cleaned_ott/cleaned_ott_with_hiddenbarren.tre", \
            nonredundant_tree="cleaned_ott/cleaned_ott.tre", \
            log="cleaned_ott/cleaned_ott_1.json", \
            prune_log="cleaned_ott/cleaned_ott_pruned_nonflagged.json", \
            flagged="cleaned_ott/flagged_in_cleaned.json"
    run:
        suppress_by_flag(ott_dir=ott_dir,
                         flags=cleaning_flags,
                         root=root_ott_id,
                         out_nonredundanttree_fp=output.nonredundant_tree,
                         out_with_deg2_tree_fp=output.with_deg_2_tree,
                         log_fp=output.log,
                         prune_log=output.prune_log,
                         flagged_fp=output.flagged)

rule edit_or_clean_ott:
    input: 
    output: "cleaned_edited_ott/cleaned_not_updated_ott.tre"
    run:
        os.symlink("../cleaned_edited_ott/cleaned_not_updated_ott.tre", output)

# End OTT cleaning
################################################################################
# Phylo cleaning
_st_pairs_fp = os.path.join(out_dir, "phylo_input", "study_tree_pairs.txt")

def write_full_path_for_inputs(x, y, z):
    pass

rule snapshot_phylo:
    input: "phylo_input/study_tree_pairs.txt", "phylo_input/blob_shas.txt"
    output: trees=dynamic("phylo_snapshot/tree_{tag}.json")
    run:
        write_full_path_for_inputs(input[0],
                                   phylesystem_dir,
                                   os.path.join(out_dir, "phylo_snapshot"))


rule clean_phylo_tre:
    """Clean phylogenetic inputs from snapshot to cleaned_phylo"""
    input: trees="phylo_snapshot/tree_{tag}.json", \
           config="config", \
           ott_pruned="cleaned_ott/cleaned_ott_pruned_nonflagged.json", \
           stp="phylo_input/study_tree_pairs.txt"
    output: trees="cleaned_phylo/{tag}.tre"
    run:
        od = os.path.join(out_dir, "cleaned_phylo")
        clean_phylo_input(ott_dir,
                          study_tree_pairs=input.stp,
                          tree_filepaths=input.trees,
                          output_dir=od,
                          cleaning_flags=cleaning_flags,
                          pruned_from_ott_json_fp=input.ott_pruned,
                          root_ott_id=root_ott_id)

rule create_exemplify_full_path_args:
    input: pairs="phylo_input/study_tree_pairs.txt", trees=dynamic("cleaned_phylo/{tag}.tre")
    output: "exemplified_phylo/args.txt"
    run:
        clean_phy = os.path.join(out_dir, "cleaned_phylo", '{tag}.tre')
        tags = [i.strip() for i in open(input.pairs, "r").readlines() if i.strip()]
        paths = [cleaned_phylo.format(tag=i) for i in tags] 
        c = '\n'.join(paths)
        write_if_needed(fp=output[0],
                        content=c,
                        name="cleaned phylo filepaths")

# End Phylo cleaning
################################################################################

rule exemplify:
    input: "otc-config", \
           args="exemplified_phylo/args.txt", \
           cott="cleaned_ott/cleaned_ott.tre"
    output: extaxa="exemplified_phylo/taxonomy.tre", \
            nonempty="exemplified_phylo/nonempty_trees.txt", \
            jsonout="exemplified_phylo/exemplified_log.json"
    shell:
        """otc-nonterminals-to-exemplars \
            -e{out_dir}/exemplified_phylo {input.cott} -f{input.args} \
            -j{output.jsonout} -n{output.nonempty}"""

rule exemplify_for_regraft:
    input: "otc-config", \
           "phylo_snapshot/ps_shard_shas.txt", \
           "phylo_snapshot/collections_shard_shas.txt", \
           config="config", \
           extaxa="exemplified_phylo/taxonomy.tre"
    output: regott="exemplified_phylo/regraft_cleaned_ott.tre", \
            regjson="exemplified_phylo/pruned_for_regraft_cleaned_ott.json"
    shell:
        """otc-regraft-taxonomy-generator \
            --in-tree={input.extaxa} \
            --config={input.config} \
            {ott_dir} \
            --json={output.regjson} \
            >{output.regott}
        """

rule clean_config:
    """Clean up the config and otc-config that are created automatically"""
    shell:
        "rm config otc-config"
