#!/usr/bin/env python3

from collections import defaultdict
import subprocess
import filecmp
import codecs
import shutil
import json
import copy
import sys
import os
import re
import io
from pathlib import Path


from peyutil import (is_str_type, is_int_type,
                     propinquity_fn_to_study_tree,
                     read_as_json, write_as_json)
from nexson import (extract_tree_nexson,
                    nexson_frag_write_newick)
from peyotl import Phylesystem
# TODO: move these up to top-level peyotl imports, when that is supported
from peyotl.ott import OTT
from peyotl.phylo.entities import OTULabelStyleEnum

__version__ = '2.0.dev1'

OTT_FILENAMES = ("forwards.tsv", 
                 "synonyms.tsv", 
                 "taxonomy.tsv", 
                 "version.txt", 
                 )

class PropinquityConfig(object):
    """
    Validatng config and setting global variables:
    Executed on startup.
    Defines the following globals based on config,
      lists as a comma-separated string:
          additional_regrafting_flags (e.g. "extinct_inherited,extinct")
          cleaning_flags (e.g "major_rank_conflict,barren")
          collections (e.g. "kcranston/catfish,kcranston/barnacles")
      Paths to directories
          collections_dir - parent of shards
          ott_dir
          out_dir - set by the --directory arg to snakemake
          peyotl_dir
          phylesystem_dir - parent of shards
          script_managed_trees_dir
      Run-specific IDs:
          root_ott_id
          synth_id
    
    Validation also sets environmental variables:
      OTC_CONFIG and OTCETERA_LOGFILE
    """

    def __init__(self, config, logger):
        self.log = logger
        self.propinquity_dir = os.path.abspath(config.get("propinquity_dir", os.curdir))
        if not os.path.isdir(self.propinquity_dir):
            m = "propinquity_dir from config {pd} does not an existing directory.\n".format(pd=propinquity_dir)
            raise RuntimeError(m)
        _config_dirs = ("collections_dir",
                        "ott_dir",
                        "phylesystem_dir",
                        "script_managed_trees_dir",
                        )
        ot_home = config.get('opentree_home')
        self.opentree_home = ot_home
        defaults = {}
        if ot_home:
            defaults["collections_dir"] = os.path.join(ot_home, "phylesystem")
            defaults["phylesystem_dir"] = defaults["collections_dir"]
            defaults["script_managed_trees_dir"] = os.path.join(ot_home, "script-managed-trees")
        try:
            for _ds in _config_dirs:
                _v = config.get(_ds, defaults.get(_ds))
                if _v is None:
                    raise RuntimeError("Missing config variable '{x}'".format(x=_ds))
                setattr(self, _ds, _v)
                if not os.path.isdir(_v):
                    m = '{p} "{v}"" does not exist.\n'.format(p=_ds, v=_v)
                    raise RuntimeError(m)
            self.collections = canon_sep_string(config["collections"], sort=False)
            self.cleaning_flags = canon_sep_string(config["cleaning_flags"])
            self.additional_regrafting_flags = canon_sep_string(config.get("additional_regrafting_flags", ""))
            self.root_ott_id = config["root_ott_id"]
            self.synth_id = config["synth_id"]
        except KeyError as x:
            raise RuntimeError("Missing config variable {x}".format(x=str(x)))
        if not os.path.isdir(os.path.join(self.phylesystem_dir, "shards", "phylesystem-1")):
            m = 'phylesystem_dir {p} is expeceted to have "shards/phylesystem-1" subdirectory.'
            raise RuntimeError(m.format(p=self.phylesystem_dir))
        if not os.path.isdir(os.path.join(self.collections_dir, "shards", "collections-1")):
            m = 'collections_dir {c} is expeceted to have "shards/collections-1" subdirectory.'
            raise RuntimeError(m.format(c=self.collections_dir))
        self.out_dir = os.path.abspath(os.curdir)
        if 'OTC_CONFIG' not in os.environ:
            _ocfp = os.path.join(self.out_dir, "otc-config") 
            os.environ['OTC_CONFIG'] = _ocfp
            logger.debug('Setting OTC_CONFIG environment variable to "{}"'.format(_ocfp))
        implied_otc_logfile = os.path.join(self.out_dir, "logs", "myeasylog.log")
        if 'OTCETERA_LOGFILE' not in os.environ:
            os.environ['OTCETERA_LOGFILE'] = implied_otc_logfile
            m = 'Setting OTCETERA_LOGFILE environment variable to "{}"'.format(implied_otc_logfile)
            logger.debug(m)
        else:
            _ocfp = os.environ['OTCETERA_LOGFILE']
            if _ocfp != implied_otc_logfile:
                m = "Using existing value for OTCETERA_LOGFILE {}.".format(_ocfp)
                logger.warning(m)

    def debug(self, msg):
        self.log.debug(msg)

    def warn(self, msg):
        self.log.warning(msg)

    def warning(self, msg):
        return self.warn(msg)

    def info(self, msg):
        self.log.info(msg)

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

def cp_if_needed(src, dest, name=None, CFG=None):
    if (not os.path.exists(dest)) or (not filecmp.cmp(src, dest)):
        shutil.copy(src, dest)
        if CFG is not None:
            CFG.warn('cp "{}" "{}"'.format(src, dest))
        return True
    if CFG is not None:
        CFG.warn('copy of {n} not needed'.format(n=name))
    return False

def mv_if_needed(src, dest, name=None, CFG=None):
    if (not os.path.exists(dest)) or (not filecmp.cmp(src, dest)):
        if CFG is not None:
            CFG.warn('mv "{}" "{}"'.format(src, dest))
        os.rename(src, dest)
        return True
    if CFG is not None:
        CFG.warn('{n} unchanged. Removing src copy'.format(n=name))
    os.unlink(src)
    return False

