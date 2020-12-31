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
    input: "exemplified_phylo/nonempty_trees.txt"
    log: "logs/snapshot"

rule exemplify:
    input: config = "config", \
           otcconfig = "otc-config", \
           phylo_fp = "exemplified_phylo/args.txt", \
           taxo = "bumped_ott/cleaned_ott.tre"
    output: nonempty = "exemplified_phylo/nonempty_trees.txt", \
            exlog = "exemplified_phylo/exemplified_log.json"
    run:
        ep_dir = os.path.split(output.nonempty)[0]
        invocation = ["otc-nonterminals-to-exemplars",
                      "-e{}".format(ep_dir),
                      input.taxo,
                      "-f{}".format(input.phylo_fp),
                      "-j{}".format(output.exlog),
                      "-n{}.hide".format(output.nonempty)
                      ]
        rp = subprocess.run(invocation)
        rp.check_returncode()
        cp_if_needed(src="{}.hide".format(output.nonempty),
                     dest=output.nonempty,
                     CFG=CFG)
