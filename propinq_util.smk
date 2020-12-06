import sys
import os

### Validating config
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
    collections = config["collections"]
    cleaning_flags = config["cleaning_flags"]
    additional_regrafting_flags = config.get("additional_regrafting_flags", "")
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

def write_otc_config_content(outstream):
    outstream.write("""
[opentree]
phylesystem = {ph}
peyotl = {pe}
ott = {o}
collections = {c}
script-managed-trees = {s}
""".format(ph=phylesystem_dir, pe=peyotl_dir,
           o=ott_dir, c=collections_dir,
           s=script_managed_trees_dir))

def write_otc_config_file(fp):
    with open(fp, "w") as outp:
        write_otc_config_content(outp)

def write_config_content(outstream):
    outstream.write("""
[taxonomy]
cleaning_flags = {cf}
additional_regrafting_flags = {arf}

[synthesis]
collections = {c}
root_ott_id = {r}
synth_id = {s}
""".format(cf=cleaning_flags,
           arf=additional_regrafting_flags,
           c=collections,
           r=root_ott_id,
           s=synth_id))

def pull_git_subdirs(par_dir, prefix):
    """Git pull on every dir matching `par_dir`/`prefix`-*

    returns the SHA of the HEAD of every matching dir
    (in order determined by string sort of subdir names).
    """
    shas = []
    subl = list(os.listdir(par_dir))
    subl.sort()
    for fn in subl:
        if fn.startswith(prefix):
            wd = os.path.join(par_dir, fn)
            subprocess.run(["git", "pull", "origin", "--no-commit"],
                           cwd=wd,
                           check=True)
            x = subprocess.check_output(['git','rev-parse', 'HEAD'],
                                        cwd=wd).decode('utf-8')
            shas.append(x)
    return shas

def write_if_needed(fp, content):
    """Writes `content` to `fp` if the content of that filepath is empty or different.

    Returns True if a write was done, False if the file already had that content.
    """
    if os.path.exists(fp):
        prev_content = open(output[0], "r").read()
        if prev_content == content:
            return False
    with open(fp, "w") as outp:
        outp.write(content)


def verify_taxon_edits_not_needed(json_fp, unclean_ott, out_ott):
    with codecs.open(json_fp, mode='r', encoding='utf-8') as jinp:
        jout = json.load(jinp)
    if "edits" in jout:
        sys.exit('''Taxonomic changes need to be made in your version of OTT to move extinct taxa higher in the taxonomy!

Use:
    {}/bin/patch_taxonomy_by_bumping.py [PATH TO YOUR OTT DIR] {} [OUTPUT PATH FOR A PATCHED OTT DIR]
to create a modified version of OTT, then set that to be your OTT path for propinquity and rerun.

'''.format(os.path.abspath(os.curdir), os.path.abspath(jfp)))
if len(sys.argv) > 2:
    try:
        from shutil import copyfile
        copyfile(sys.argv[2], sys.argv[3])
    except:
        sys.stderr.write(usage)
        raise