def write_if_needed(fp, content, name=None, CFG=None):
    """Writes `content` to `fp` if the content of that filepath is empty or different.

    Returns True if a write was done, False if the file already had that content.
    if `name` is not None, and the filepath has not changed, then
        a logger.warn "{name} has not changed" message will be emitted.
    """
    if os.path.exists(fp):
        prev_content = open(fp, "r").read()
        if prev_content == content:
            if name is not None:
                if CFG is not None:
                    CFG.warn("{n} has not changed".format(n=name))
            return False
    with open(fp, "w") as outp:
        outp.write(content)
    return True

_OTC_CONF_TEMPLATE = """
[opentree]
phylesystem = {ph}
ott = {o}
collections = {c}
script-managed-trees = {s}
"""

def gen_otc_config_content(cfg):
    """Composes a config file for the otcetera run

    Serializes global variables from this Snakemake run.
    """
    return _OTC_CONF_TEMPLATE.format(ph=cfg.phylesystem_dir,
                                     o=cfg.ott_dir,
                                     c=cfg.collections_dir,
                                     s=cfg.script_managed_trees_dir)

_CONF_TEMPLATE = """
[taxonomy]
cleaning_flags = {cf}
additional_regrafting_flags = {arf}

[synthesis]
collections = {c}
root_ott_id = {r}
synth_id = {s}
"""

def gen_config_content(cfg):
    """Composes a config file for the propinquity

    Serializes global variables in a backward-compatible manner
    for the pre-snakemake propinquity.
    """
    return _CONF_TEMPLATE.format(cf=cfg.cleaning_flags,
                                 arf=cfg.additional_regrafting_flags,
                                 c=cfg.collections,
                                 r=cfg.root_ott_id,
                                 s=cfg.synth_id)


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

def export_trees_list_and_shas(concrete_coll_json_fp,
                               out_fp,
                               obj_blob_shas_fp,
                               CFG):
    included = collection_to_included_trees(collection=None, fp=concrete_coll_json_fp)
    obj_blob_shas_lines = []
    study_tree_pair_lines = []
    for i in included:
        study_tree_pair_lines.append('@'.join([i['studyID'], i['treeID']]))
        obj_blob_shas_lines.append(i["object_SHA"])
    obs_content = '{}\n'.format('\n'.join(obj_blob_shas_lines))
    stp_content = '{}\n'.format('\n'.join(study_tree_pair_lines))
    a = write_if_needed(fp=out_fp, content=stp_content,
                        name="study@tree pairs", CFG=CFG)
    b = write_if_needed(fp=obj_blob_shas_fp, content=obs_content,
                        name="tree git object SHAs", CFG=CFG)
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

def reaggregate_synth_collections(inp_fp_list, out_fp, CFG):
    """Writes the contents of `inp_fp_list` as one collection at `out_fp`."""
    inp = [read_as_json(i) for i in inp_fp_list]
    blob = concatenate_collections(inp)
    content = json.dumps(blob, indent=0, sort_keys=True) + '\n'
    return write_if_needed(fp=out_fp,
                           content=content,
                           name="concatenated collections", CFG=CFG)

def copy_ps_file_if_needed(git_action,
                           sha,
                           coll_decision,
                           out_dir,
                           cd_to_new_map,
                           CFG):
    """Copies the tree from `coll_decision` to `out_dir` if needed.

    Returns tuple (file_exists, file_was_touche, dest_fp)
    `git_action` is a git_action wrapper from Phylesystem
    `sha` is a commit SHA for the commit (or '' for the default branch)
    `cd_to_new_map` dict mapping `id(coll_decision)` to a concrete
        decision.
    """ 
    study_id = coll_decision['studyID']
    tree_id = coll_decision['treeID']
    fp = git_action.path_for_doc(study_id)
    new_name = 'tree_{}@{}.json'.format(study_id, tree_id)
    np = os.path.join(out_dir, new_name)
    if not os.path.isfile(fp):
        if CFG is not None:
            CFG.warn('Study file "{}" does not exist. Assuming that this study has been deleted'.format(fp))
        if os.path.isfile(np):
            os.remove(np)
        return False, False, None
    # create a new "decision" entry that is bound to this SHA
    concrete_coll_decision = copy.deepcopy(coll_decision)
    concrete_coll_decision['SHA'] = sha
    concrete_coll_decision['object_SHA'] = git_action.object_SHA(study_id, sha)
    cd_to_new_map[id(coll_decision)] = concrete_coll_decision
    if not cp_if_needed(fp, np, study_id, CFG=CFG):
        return True, False, np
    return True, True, np


