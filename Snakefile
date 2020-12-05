from snakemake.utils import min_version
from snakemake.logging import logger
import sys
import os
min_version("5.30.1")
propinquity_dir = os.path.abspath(config.get("propinquity_dir", os.curdir))
if not os.path.isdir(propinquity_dir):
    sys.exit("propinquity_dir from config {pd} does not an existing directory.\n".format(pd=propinquity_dir))

include: os.path.join(propinquity_dir, "propinq_util.smk")

out_dir = os.path.abspath(os.curdir)
logger.info('Writing output to "{o}"'.format(o=out_dir))

if 'OTC_CONFIG' not in os.environ:
    if not os.path.isfile("otc-config"):
        with open("otc-config", "w") as outp:
            write_otc_config_content(outp)
    else:
        logger.warning("Using existing otc-config file.")
    _ocfp = os.path.join(out_dir, "otc-config")
    os.environ['OTC_CONFIG'] = _ocfp
    logger.warning('Setting OTC_CONFIG environment variable to "{}"'.format(_ocfp))
else:
    _ocfp = os.environ['OTC_CONFIG']
    if not os.path.isfile(_ocfp):
        logger.error("OTC_CONFIG setting {} does not point to a file.".format(_ocfp))
        exit(1)
    logger.warning("Using existing value for OTC_CONFIG environment variable.")
    

if not os.path.isdir("logs"):
    os.makedirs("logs")

if not os.path.isfile("config"):
    with open("config", "w") as outp:
        write_config_content(outp)
else:
    logger.warning("Using existing config file.")



rule all:
    log: "logs/config"
    output: "config"
    shell: "echo hi > {output}"