#!/usr/bin/env python3

from collections import defaultdict
import codecs
import filecmp
import shutil
import json
import copy
import sys
import os

from peyutil import (is_str_type, read_as_json, write_as_json)
from peyotl import Phylesystem

__version__ = '2.0.dev1'


class PropinquityConfig(object):
    def __init__(self, config, logger):
        self.log = logger
        print(config)

        propinquity_dir = os.path.abspath(config.get("propinquity_dir", os.curdir))
        if not os.path.isdir(propinquity_dir):
            raise RuntimeError("propinquity_dir from config {pd} does not an existing directory.\n".format(pd=propinquity_dir))

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
            raise RuntimeError(expand("Missing config variable {x}", x=str(x))[0])

        if not os.path.isdir(os.path.join(phylesystem_dir, "shards", "phylesystem-1")):
            raise RuntimeError(expand('phylesystem_dir {phylesystem_dir} is expeceted to have "shards/phylesystem-1" subdirectory.\n'))
        if not os.path.isdir(os.path.join(collections_dir, "shards", "collections-1")):
            raise RuntimeError(expand('collections_dir {collections_dir} is expeceted to have "shards/collections-1" subdirectory.\n'))


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


    def debug(self, msg):
        self.logger.debug(msg)

    def warn(self, msg):
        self.log.warning(msg)

    def error(self, msg):
        self.log.error(msg)


def validate_config(config, logger):
    return PropinquityConfig(config, logger)

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
# helper functions

def cp_if_needed(src, dest, name=None):
    if (not os.path.exists(dest)) or (not filecmp.cmp(src, dest)):
        shutil.copy(src, dest)
        warn('cp "{}" "{}"'.format(src, dest))
        return True
    warn('copy of {n} not needed'.format(n=name))
    return False

def write_if_needed(fp, content, name=None):
    """Writes `content` to `fp` if the content of that filepath is empty or different.

    Returns True if a write was done, False if the file already had that content.
    if `name` is not None, and the filepath has not changed, then
        a logger.warn "{name} has not changed" message will be emitted.
    """
    if os.path.exists(fp):
        prev_content = open(fp, "r").read()
        if prev_content == content:
            if name is not None:
                warn("{n} has not changed".format(n=name))
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

def collection_to_included_trees(collection=None, fp=None):
    """Takes a collection object (or a filepath to collection object), 

    Returns each element of from `decisions` that has the decision set to included.
    """
    if collection is None:
        collection = read_as_json(fp)
    dlist = collection.get('decisions', [])
    return [d for d in dlist if d['decision'] == 'INCLUDED']

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

def export_trees_list_and_shas(concrete_coll_json_fp, out_fp, obj_blob_shas_fp):
    included = collection_to_included_trees(collection=None, fp=concrete_coll_json_fp)
    obj_blob_shas_lines = []
    study_tree_pair_lines = []
    for i in included:
        study_tree_pair_lines.append('@'.join([i['studyID'], i['treeID']]))
        obj_blob_shas_lines.append(i["object_SHA"])
    obs_content = '{}\n'.format('\n'.join(obj_blob_shas_lines))
    stp_content = '{}\n'.format('\n'.join(study_tree_pair_lines))
    a = write_if_needed(fp=out_fp, content=stp_content,
                        name="study@tree pairs")
    b = write_if_needed(fp=obj_blob_shas_fp, content=obs_content,
                        name="tree git object SHAs")
    return a or b


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



def copy_phylesystem_file_if_differing(git_action,
                                       sha,
                                       coll_decision,
                                       out_dir,
                                       cd_to_new_map):
    study_id = coll_decision['studyID']
    tree_id = coll_decision['treeID']
    fp = git_action.path_for_doc(study_id)
    new_name = 'tree_{}@{}.json'.format(study_id, tree_id)
    np = os.path.join(out_dir, new_name)
    if not os.path.isfile(fp):
        warn('Study file "{}" does not exist. Assuming that this study has been deleted'.format(fp))
        if os.path.isfile(np):
            os.remove(np)
        return False
    # create a new "decision" entry that is bound to this SHA
    concrete_coll_decision = copy.deepcopy(coll_decision)
    concrete_coll_decision['SHA'] = sha
    concrete_coll_decision['object_SHA'] = git_action.object_SHA(study_id, sha)
    cd_to_new_map[id(coll_decision)] = concrete_coll_decision
    return cp_if_needed(fp, np, study_id)


def export_studies_from_collection(ranked_coll_fp,
                                   phylesystem_par,
                                   script_managed_trees,
                                   out_par):
    # Get the list of included trees
    try:
        included = collection_to_included_trees(fp=ranked_coll_fp)
    except:
        error('Error: JSON parse error when reading collection "{}".\n'.format(ranked_coll_fp))
        raise
    ps = Phylesystem(repos_par=phylesystem_par)
    if not os.path.isdir(out_par):
        os.makedirs(out_par)
    # Remove included trees for studies that have been removed from phylesystem
    included_and_exists = []
    for inc in included:
        study_id = inc['studyID']
        ga = ps.create_git_action(study_id)
        fp = ga.path_for_doc(study_id)
        if not os.path.isfile(fp):
            warn(fp + ' does not exist: removing from collection on the assumption that the study has been deleted.')
        else:
            included_and_exists.append(inc)
    included = included_and_exists
    included_by_sha = defaultdict(list)
    for inc in included:
        included_by_sha[inc['SHA']].append(inc)
    # map id of input included tree to concrete form
    generic2concrete = {}
    num_moved, num_deleted = 0, 0

    needs_reset_to_master = False
    for sha, from_this_sha_inc in included_by_sha.items():
        for inc in from_this_sha_inc:
            study_id = inc['studyID']
            logger.info('study_id={s} from SHA={h}'.format(s=study_id, h=sha))
            ga = ps.create_git_action(study_id)
            with ga.lock():
                if sha == '':
                    needs_reset_to_master = False
                    ga.checkout_master()
                else:
                    ga.checkout(sha)
                    needs_reset_to_master = True
                if copy_phylesystem_file_if_differing(ga, sha, inc,
                                                      out_par, generic2concrete):
                    num_moved += 1
                else:
                    num_deleted += 1
    if needs_reset_to_master:
        ga.checkout_master()
    debug('{} total trees'.format(len(included) - num_deleted))
    debug('{} JSON files copied'.format(num_moved))
    debug('{} trees in collections, but with missing studies'.format(num_deleted))

    # now we write a "concrete" version of this snapshot
    coll_name = os.path.split(ranked_coll_fp)[-1]
    coll_tag = '.'.join(coll_name.split('.')[:-1])
    for inc in included:
        concrete_collection = get_empty_collection()
        cd_list = concrete_collection['decisions']
        
        try:
            concrete = generic2concrete[id(inc)]
            cd_list.append(concrete)
        except KeyError:
            pass
        else:
            concrete_collection['description'] = m
            study_id = concrete['studyID']
            tree_id = concrete['treeID']
            new_name = '{}@{}.json'.format(study_id, tree_id)
            m = 'Concrete form of collection "{}" {}'.format(coll_name, new_name)
            concrete_fn = os.path.join(out_par, 'concrete_' + coll_tag + new_name)
            write_as_json(concrete_collection, concrete_fn)

def merge_concrete_collection(ranked_coll_fp, concrete_coll, out_json_fp):
    raise ValueError('\n'.join([str(i) for i in (ranked_coll_fp, concrete_coll, out_json_fp)]))