def export_studies_from_collection(ranked_coll_fp,
                                   phylesystem_par,
                                   script_managed_trees,
                                   out_par,
                                   concrete_coll_out_fp,
                                   CFG=None):
    # Get the list of included trees
    try:
        included = collection_to_included_trees(fp=ranked_coll_fp)
    except:
        if CFG is not None:
            CFG.error('Error: JSON parse error when reading collection "{}".\n'.format(ranked_coll_fp))
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
            if CFG is not None:
                CFG.warn(fp + ' does not exist: removing from collection on the assumption that the study has been deleted.')
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
    file_names_copied = set()
    for sha, from_this_sha_inc in included_by_sha.items():
        for inc in from_this_sha_inc:
            study_id = inc['studyID']
            if CFG is not None:
                CFG.info('study_id={s} from SHA={h}'.format(s=study_id, h=sha))
            ga = ps.create_git_action(study_id)
            with ga.lock():
                if sha == '':
                    needs_reset_to_master = False
                    ga.checkout_master()
                else:
                    ga.checkout(sha)
                    needs_reset_to_master = True
                x = copy_ps_file_if_needed(ga, sha, inc,
                                           out_par, generic2concrete, CFG=CFG)
                if x[0]:
                    file_name = os.path.split(x[-1])[-1]
                    file_names_copied.add(file_name)
                    num_moved += 1
                else:
                    num_deleted += 1
    if needs_reset_to_master:
        ga.checkout_master()
    if CFG:
        CFG.debug('{} total trees'.format(len(included) - num_deleted))
        CFG.debug('{} JSON files copied'.format(num_moved))
        CFG.debug('{} trees in collections, but with missing studies'.format(num_deleted))

    tree_file_name_pattern = re.compile(r'tree_[a-z_A-Z0-9]+@[a-z_A-Z0-9]+\.json') # {[a-z_A-Z0-9]+}.*{+}.json')
    for i in os.listdir(out_par):
        if tree_file_name_pattern.match(i):
            if i not in file_names_copied:
                if CFG is not None:
                    CFG.warn('need to delete {}'.format(i))
                os.remove(os.path.join(out_par, i))

    # now we write a "concrete" version of this snapshot
    coll_name = os.path.split(ranked_coll_fp)[-1]
    coll_tag = '.'.join(coll_name.split('.')[:-1])
    concrete_collection = get_empty_collection()
    cd_list = concrete_collection['decisions']
    ifn = os.path.split(ranked_coll_fp)[-1]
    m = 'Concrete form of collection "{}"'.format(ifn)
    concrete_collection['description'] = m
    for inc in included:
        try:
            concrete = generic2concrete[id(inc)]
            cd_list.append(concrete)
        except KeyError:
            pass
    ccc = json.dumps(concrete_collection, indent=0, sort_keys=True) + '\n'
    write_if_needed(content=ccc, fp=concrete_coll_out_fp, CFG=CFG)

def merge_concrete_collection(ranked_coll_fp, concrete_coll, out_json_fp):
    raise ValueError('\n'.join([str(i) for i in (ranked_coll_fp, concrete_coll, out_json_fp)]))


def suppress_by_flag(ott_dir,
                     flags,
                     root,
                     out_nonredundanttree_fp,
                     out_with_deg2_tree_fp,
                     log_fp,
                     prune_log,
                     flagged_fp):
    if not isinstance(flags, list):
        flags = flags.split(',')
    ott = OTT(ott_dir=ott_dir)
    create_log = (log_fp is not None) or (flagged_fp is not None)
    with codecs.open(out_with_deg2_tree_fp, 'w', encoding='utf-8') as outp:
        log = ott.write_newick(outp,
                               label_style=OTULabelStyleEnum.CURRENT_LABEL_OTT_ID,
                               root_ott_id=int(root),
                               prune_flags=flags,
                               create_log_dict=create_log)
        outp.write('\n')
    if flagged_fp is not None:
        d = {'extinct': log.get('extinct_unpruned_ids',[]),
             'incertae_sedis': log.get('incertae_sedis_unpruned_ids', [])
            }
        write_as_json(d, flagged_fp)
    if log_fp is not None:
        write_as_json(log, log_fp)
    if out_nonredundanttree_fp is None:
        return
    invocation = ["otc-relabel-tree",
                  out_with_deg2_tree_fp,
                  "--del-higher-taxon-tips",
                  "-j{}".format(prune_log),
                  "--taxonomy",
                  ott_dir,
                  ]
    with open(out_nonredundanttree_fp, "w") as outp:
        rp = subprocess.run(invocation, stdout=outp)
    rp.check_returncode()



class EmptyTreeError(Exception):
    pass


