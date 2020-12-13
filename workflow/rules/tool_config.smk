from propinquity import (gen_config_content,
                         gen_otc_config_content,
                         validate_config,
                         write_if_needed)
from snakemake.utils import min_version
from snakemake.logging import logger
import subprocess
import sys
import os


CFG = validate_config(config, logger)


rule all:
    input: "config", "otc_config"
    log: "logs/config"


rule config:
    """Uses snakemake config to creat a config file for synthesis settings"""
    output: "config"
    log: "logs/config"
    run:
        write_if_needed(fp=output[0], content=gen_config_content(CFG))

rule otc_config:
    """Uses snakemake config to creat a config file for otcetera tools"""
    output: "otc-config"
    log: "logs/config"
    run:
        write_if_needed(fp=output[0], content=gen_otc_config_content(CFG))


rule clean_config:
    """Clean up the config and otc-config that are created automatically"""
    shell: "rm config otc-config"

