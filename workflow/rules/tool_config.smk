from snakemake.utils import min_version
from snakemake.logging import logger
import subprocess
import sys
import os

min_version("5.30.1")

print(config)

propinquity_dir = os.path.abspath(config.get("propinquity_dir", os.curdir))
if not os.path.isdir(propinquity_dir):
    sys.exit("propinquity_dir from config {pd} does not an existing directory.\n".format(pd=propinquity_dir))

################################################################################
# Validatng config and setting global variables:
# Executed on startup.
# Defines the following globals based on config,
#   lists as a comma-separated string:
#       additional_regrafting_flags (e.g. "extinct_inherited,extinct")
#       cleaning_flags (e.g "major_rank_conflict,barren")
#       collections (e.g. "kcranston/catfish,kcranston/barnacles")
#   Paths to directories
#       collections_dir - parent of shards
#       ott_dir
#       out_dir - set by the --directory arg to snakemake
#       peyotl_dir
#       phylesystem_dir - parent of shards
#       script_managed_trees_dir
#   Run-specific IDs:
#       root_ott_id
#       synth_id
#
# Validation also sets environmental variables:
#   OTC_CONFIG and OTCETERA_LOGFILE


_config_dirs = ("collections_dir",
                "ott_dir",
                "peyotl_dir", 
                "phylesystem_dir",
                "script_managed_trees_dir",
                )

try:
    for _ds in _config_dirs:
        _v = config[_ds]
        locals()[_ds] = _v
        if not os.path.isdir(_v):
            sys.exit('{p} "{v}"" does not exist.\n'.format(p=_ds, v=_v))
    collections = canon_sep_string(config["collections"], sort=False)
    cleaning_flags = canon_sep_string(config["cleaning_flags"])
    additional_regrafting_flags = canon_sep_string(config.get("additional_regrafting_flags", ""))
    root_ott_id = config["root_ott_id"]
    synth_id = config["synth_id"]
except KeyError as x:
    exit(expand("Missing config variable {x}", x=str(x))[0])

if not os.path.isdir(os.path.join(phylesystem_dir, "shards", "phylesystem-1")):
    sys.exit(expand('phylesystem_dir {phylesystem_dir} is expeceted to have "shards/phylesystem-1" subdirectory.\n'))
if not os.path.isdir(os.path.join(collections_dir, "shards", "collections-1")):
    sys.exit(expand('collections_dir {collections_dir} is expeceted to have "shards/collections-1" subdirectory.\n'))


out_dir = os.path.abspath(os.curdir)
logger.info('Writing output to "{o}"'.format(o=out_dir))

if 'OTC_CONFIG' not in os.environ:
    _ocfp = os.path.join(out_dir, "otc-config")
    os.environ['OTC_CONFIG'] = _ocfp
    logger.debug('Setting OTC_CONFIG environment variable to "{}"'.format(_ocfp))


if 'OTCETERA_LOGFILE' not in os.environ:
    os.environ['OTCETERA_LOGFILE'] = os.path.join(out_dir, "logs", "myeasylog.log")
else:
    _ocfp = os.environ['OTCETERA_LOGFILE']
    logger.warning("Using existing value for OTCETERA_LOGFILE {}.".format(_ocfp))

# end config validation and global setting
################################################################################


rule all:
    input: "config", "otc_config"
    log: "logs/config"


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


rule clean_config:
    """Clean up the config and otc-config that are created automatically"""
    shell: "rm config otc-config"