class NexsonTreeWrapper(object):
    def __init__(self, nexson, tree_id, log_obj=None, logger_msg_obj=None):
        self.logger_msg_obj = logger_msg_obj
        self.tree, self.otus = find_tree_and_otus_in_nexson(nexson, tree_id)
        if self.tree is None:
            raise KeyError('Tree "{}" was not found.'.format(tree_id))
        self._log_obj = log_obj
        self._edge_by_source = self.tree['edgeBySourceId']
        self._node_by_id = self.tree['nodeById']
        self._root_node_id = None
        self.root_node_id = self.tree['^ot:rootNodeId']
        assert self.root_node_id
        self._ingroup_node_id = self.tree.get('^ot:inGroupClade')
        for k, v in self._node_by_id.items():
            v['@id'] = k
        self._edge_by_target = self._create_edge_by_target()
        self.nodes_deleted, self.edges_deleted = [], []
        self._by_ott_id = None
        self.is_empty = False


    def get_root_node_id(self):
        return self._root_node_id

    def set_root_node_id(self, r):
        try:
            assert r
            assert r in self._edge_by_source
            assert r in self._node_by_id
        except:
            error('Illegal root node "{}"'.format(r))
            raise
        self._root_node_id = r

    root_node_id = property(get_root_node_id, set_root_node_id)

    def _create_edge_by_target(self):
        """creates a edge_by_target dict with the same edge objects as the edge_by_source.
        Also adds an '@id' field to each edge."""
        ebt = {}
        for edge_dict in self._edge_by_source.values():
            for edge_id, edge in edge_dict.items():
                target_id = edge['@target']
                edge['@id'] = edge_id
                assert target_id not in ebt
                ebt[target_id] = edge
        # _check_rev_dict(self._tree, ebt)
        return ebt

    def _clear_del_log(self):
        self.nodes_deleted = []
        self.edges_deleted = []

    def _log_deletions(self, key):
        if self._log_obj is not None:
            o = self._log_obj.setdefault(key, {'nodes': [], 'edges': []})
            o['nodes'].extend(self.nodes_deleted)
            o['edges'].extend(self.edges_deleted)
        self._clear_del_log()

    def _do_prune_to_ingroup(self):
        edge_to_del = self._edge_by_target.get(self._ingroup_node_id)
        if edge_to_del is None:
            return
        try:
            self.prune_edge_and_rootward(edge_to_del)
        finally:
            self._log_deletions('outgroup')

    def prune_to_ingroup(self):
        """Remove nodes and edges from tree if they are not the ingroup or a descendant of it."""
        # Prune to just the ingroup
        if not self._ingroup_node_id:
            if self.logger_msg_obj is not None:
                self.logger_msg_obj.debug('No ingroup node was specified.')
            self._ingroup_node_id = self.root_node_id
        elif self._ingroup_node_id != self.root_node_id:
            self._do_prune_to_ingroup()
            self.root_node_id = self._ingroup_node_id
        else:
            self.logger_msg_obj.debug('Ingroup node is root.')
        return self.root_node_id

    def prune_edge_and_rootward(self, edge_to_del):
        while edge_to_del is not None:
            source_id, target_id = self._del_edge(edge_to_del)
            ebsd = self._edge_by_source.get(source_id)
            if ebsd:
                to_prune = list(ebsd.values())  # will modify ebsd in loop below, so shallow copy
                for edge in to_prune:
                    self.prune_edge_and_tipward(edge)
                assert source_id not in self._edge_by_source
            edge_to_del = self._edge_by_target.get(source_id)

    def prune_edge_and_tipward(self, edge):
        source_id, target_id = self._del_edge(edge)
        self.prune_clade(target_id)

    def prune_clade(self, node_id):
        """Prune `node_id` and the edges and nodes that are tipward of it.
        Caller must delete the edge to node_id."""
        to_del_nodes = [node_id]
        while bool(to_del_nodes):
            node_id = to_del_nodes.pop(0)
            self._flag_node_as_del_and_del_in_by_target(node_id)
            ebsd = self._edge_by_source.get(node_id)
            if ebsd is not None:
                child_edges = list(ebsd.values())
                to_del_nodes.extend([i['@target'] for i in child_edges])
                del self._edge_by_source[
                    node_id]  # deletes all of the edges out of this node (still held in edge_by_target til children are encountered)

    def _flag_node_as_del_and_del_in_by_target(self, node_id):
        """Flags a node as deleted, and removes it from the _edge_by_target (and parent's edge_by_source), if it is still found there.
        Does NOT remove the node's entries from self._edge_by_source."""
        self.nodes_deleted.append(node_id)
        etp = self._edge_by_target.get(node_id)
        if etp is not None:
            del self._edge_by_target[node_id]

    def _del_edge(self, edge_to_del):
        edge_id = edge_to_del['@id']
        target_id = edge_to_del['@target']
        source_id = edge_to_del['@source']
        del self._edge_by_target[target_id]
        ebsd = self._edge_by_source[source_id]
        del ebsd[edge_id]
        if not ebsd:
            del self._edge_by_source[source_id]
        self.edges_deleted.append(edge_id)
        return source_id, target_id

    def _del_tip(self, node_id):
        """Assumes that there is no entry in edge_by_source[node_id] to clean up."""
        self.nodes_deleted.append(node_id)
        etp = self._edge_by_target.get(node_id)
        assert etp is not None
        source_id, target_id = self._del_edge(etp)
        assert target_id == node_id
        return source_id

    def group_and_sort_leaves_by_ott_id(self):
        """returns a dict mapping ott_id to list of elements referring to leafs mapped
        to that ott_id. They keys will be ott_ids and None (for unmapped tips). The values
        are lists of tuples. Each tuple represents a different leaf and contains:
            (integer_for_of_is_examplar: -1 if the node is flagged by ^ot:isTaxonExemplar. 0 otherwise
            the leaf's node_id,
            the node object
            the otu object for the node
            )
        """
        ott_id_to_sortable_list = defaultdict(list)
        for node_id in self._edge_by_target.keys():
            node_obj = self._node_by_id[node_id]
            if node_id in self._edge_by_source:
                continue
            otu_id = node_obj['@otu']
            otu_obj = self.otus[otu_id]
            ott_id = otu_obj.get('^ot:ottId')
            is_exemplar = node_obj.get('^ot:isTaxonExemplar', False)
            int_is_exemplar = 0
            if is_exemplar:
                int_is_exemplar = -1  # to sort to the front of the list
            sortable_el = (int_is_exemplar, node_id, node_obj, otu_obj)
            ott_id_to_sortable_list[ott_id].append(sortable_el)
        for v in ott_id_to_sortable_list.values():
            v.sort()
        return ott_id_to_sortable_list

    @property
    def by_ott_id(self):
        if self._by_ott_id is None:
            self._by_ott_id = self.group_and_sort_leaves_by_ott_id()
        return self._by_ott_id

    def prune_unmapped_leaves(self):
        # Leaf nodes with no OTT ID at all...
        if None in self.by_ott_id:
            self.prune_tip_in_sortable_list(self.by_ott_id[None], 'unmapped_otu')
            del self.by_ott_id[None]

    def prune_tip_in_sortable_list(self, sortable_list, reason):
        try:
            par_to_check = set()
            for sortable_el in sortable_list:
                node_id = sortable_el[1]
                par_to_check.add(self._del_tip(node_id))
                self.nodes_deleted.append(node_id)
        finally:
            self._log_deletions(reason)
        self.prune_if_deg_too_low(par_to_check)

    prune_ott_problem_leaves = prune_tip_in_sortable_list

    def prune_if_deg_too_low(self, ind_nd_id_list):
        try:
            orphaned_root = None
            while bool(ind_nd_id_list):
                next_ind_nd_id_list = set()
                for nd_id in ind_nd_id_list:
                    out_edges = self._edge_by_source.get(nd_id)
                    if out_edges is None:
                        out_degree = 0
                    else:
                        out_degree = len(out_edges)
                    if out_degree < 2:
                        to_par = self._edge_by_target.get(nd_id)
                        if to_par:
                            par = to_par['@source']
                            next_ind_nd_id_list.add(par)
                            if out_degree == 1:
                                out_edge = list(out_edges.values())[0]
                                self.suppress_deg_one_node(to_par, nd_id, out_edge)
                            else:
                                self._del_tip(nd_id)
                            if nd_id in next_ind_nd_id_list:
                                next_ind_nd_id_list.remove(nd_id)
                        else:
                            assert (orphaned_root is None) or (orphaned_root == nd_id)
                            orphaned_root = nd_id
                ind_nd_id_list = next_ind_nd_id_list
            if orphaned_root is not None:
                new_root = self.prune_deg_one_root(orphaned_root)
                if self._log_obj is not None:
                    self._log_obj['revised_ingroup_node'] = new_root
                self.root_node_id, self._ingroup_node_id = new_root, new_root
        finally:
            self._log_deletions('became_trivial')

    def suppress_deg_one_node(self, to_par_edge, nd_id, to_child_edge):
        """Deletes to_par_edge and nd_id. To be used when nd_id is an out-degree= 1 node"""
        # circumvent the node with nd_id
        to_child_edge_id = to_child_edge['@id']
        par = to_par_edge['@source']
        self._edge_by_source[par][to_child_edge_id] = to_child_edge
        to_child_edge['@source'] = par
        # make it a tip...
        del self._edge_by_source[nd_id]
        # delete it
        self._del_tip(nd_id)

    def prune_deg_one_root(self, new_root):
        while True:
            ebs_el = self._edge_by_source.get(new_root)
            if ebs_el is None:
                self.is_empty = True
                raise EmptyTreeError()
            if len(ebs_el) > 1:
                return new_root
            edge = list(ebs_el.values())[0]
            new_root = edge['@target']
            self._del_tip(new_root)

    def prune_ott_problem_leaves_by_id(self, ott_id, reason):
        self.prune_ott_problem_leaves(self.by_ott_id[ott_id], reason)
        del self.by_ott_id[ott_id]

    def prune_tree_for_supertree(self,
                                 ott,
                                 to_prune_fsi_set,
                                 root_ott_id,
                                 taxonomy_treefile=None,
                                 id_to_other_prune_reason=None):
        """
        `to_prune_fsi_set` is a set of flag indices to be pruned.
        """
        if id_to_other_prune_reason is None:
            id_to_other_prune_reason = {}
        self.prune_to_ingroup()
        self.prune_unmapped_leaves()
        other_pruned = set()
        if id_to_other_prune_reason:
            id2p = set(id_to_other_prune_reason.keys()).intersection(set(self.by_ott_id.keys()))
            for ott_id in id2p:
                reason = id_to_other_prune_reason[ott_id]
                self.prune_ott_problem_leaves_by_id(ott_id, reason)
        # Check the stored OTT Ids against the current version of OTT
        mapped, unrecog, forward2unrecog, pruned, above_root, old2new = ott.map_ott_ids(self.by_ott_id.keys(),
                                                                                        to_prune_fsi_set, root_ott_id)
        for ott_id in unrecog:
            self.prune_ott_problem_leaves_by_id(ott_id, 'unrecognized_ott_id')
        for ott_id in forward2unrecog:
            self.prune_ott_problem_leaves_by_id(ott_id, 'forwarded_to_unrecognized_ott_id')
        for ott_id in pruned:
            self.prune_ott_problem_leaves_by_id(ott_id, 'flagged')
        for ott_id in above_root:
            self.prune_ott_problem_leaves_by_id(ott_id, 'above_root')
        for old_id, new_id in old2new.items():
            old_node_list = self.by_ott_id[old_id]
            del self.by_ott_id[old_id]
            if new_id in self.by_ott_id:
                v = self.by_ott_id[new_id]
                v.extend(old_node_list)
                v.sort() # I think only the last step requires sorting (NEED to check that,
                         # If so, we could move this sort to that point to avoid multiple sortings.
            else:
                self.by_ott_id[new_id] = old_node_list
            for sortable_el in old_node_list:
                otu = sortable_el[3]
                assert otu['^ot:ottId'] == old_id
                otu['^ot:ottId'] = new_id
                assert '^ot:ottTaxonName' in otu
                otu['^ot:ottTaxonName'] = ott.get_name(new_id)
        lost_tips = set(unrecog)
        lost_tips.update(forward2unrecog)
        lost_tips.update(pruned)
        lost_tips.update(other_pruned)
        # Get the induced tree...
        assert self.root_node_id
        try:
            ott_tree = ott.induced_tree(mapped, create_monotypic_nodes=True)
        except SpikeTreeError:
            error('SpikeTreeError from mapped ott_id list = {}'.format(', '.join([str(i) for i in mapped])))
            raise EmptyTreeError()
        if taxonomy_treefile is not None:
            with codecs.open(taxonomy_treefile, 'w', encoding='utf-8') as tto:
                ott_tree.write_newick(tto)
        # ... so that we can look for leaves mapped to ancestors of other leaves
        taxon_contains_other_ott_ids = []
        to_retain = []
        for ott_id in self.by_ott_id:
            if ott_id in lost_tips:
                continue
            n = old2new.get(ott_id)
            if n is None:
                n = ott_id
            nd = ott_tree.find_node(n)
            assert nd is not None
            if nd.children:
                # nd must be an internal node.
                #   given that the descendants of this node are mapped in a more specific
                #   way, we will prune this ott_id from the tree
                taxon_contains_other_ott_ids.append(ott_id)
            else:
                to_retain.append(ott_id)

        for ott_id in taxon_contains_other_ott_ids:
            self.prune_ott_problem_leaves_by_id(ott_id, 'mapped_to_taxon_containing_other_mapped_tips')
        # finally, we walk through any ott_id's mapped to multiple nodes
        for ott_id in to_retain:
            nm = self.by_ott_id[ott_id]
            if len(nm) > 1:
                el = nm.pop(0)
                reason = 'replaced_by_exemplar_node' if (el[0] == -1) else 'replaced_by_arbitrary_node'
                self.prune_ott_problem_leaves_by_id(ott_id, reason)
        return self

