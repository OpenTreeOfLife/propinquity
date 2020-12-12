import sys
import os
import codecs
import json


################################################################################
# simple helper functions

def canon_sep_string(v, sep=",", sort=True):
    """Return a canonical form of a delimited string.

    Strips whitespace from sep-separated string, (optionally)
    sorts the list, and then returns the delimited form.
    """
    vl = [i.strip() for i in v.split(sep) if i.strip()]
    if sort:
        vl.sort()
    return sep.join(vl)

################################################################################
# @TODO: from peyutil import read_as_json, write_as_json

def read_as_json(in_filename, encoding='utf-8'):
    with codecs.open(in_filename, 'r', encoding=encoding) as inpf:
        return json.load(inpf)


def write_as_json(blob, dest, indent=0, sort_keys=True):
    """Writes `blob` as JSON to the filepath or outstream `dest`.

    If `dest` is a string, it is assumed to be object with .write().
    Uses utf-8 encoding if the filepath is given (does *not* change
    the encoding if dest is already open).
    """
    opened_out = False
    if is_str_type(dest):
        out = codecs.open(dest, mode='w', encoding='utf-8')
        opened_out = True
    else:
        out = dest
    try:
        json.dump(blob, out, indent=indent, sort_keys=sort_keys)
        out.write('\n')
    finally:
        out.flush()
        if opened_out:
            out.close()

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
# helper functions

def write_if_needed(fp, content, name=None):
    """Writes `content` to `fp` if the content of that filepath is empty or different.

    Returns True if a write was done, False if the file already had that content.
    if `name` is not None, and the filepath has not changed, then
        a logger.info "{name} has not changed" message will be emitted.
    """
    if os.path.exists(fp):
        prev_content = open(output[0], "r").read()
        if prev_content == content:
            if name is not None:
                logger.info("{n} has not changed".format(n=name))
            return False
    with open(fp, "w") as outp:
        outp.write(content)
    return True

_OTC_CONF_TEMPLATE = """
[opentree]
phylesystem = {ph}
peyotl = {pe}
ott = {o}
collections = {c}
script-managed-trees = {s}
"""

def gen_otc_config_content():
    """Composes a config file for the otcetera run

    Serializes global variables from this Snakemake run.
    """
    return _OTC_CONF_TEMPLATE.format(ph=phylesystem_dir,
                                     pe=peyotl_dir,
                                     o=ott_dir,
                                     c=collections_dir,
                                     s=script_managed_trees_dir)

_CONF_TEMPLATE = """
[taxonomy]
cleaning_flags = {cf}
additional_regrafting_flags = {arf}

[synthesis]
collections = {c}
root_ott_id = {r}
synth_id = {s}
"""

def gen_config_content():
    """Composes a config file for the propinquity

    Serializes global variables in a backward-compatible manner
    for the pre-snakemake propinquity.
    """
    return _CONF_TEMPLATE.format(cf=cleaning_flags,
                                 arf=additional_regrafting_flags,
                                 c=collections,
                                 r=root_ott_id,
                                 s=synth_id)


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

def gen_tree_tags(study_tree_pair_fp):
    with open(study_tree_pair_fp, "r") as inp:
        for line in inp:
            ls = line.strip()
            if ls:
                yield ls

# end helpers
################################################################################
# major actions

def suppress_by_flag(ott_dir,
                     flags,
                     root,
                     out_nonredundanttree_fp,
                     out_with_deg2_tree_fp,
                     log_fp,
                     prune_log,
                     flagged_fp):
    raise NotImplementedError("$(PEYOTL_ROOT)/scripts/ott/suppress_by_flag.py")

def export_collections(export, concrete_coll_json_fp, out_fp, obj_blob_shas_fp):
    raise NotImplementedError("$(PEYOTL_ROOT)/scripts/collection_export.py")

def export_studies_from_collection(ranked_coll,
                                   phylesystem_par,
                                   out_par):
    raise NotImplementedError("$(PEYOTL_ROOT)/scripts/phylesystem/export_studies_from_collection.py -v")

def get_empty_collection():
    collection = {
        "url": "",
        "name": "",
        "description": "",
        "creator": {"login": "", "name": ""},
        "contributors": [],
        "decisions": [],
        "queries": []
    }
    return collection

def concatenate_collections(collection_list):
    r = get_empty_collection()
    r_decisions = r['decisions']
    r_contributors = r['contributors']
    r_queries = r['queries']
    contrib_set = set()
    inc_set = set()
    not_inc_set = set()
    for n, coll in enumerate(collection_list):
        r_queries.extend(coll['queries'])
        for contrib in coll['contributors']:
            l = contrib['login']
            if l not in contrib_set:
                r_contributors.append(contrib)
                contrib_set.add(l)
        for d in coll['decisions']:
            key = '{}_{}'.format(d['studyID'], d['treeID'])
            inc_d = d['decision'].upper() == 'INCLUDED'
            if key in inc_set:
                if not inc_d:
                    raise ValueError('Collections disagree on inclusion of study_tree = "{}"'.format(key))
            elif key in not_inc_set:
                if inc_d:
                    raise ValueError('Collections disagree on inclusion of study_tree = "{}"'.format(key))
            else:
                if inc_d:
                    inc_set.add(key)
                else:
                    not_inc_set.add(key)
                r_decisions.append(d)
    return r

def reaggregate_synth_collections(inp_fp_list, out_fp):
    """Writes the contents of `inp_fp_list` as one collection at `out_fp`."""
    inp = [read_as_json(i) for i in inp_fp_list]
    blob = concatenate_collections(inp)
    content = json.dumps(blob, indent=0, sort_keys=True) + '\n'
    return write_if_needed(fp=out_fp,
                           content=content,
                           name="concatenated collections")


def clean_phylo_input(ott_dir,
                      study_tree_pairs,
                      tree_filepaths,
                      output_dir,
                      cleaning_flags,
                      pruned_from_ott_json_fp,
                      root_ott_id):
    raise NotImplementedError("$(PEYOTL_ROOT)/scripts/nexson/prune_to_clean_mapped.py ")



# def verify_taxon_edits_not_needed(json_fp, unclean_ott, out_ott):
#     with codecs.open(json_fp, mode='r', encoding='utf-8') as jinp:
#         jout = json.load(jinp)
#     if "edits" in jout:
#         return False
#     if len(sys.argv) > 2:
#     try:
#         from shutil import copyfile
#         copyfile(sys.argv[2], sys.argv[3])
#     except:
#         sys.stderr.write(usage)
#         raise
