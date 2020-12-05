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
    input: "phylo_snapshot/ps_shard_shas.txt"
    log: "logs/config"

rule config:
    """Uses snakemake config to creat a config file for synthesis settings"""
    output: "config"
    log: "logs/config"
    run:
        with open(output[0], "w") as outp:
            write_config_content(outp)

rule otc_config:
    """Uses snakemake config to creat a config file for otcetera tools"""
    output: "otc-config"
    log: "logs/config"
    run:
        write_otc_config_file(output[0])

rule phylesystem_pull:
    """Pulls all phylesystem shards from their origin and writes HEAD shas in output"""
    input: "config"
    log: "logs/phylesystem_pull"
    output: "phylo_snapshot/ps_shard_shas.txt"
    run:
        ps_shards_dir = os.path.join(phylesystem_dir, "shards")
        shas = pull_git_subdirs(ps_shards_dir, prefix='phylesystem-')
        if not write_if_needed(output[0], "\n".join(shas)):
            logger.info("phylesystem shards have not changed.")

rule clean_config:
    """Clean up the config and otc-config that are created automatically"""
    shell:
        "rm config otc-config"