def find_tree_and_otus_in_nexson(nexson, tree_id):
    tl = extract_tree_nexson(nexson, tree_id)
    if (len(tl) != 1):
        #        sys.stderr.write('{}: len(tl) = {}\n'.format(tree_id,len(tl)))
        return None, None
    tree_id, tree, otus = tl[0]
    return tree, otus


def generate_newicks_for_external_trees(external_trees,
                                        ott_dir,
                                        root,
                                        clean_flags,
                                        out_dir,
                                        script_managed_trees_path,
                                        nonempty_out_fp,
                                        CFG=None):
    """Returns True if any files are written."""
    # Generate the newick for the external trees here!
    if not external_trees:
        return False
    assert script_managed_trees_path, "Path for script-managed-trees not set!"

    cmd = ['otc-prune-clean',
           '--taxonomy={}'.format(ott_dir),
           '--root={}'.format(root),
           '--clean={}'.format(clean_flags),
           '--out-dir={}'.format(out_dir)]
    to_add = []
    for (study_tree, path) in external_trees:
        path = os.path.join(script_managed_trees_path, path)
        cmd.append(f"{path}:{study_tree}")
        to_add.append(os.path.join(out_dir, study_tree + ".tre"))

    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        CFG.warning(e.stdout.decode('UTF-8'))
        CFG.warning(e.stderr.decode('UTF-8'))
        raise e
    nonempty_out_fp.extend(to_add)
    return True

