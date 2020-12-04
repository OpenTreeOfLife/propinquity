from snakemake.utils import min_version
import sys
import os
min_version("5.30.1")
propinquity_dir = os.path.abspath(config.get("propinquity_dir", os.curdir))
if not os.path.isdir(propinquity_dir):
    sys.exit("propinquity_dir from config {pd} does not an existing directory.\n".format(pd=propinquity_dir))
include: os.path.join(propinquity_dir, "propinq_util.snakemake")


if not os.path.isdir("logs"):
    os.makedirs("logs")

if not os.path.isfile("config"):
    with open("config", "w") as outp:
      outp.write("hello\n")

rule all:
    log: "logs/config"
    output: "config"
    shell: "echo hi > {output}"