def clean_phylo_input(ott_dir,
                      study_tree_pairs,
                      tree_filepaths,
                      output_dir,
                      cleaning_flags,
                      pruned_from_ott_json_fp,
                      root_ott_id,
                      script_managed_dir,
                      nonempty_out_fp,
                      CFG=None):
    """Returns True if any files are written or deleted."""
    par_inp = os.path.split(output_dir)[0]
    inp_files = [os.path.join(par_inp, i) for i in tree_filepaths]
    to_prune_for_reasons = {}
    if pruned_from_ott_json_fp is not None:
        try:
            nonflagged_blob = read_as_json(pruned_from_ott_json_fp)
        except:
            nonflagged_blob = None
        if nonflagged_blob:
            for reason, id_list in nonflagged_blob.items():
                for ott_id in id_list:
                    to_prune_for_reasons[ott_id] = reason
    if (root_ott_id is not None) and (not is_int_type(root_ott_id)):
        root_ott_id = int(root_ott_id)
    if cleaning_flags is None:
        cleaning_flags = OTT.TREEMACHINE_SUPPRESS_FLAGS
    flags = [i.strip() for i in cleaning_flags.split(',') if i.strip()]
    ott = OTT(ott_dir=ott_dir)
    to_prune_fsi_set = ott.convert_flag_string_set_to_union(flags)

    external_trees = []
    touched = False
    all_newick_fps = []
    for inp in inp_files:
        if CFG is not None:
            CFG.debug('{}'.format(inp))
        log_obj = {}
        inp_fn = os.path.split(inp)[-1]
        study_tree = '.'.join(inp_fn.split('.')[:-1])  # strip extension
        study_id, tree_id = propinquity_fn_to_study_tree(inp_fn)
        nexson_blob = read_as_json(inp)
        nexml_blob = nexson_blob["nexml"]
        if "externalTrees" in nexml_blob or ():
            etlist = nexson_blob["nexml"]["externalTrees"]
            for et in etlist:
                path = et["pathFromScriptManagedRepo"]
                print(f'{study_tree} at {path}')
                external_trees.append( (study_tree,path) )
            continue

        ntw = NexsonTreeWrapper(nexson_blob, tree_id, log_obj=log_obj,
                                logger_msg_obj=CFG)
        assert ntw.root_node_id
        taxonomy_treefile = os.path.join(output_dir, study_tree + '-taxonomy.tre')
        try:
            ntw.prune_tree_for_supertree(ott=ott,
                                         to_prune_fsi_set=to_prune_fsi_set,
                                         root_ott_id=root_ott_id,
                                         taxonomy_treefile=taxonomy_treefile,
                                         id_to_other_prune_reason=to_prune_for_reasons)
        except EmptyTreeError:
            log_obj['EMPTY_TREE'] = True
        out_log = os.path.join(output_dir, study_tree + '.json')
        write_as_json(log_obj, out_log)
        newick_fp = os.path.join(output_dir, study_tree + '.tre')



        def compose_label(node_id, node, otu):
            try:
                return '_'.join([otu['^ot:ottTaxonName'], str(node_id), 'ott' + str(otu['^ot:ottId'])])
            except:
                # internal nodes may lack otu's but we still want the node Ids
                return '_{}_'.format(str(node_id))

        if ntw.is_empty:
            if os.path.isfile(newick_fp):
                os.unlink(newick_fp)
                touched = True
            continue
        outp = io.StringIO()
        nexson_frag_write_newick(outp,
                                 ntw._edge_by_source,
                                 ntw._node_by_id,
                                 ntw.otus,
                                 label_key=compose_label,
                                 leaf_labels=None,
                                 root_id=ntw.root_node_id,
                                 ingroup_id=None,
                                 bracket_ingroup=False,
                                 with_edge_lengths=False)
        outp.write('\n')
        content = outp.getvalue()
        if write_if_needed(content=content, fp=newick_fp):
            touched = True
        all_newick_fps.append(newick_fp)
    if generate_newicks_for_external_trees(external_trees,
                                           ott_dir,
                                           root_ott_id,
                                           cleaning_flags,
                                           output_dir,
                                           script_managed_dir,
                                           all_newick_fps,
                                           CFG=CFG):
        touched = True
    with open(nonempty_out_fp, "w") as neop:
        neop.write('{}\n'.format('\n'.join(all_newick_fps)))
    return touched

def force_or_touch_file(fn, touch=True):
    """Touches fn if touch is True. If touch is False, it will create fn
    if fn does not exist. However, it will not update the timestamp
    of fn if fn already existed.

    This is useful if you need `fn` to exist when an operation is completed,
        but you don't want to touch it unnecessarily if it has not changed.
    Thus, the caller would pass in False if the content is unchanged.
    """
    if touch or not os.path.exists(fn):
        touch_file(fn)

def touch_file(fn):
    Path(fn).touch()



def detect_extinct_taxa_to_bump(ott_tree,
                                phylo_input_fp,
                                ott_flagged,
                                out,
                                CFG=None):
    invocation = ["otc-move-extinct-higher-to-avoid-contesting-taxa",
                  ott_tree,
                  "-f{}".format(phylo_input_fp),
                  "-t{}".format(ott_flagged),
                  "-j{}".format(out),
                  ]
    rp = subprocess.run(invocation)
    rp.check_returncode()


def write_modified_taxonomy_tsv(inf, outf, uid_id_to_new_parent):
    m = {}
    for line in inf:
        ls = line.split('\t')
        uid = ls[0]
        new_par = uid_id_to_new_parent.get(uid)
        if new_par is None:
            outf.write(line)
            continue
        assert ls[1] == '|'
        old_par = ls[2]
        ls[2] = new_par
        m[uid] = {'old_parent': old_par, 'new_parent': new_par}
        outf.write('\t'.join(ls))
    return m

_OTT_VERS_FN = 'ott_version.txt'

def _write_bumped_taxonomy(src_ott_dir, bump_json_fp, out_dir, CFG=None):
    with codecs.open(bump_json_fp, mode='r', encoding='utf-8') as jinp:
        jout = json.load(jinp)
    move_edit_dict = jout["edits"]
    fossil_id_to_parent = {}
    for mk, mv in move_edit_dict.items():
        if not mk.startswith('ott'):
            m = "Key in {} 'edits' dict element of {} does not start with ott"
            raise ValueError(m.format(mk, move_json_filepath))
        k = mk[3:].strip()
        np = mv["new_parent"]
        if not np.startswith('ott'):
            m = "new_parent in {} 'edits' dict element of {} does not start with ott"
            raise ValueError(m.format(mk, move_json_filepath))
        v = np[3:].strip()
        fossil_id_to_parent[k] = v
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    needs_taxonomy = True
    if fossil_id_to_parent:
        infp = os.path.join(src_ott_dir, 'taxonomy.tsv')
        outfp = os.path.join(out_dir, 'taxonomy.tsv')
        needs_taxonomy = False
        with codecs.open(infp, 'r', encoding='utf-8') as inp:
            with codecs.open(outfp, 'w', encoding='utf-8') as outp:
                m = write_modified_taxonomy_tsv(inp, outp, fossil_id_to_parent)
        outfp = os.path.join(out_dir, 'patched_by_bumping.json')
        write_as_json(m, outfp)
    _cp_taxonomy(src_ott_dir,
                 out_dir,
                 cp_taxonomy_tsv=needs_taxonomy,
                 CFG=CFG)
    vt = os.path.join(out_dir, 'version.txt')
    vers_text = open(vt, "r").read().strip()
    synth_id = getattr(CFG, 'synth_id', 'synth-?')
    ott_vers_text = '{}-extinct-bumped-{}\n'.format(vers_text, synth_id)
    fp = os.path.join(out_dir, _OTT_VERS_FN)
    write_if_needed(fp, ott_vers_text, name=_OTT_VERS_FN, CFG=CFG)

def _cp_taxonomy(src_ott_dir, out_dir, cp_taxonomy_tsv=True, CFG=None):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    for fn in OTT.FILENAMES:
        if (not cp_taxonomy_tsv) and fn == 'taxonomy.tsv':
            continue
        src = os.path.join(src_ott_dir, fn)
        dest = os.path.join(out_dir, fn)
        if not os.path.exists(src):
            if CFG:
                CFG.warning('taxonomy file "{}" does not exist, skipping...'.format(src))
            continue
        cp_if_needed(src=src, dest=dest, name=fn, CFG=CFG)

def bumping_of_extinct_req(bump_json_fp):
    with open(bump_json_fp, mode='r', encoding='utf-8') as jinp:
        bump_dict = json.load(jinp)
    return "edits" in bump_dict

def bump_or_link(src_ott_dir,
                 bump_json_fp,
                 out_dir,
                 CFG=None):
    if bumping_of_extinct_req(bump_json_fp):
        _write_bumped_taxonomy(src_ott_dir, bump_json_fp, out_dir, CFG=CFG)
        return True
    _cp_taxonomy(src_ott_dir, out_dir, cp_taxonomy_tsv=True, CFG=CFG)
    cp_if_needed(os.path.join(src_ott_dir, 'version.txt'),
                 os.path.join(out_dir, _OTT_VERS_FN),
                 _OTT_VERS_FN,
                 CFG=CFG)

def cp_or_suppress_by_flag(ott_dir,
                           flags,
                           root,
                           bump_json_fp,
                           in_nonredundanttree_fp,
                           in_with_deg2_tree_fp,
                           in_log_fp,
                           in_prune_log,
                           in_flagged_fp,
                           out_nonredundanttree_fp,
                           out_with_deg2_tree_fp,
                           out_log_fp,
                           out_prune_log,
                           out_flagged_fp,
                           CFG=None):
    if bumping_of_extinct_req(bump_json_fp):
        suppress_by_flag(ott_dir=ott_dir,
                         flags=flags,
                         root=root,
                         out_nonredundanttree_fp=out_nonredundanttree_fp,
                         out_with_deg2_tree_fp=out_with_deg2_tree_fp,
                         log_fp=out_log_fp,
                         prune_log=out_prune_log,
                         flagged_fp=out_flagged_fp)
        return
    cp_list = [(in_nonredundanttree_fp, out_nonredundanttree_fp),
               (in_with_deg2_tree_fp, out_with_deg2_tree_fp),
               (in_log_fp, out_log_fp),
               (in_prune_log, out_prune_log),
               (in_flagged_fp, out_flagged_fp),
              ]
    for src, dest in cp_list:
        cp_if_needed(src, dest, os.path.split(src)[-1], CFG=CFG)


def subset_ott(orig_ott_dir, sub_ott_dir, root_id, CFG):
    ofp = os.path.abspath(sub_ott_dir)
    invocation = ["otc-taxonomy-parser",
                  os.path.abspath(orig_ott_dir),
                  "-x{}".format(root_id), # -x requires allow-subtree-of-taxonomy branch of otc
                  "--write-taxonomy={}".format(ofp)
                 ]
    rp = subprocess.run(invocation)
    rp.check_returncode()
    _cp_taxonomy(orig_ott_dir,
                 ofp,
                 cp_taxonomy_tsv=False,
                 CFG=CFG)

def run_unhide_if_worked(invocation,
                         unhide_list,
                         CFG=None,
                         stdout_capture=None):
    """Runs `invocation`. If that does not fail, moves src to dest
    for every element in `unhide_list = [(src1, dest1), ...]
    """
    if stdout_capture is None:
        rp = subprocess.run(invocation)
        rp.check_returncode()
    else:
        par = os.path.split(stdout_capture)[0]
        if not os.path.exists(par):
            os.makedirs(par)
        with open(stdout_capture, "w") as outp:
            if subprocess.call(invocation, stdout=outp) != 0:
                raise RuntimeError('Call failed:\n"{}"\n'.format('" "'.join(invocation)))
    
    for src, dest in unhide_list:
        mv_if_needed(src=src, dest=dest, CFG=CFG)


def exemplify_taxa(in_tax_tree_fp,
                   in_phylo_fp,
                   out_nonempty_tree_fp,
                   out_log_fp,
                   CFG):
    ep_dir = os.path.split(out_nonempty_tree_fp)[0]
    tmp_nonempty = "{}.hide".format(out_nonempty_tree_fp)
    tmp_log = "{}.hide".format(out_log_fp)
    invocation = ["otc-nonterminals-to-exemplars",
                  "-e{}".format(ep_dir),
                  in_tax_tree_fp,
                  "-f{}".format(in_phylo_fp),
                  "-j{}".format(tmp_log),
                  "-n{}".format(tmp_nonempty)
                  ]
    unhide = [(tmp_nonempty, out_nonempty_tree_fp),
              (tmp_log, out_log_fp),]
    run_unhide_if_worked(invocation, unhide, CFG=CFG)

def decompose_into_subproblems(tax_tree_fp,
                               phylo_list_fp,
                               out_dir,
                               out_subprob_id_fp,
                               out_contesting,
                               CFG=None):
    tmp_subpr_id = "{}.hide".format(out_subprob_id_fp)
    tmp_contesting = "{}.hide".format(out_contesting)
    invocation = ["otc-uncontested-decompose",
                  "-e{}".format(out_dir),
                  "-x{}".format(tmp_subpr_id),
                  "-c{}".format(tmp_contesting),
                  tax_tree_fp,
                  "-f{}".format(phylo_list_fp)
                  ]
    unhide = [(tmp_subpr_id, out_subprob_id_fp),
              (tmp_contesting, out_contesting),]
    run_unhide_if_worked(invocation, unhide, CFG=CFG)

def solve_subproblem(incert_sed_fp, subprob_fp, out_fp, CFG=None):
    print(f"""{incert_sed_fp}
{subprob_fp}
{out_fp}
""")


def write_inc_sed_ids(tax_tree,
                      ott_dir,
                      config_fp,
                      out_inc_sed_id_fp,
                      CFG=None):
    out_fp = out_inc_sed_id_fp + ".hide"
    invocation = ["otc-taxonomy-parser",
                  ott_dir,
                  "--config={}".format(config_fp),
                  "--in-tree={}".format(tax_tree),
                  "--any-flag=incertae_sedis,major_rank_conflict,unplaced,unclassified",
                  '--format="%I"',
                 ]
    unhide = [(out_fp, out_inc_sed_id_fp), ]
    run_unhide_if_worked(invocation,
                         unhide,
                         CFG=CFG,
                         stdout_capture=out_fp)

