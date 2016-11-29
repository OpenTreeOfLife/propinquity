#!/usr/bin/env python
'''Writes html files that explains the synthesis run that was completed
'''

from __future__ import absolute_import, division, print_function, unicode_literals
try:
    from chameleon import PageTemplateLoader
except:
    import sys
    sys.exit('''Running this (optional) documentation generator requires the Chameleon
python package be installed. Usually this is simply a matter of running:

    pip install Chameleon

If that fails, consult https://chameleon.readthedocs.org/en/latest/index.html
''')
try:
    import configparser  # pylint: disable=F0401
except ImportError:
    import ConfigParser as configparser
from peyotl import read_as_json
from peyotl.utility import propinquity_fn_to_study_tree
import subprocess
import peyotl
import codecs
import json
import sys
import os
import re

class Extensible(object):
    pass

def errstream(msg):
    sys.stderr.write('{n}: ERROR: {m}\n'.format(n=SCRIPT_NAME, m=msg))

def get_property(configs, section, name):
    for config in configs:
        p = configparser.SafeConfigParser()
        try:
            p.read(config)
            return p.get(section,name).strip()
        except:
            pass

def get_property_required(configs, section, name):
    value = get_property(configs, section, name)
    if value is None:
        print >> sys.stderr , 'Could not find a [{}] section with a valid "{}" setting.'.format(section,name)
        sys.exit(0)
    return value

def parse_config(config_filepath):
    parsed_config = configparser.SafeConfigParser()
    try:
        parsed_config.read(config_filepath)
    except:
        errstream('problem reading "{}"'.format(config_filepath))
        raise
    config = Extensible()
    DEFAULT_CONFIG_LOCATION = os.path.expanduser('~/.opentree')
    config.config_filepath = os.path.abspath(config_filepath)
    config_filepaths = [config.config_filepath, DEFAULT_CONFIG_LOCATION]
    config.taxonomy_cleaning_flags = [i.strip() for i in get_property(config_filepaths, 'taxonomy', 'cleaning_flags').split(',')]
    config.taxonomy_cleaning_flags.sort()
    config.collections = [i.strip() for i in get_property(config_filepaths, 'synthesis', 'collections').strip().split()]
    config.root_ott_id = get_property(config_filepaths, 'synthesis', 'root_ott_id')
    config.peyotl_root = get_property(config_filepaths, 'opentree', 'peyotl')
    config.phylesystem_root = get_property(config_filepaths, 'opentree', 'phylesystem')
    config.collections_root = get_property(config_filepaths, 'opentree', 'collections')
    config.ott_root = get_property(config_filepaths, 'opentree', 'ott')
    ott_version_file = os.path.join(config.ott_root, 'version.txt')
    config.ott_version = codecs.open(ott_version_file, 'rU', encoding='utf-8').read().strip()
    ott_major_pat = re.compile('^([0-9.]+)[a-z]?.*')
    m = ott_major_pat.match(config.ott_version)
    if m:
        config.ott_major_minor_version = m.group(1)
    else:
        config.ott_major_minor_version = 'NOT built using OTT'
    return config

def get_otc_version():
    git_sha, version, boost_version = ['unknown']*3
    try:
        out = subprocess.check_output('otc-version-reporter')
        try:
            git_sha = re.compile('git_sha *= *([a-zA-Z0-9]+)').search(out).group(1)
        except:
            pass
        try:
            version = re.compile('version *= *([-._a-zA-Z0-9]+)').search(out).group(1)
        except:
            pass
        try:
            boost_version = re.compile('BOOST_LIB_VERSION *= *([-._a-zA-Z0-9]+)').search(out).group(1)
        except:
            pass
    except:
        pass
    return git_sha, version, boost_version

def get_git_sha_from_dir(d):
    head = os.path.join(d, '.git', 'HEAD')
    head_branch_ref_frag = open(head, 'rU').read().split()[1]
    head_branch_ref = os.path.join(d, '.git', head_branch_ref_frag)
    return open(head_branch_ref, 'rU').read().strip()


def get_peyotl_version(peyotl_dir):
    peyotl_version, peyotl_sha = ['unknown'] * 2
    try:
        peyotl_version = peyotl.__version__
    except:
        pass
    try:
        peyotl_sha = get_git_sha_from_dir(peyotl_dir)
    except:
        pass
    return peyotl_version, peyotl_sha

def get_runtime_configuration(config_filepath):
    config = parse_config(config_filepath)
    x = get_otc_version()
    config.otc_sha, config.otc_version, config.otc_boost_version = x
    x = get_peyotl_version(config.peyotl_root)
    config.peyotl_version, config.peyotl_sha = x
    config.propinquity_sha = get_git_sha_from_dir(propinquity_dir)
    return config

def stripped_nonempty_lines(fn):
    x = []
    with open(fn, 'rU') as inp:
        for line in inp:
            ls = line.strip()
            if ls:
                x.append(ls)
    return x

def parse_subproblem_solutions_degree_dist(fn):
    x = []
    for p in gen_degree_dist(fn):
        fn, dd_list = p
        assert dd_list[0][0] == 0
        num_leaves = dd_list[0][1]
        num_forking = 0
        for el in dd_list:
            if el[0] > 1:
                num_forking += el[1]
        x.append((num_leaves, num_forking, fn))
    x.sort(reverse=True)
    x = [(i[2], i[0], i[1]) for i in x]
    return x

def gen_degree_dist(fn):
    header_pat = re.compile(r'Out-degree\S+Count')
    with open(fn, 'rU') as inp:
        lines = stripped_nonempty_lines(fn)
        rfn = None
        expecting_header = False
        dd = []
        for n, line in enumerate(inp):
            ls = line.strip()
            if not ls:
                continue
            if expecting_header:
                if header_pat.match(ls):
                    raise ValueError('expecting a header at line {}, but found "{}"'.format(1 + n, ls))
                expecting_header = False
            else:
                if ls.endswith('.tre'):
                    if rfn:
                        yield rfn, dd
                    dd = []
                    rfn = ls
                    expecting_header = True
                else:
                    row = ls.split()
                    assert len(row) == 2
                    dd.append([int(i) for i in row])
        if rfn:
            yield rfn, dd

def write_as_json(obj, out_stream):
    json.dump(obj, out_stream, indent=2, sort_keys=True, separators=(',', ': '))
    out_stream.write('\n')

def render_top_index(container, template, html_out, json_out):
    write_as_json({'config' : container.config.__dict__}, json_out)
    html_out.write(template(config=container.config,
                            phylo_input=container.phylo_input,
                            exemplified_phylo=container.exemplified_phylo))

# Note: these render commands could in theory be replaced by Jim with cooler HTML output or something.
def render_phylo_input_index(container, template, html_out, json_out):
    write_as_json({'phylo_input' : container.phylo_input.__dict__}, json_out)
    html_out.write(template(phylo_input=container.phylo_input))

def render_phylo_snapshot_index(container, template, html_out, json_out):
    html_out.write(template(phylo_input=container.phylo_input,
                            phylo_snapshot=container.phylo_snapshot))

def render_cleaned_ott_index(container, template, html_out, json_out):
    html_out.write(template(cleaned_ott=container.cleaned_ott))
def render_cleaned_phylo_index(container, template, html_out, json_out):
    html_out.write(template(phylo_input=container.phylo_input,
                            phylo_snapshot=container.phylo_snapshot,
                            exemplified_phylo=container.exemplified_phylo))
def render_exemplified_phylo_index(container, template, html_out, json_out):
    write_as_json({'exemplified_phylo' : container.exemplified_phylo.__dict__}, json_out)
    html_out.write(template(exemplified_phylo=container.exemplified_phylo))
def render_subproblems_index(container, template, html_out, json_out):
    write_as_json({'subproblems' : container.subproblems.__dict__}, json_out)
    html_out.write(template(subproblems=container.subproblems))
def render_subproblem_solutions_index(container, template, html_out, json_out):
    write_as_json({'subproblem_solutions' : container.subproblem_solutions.__dict__}, json_out)
    html_out.write(template(subproblems=container.subproblems,
                            subproblem_solutions=container.subproblem_solutions))
def render_grafted_solution_index(container, template, html_out, json_out):
    html_out.write(template(subproblems=container.subproblems))
def render_labelled_supertree_index(container, template, html_out, json_out):
    html_out.write(template(unprune_stats=container.labelled_supertree.unprune_stats,
                            non_monophyletic_taxa=container.labelled_supertree.non_monophyletic_taxa))
def render_annotated_supertree_index(container, template, html_out, json_out):
    html_out.write(template())
def render_assessments_index(container, template, html_out, json_out):
    html_out.write(template(assessments=container.assessments))
# def render_broken_taxa_report(container, template, html_out, json_out):
#     html_out.write(template(broken_taxa=container.broken_taxa))

def node_label2obj(nl):
    '''Node labels in cleaned input trees are quirky, this tries to parse them...'''
    el = {'label': nl}
    if not nl:
        # Resolution of a polytomy during otc-uncontested-decompose can result
        # in new nodes with empty labels
        return el
    ott_id = None
    name = None
    node_id = None
    if nl.endswith(' '):
        # Most nodes internals have no OTT Id so they end with a space
        nnl = nl[:-1]
        sn = nnl.split('_')
        assert len(sn) > 1
        name = '_'.join(sn[:-1])
        node_id = sn[-1]
    else:
        delim = '_'
        sn = nl.split(delim)
        if len(sn) > 1:
            if len(sn) <= 2:
                sys.exit('problem:\n"{}"\n'.format(nl))
            assert len(sn) > 2
        else:
            # Some have "nodeID ottID"
            delim = ' '
            sn = nl.split(delim)
        if len(sn) > 2:
            name = delim.join(sn[:-2])
            node_id = sn[-2]
            ott_id = sn[-1]
        else:
            if len(sn) == 1:
                ott_id = sn
            else:
                assert len(sn) == 2
                node_id, ott_id = sn
    if ott_id:
        el['ott'] = ott_id
    if name:
        el['name'] = name
    if node_id:
        el['node_id'] = node_id
    return el

class DocGen(object):
    def __init__(self, propinquity_dir, supertree_output_dir, config_filepath):
        self.top_output_dir = supertree_output_dir
        self.propinquity_dir = propinquity_dir
        subprocess.call(['make', os.path.join(self.top_output_dir, 'assessments', 'summary.json')])
        templates_dir = os.path.join(propinquity_dir, 'doc', 'templates')
        self.templates = PageTemplateLoader(templates_dir)
        self.config = get_runtime_configuration(config_filepath)
        self.phylo_input = self.read_phylo_input()
        self.phylo_snapshot = self.read_phylo_snapshot()
        self.cleaned_ott = self.read_cleaned_ott()
        self.exemplified_phylo = self.read_exemplified_phylo()
        self.subproblem_solutions = self.read_subproblem_solutions()
        self.subproblems = self.read_subproblems()
        self.labelled_supertree = self.read_labelled_supertree()
        self.assessments = self.read_assessments()
        #self.broken_taxa = self.read_broken_taxa()
    def read_assessments(self):
        d = os.path.join(self.top_output_dir, 'assessments')
        blob = Extensible()
        blob.assessments = read_as_json(os.path.join(d, 'summary.json'))
        blob.categories_of_checks = list(blob.assessments.keys())
        blob.categories_of_checks.sort()
        blob.categories_of_checks_with_errors = []
        for k, v in blob.assessments.items():
            if v['result'] != 'OK':
                blob.categories_of_checks_with_errors.append(k)
        blob.categories_of_checks_with_errors.sort()
        return blob
    # def read_broken_taxa(self):
    #     d = os.path.join(self.top_output_dir, 'labelled_supertree')
    #     blob = Extensible()
    #     blob.assessments = read_as_json(os.path.join(d, 'broken_taxa.json'))

    def read_labelled_supertree(self):
        d = os.path.join(self.top_output_dir, 'labelled_supertree')
        p = 'labelled_supertree_out_degree_distribution.txt'
        lsodd = os.path.join(d, p)
        subprocess.call(['make', lsodd])
        subprocess.call(['make', os.path.join(d, 'labelled_supertree_ottnames.tre')])
        assert(os.path.exists(lsodd))
        blob = Extensible()
        blob.unprune_stats = read_as_json(os.path.join(d, 'input_output_stats.json'))
        blob.non_monophyletic_taxa = read_as_json(os.path.join(d, 'broken_taxa.json'))
        if blob.non_monophyletic_taxa['non_monophyletic_taxa'] is None:
            blob.non_monophyletic_taxa['non_monophyletic_taxa'] = {}
        return blob
    def read_subproblem_solutions(self):
        d = os.path.join(self.top_output_dir, 'subproblem_solutions')
        sdd = os.path.join(d, 'solution-degree-distributions.txt')
        subprocess.call(['make', sdd])
        assert(os.path.exists(sdd))
        blob = Extensible()
        blob.subproblem_num_leaves_num_internal_nodes = parse_subproblem_solutions_degree_dist(sdd)
        return blob
    def read_subproblems(self):
        d = os.path.join(self.top_output_dir, 'subproblems')
        blob = Extensible()
        conf_tax_json_fp = os.path.join(d, 'contesting-trees.json')
        conf_tax_info = read_as_json(conf_tax_json_fp)
        if not conf_tax_info:
            conf_tax_info = {}
        externalized_conf_tax_info = {}
        for ott_id, tree2node_info_list in conf_tax_info.items():
            tr_ob_li = []
            if ott_id.startswith('ott'):
                ott_id = ott_id[3:]
            externalized_conf_tax_info[ott_id] = tr_ob_li
            for study_tree_fn, node_info_list in tree2node_info_list.items():
                study_id, tree_id = propinquity_fn_to_study_tree(study_tree_fn)
                cf_nl = []
                tre_obj = {'study_id': study_id,
                           'tree_id': tree_id,
                           'tree_filename': study_tree_fn,
                           'conflicting_nodes': cf_nl}
                tr_ob_li.append(tre_obj)
                if len(node_info_list) < 2:
                    raise RuntimeError('read_subproblems < 2 node info elements for taxon ID = {}'.format(ott_id))
                for node_info in node_info_list:
                    rcfn = node_info['children_from_taxon']
                    cfn = [node_label2obj(i) for i in rcfn]
                    el = {'parent': node_label2obj(node_info['parent']),
                          'children_from_taxon': cfn
                         }
                    cf_nl.append(el)
        blob.contested_taxa = externalized_conf_tax_info
        blob.tree_files = stripped_nonempty_lines(os.path.join(d, 'subproblem-ids.txt'))
        id2num_leaves = {}
        for el in self.subproblem_solutions.subproblem_num_leaves_num_internal_nodes:
            id2num_leaves[el[0]] = el[1]
        by_num_phylo = []
        by_input = {}
        for s in blob.tree_files:
            assert s.endswith('.tre')
            pref = s[:-4]
            assert pref.startswith('ott')
            tree_name_file = os.path.join(d, pref + '-tree-names.txt')
            phylo_inputs = []
            for i in stripped_nonempty_lines(tree_name_file):
                x = i[:-4] if i.endswith('.tre') else i
                phylo_inputs.append(i)
                if x != 'TAXONOMY':
                    by_input.setdefault(x, []).append(pref)
            npi = len(phylo_inputs)
            by_num_phylo.append((npi, int(pref[3:]), s, phylo_inputs))
        by_num_phylo.sort(reverse=True)
        blob.sorted_by_num_phylo_inputs = [[i[2], i[3], id2num_leaves[i[2]]] for i in by_num_phylo]
        by_input = [(len(v), k, v) for k, v in by_input.items()]
        by_input.sort(reverse=True)
        blob.input_and_subproblems_sorted = [[i[1], i[2]] for i in by_input]
        return blob
    def read_cleaned_ott(self):
        blob = Extensible()
        d = os.path.join(self.top_output_dir, 'cleaned_ott')
        o = read_as_json(os.path.join(d, 'cleaned_ott.json'))
        for k, v in o.items():
            setattr(blob, k, v)
            if k == 'flags_to_prune':
                v.sort()
        blob.root_ott_id = self.config.root_ott_id
        return blob
    def read_exemplified_phylo(self):
        d = os.path.join(self.top_output_dir, 'exemplified_phylo')
        x = read_as_json(os.path.join(d, 'exemplified_log.json'))
        tx = x['taxa_exemplified']
        if not tx:
            tx = {}
        by_source_tree = {}
        for ott_id, exdict in tx.items():
            tm = exdict['trees_modified']
            for tree in tm:
                key = '.'.join(tree.split('.')[:-1])
                by_source_tree.setdefault(key, []).append(ott_id)
        for v in by_source_tree.values():
            v.sort()
        ptdd = os.path.join(d, 'pruned_taxonomy_degree_distribution.txt')
        subprocess.call(['make', ptdd])
        assert(os.path.exists(ptdd))
        ddlines = [i.split() for i in stripped_nonempty_lines(ptdd) if i.split()[0] == '0']
        assert(len(ddlines) == 1)
        leaf_line = ddlines[0] # should b
        assert(len(leaf_line) == 2)
        blob = Extensible()
        blob.num_leaves_in_exemplified_taxonomy = int(leaf_line[1])
        blob.taxa_exemplified = tx
        blob.source_tree_to_ott_id_exemplified_list = by_source_tree
        f = os.path.join(d, 'nonempty_trees.txt')
        blob.nonempty_tree_filenames = stripped_nonempty_lines(f)
        blob.nonempty_trees = [propinquity_fn_to_study_tree(i) for i in blob.nonempty_tree_filenames]
        return blob
    def read_phylo_input(self):
        blob = Extensible()
        blob.directory = os.path.join(self.top_output_dir, 'phylo_input')
        blob.study_tree_pair_file = os.path.join(blob.directory, 'study_tree_pairs.txt')
        x = stripped_nonempty_lines(blob.study_tree_pair_file)
        blob.study_id_tree_id_pairs = [propinquity_fn_to_study_tree(i, strip_extension=False) for i in x]
        return blob
    def read_phylo_snapshot(self):
        blob = Extensible()
        blob.directory = os.path.join(self.top_output_dir, 'phylo_snapshot')
        blob.git_shas_file = os.path.join(blob.directory, 'git_shas.txt')
        blob.collections_git_shas_file = os.path.join(blob.directory, 'collections_git_shas.txt')
        subprocess.call(['make', blob.collections_git_shas_file])
        blob.collections_git_shas = stripped_nonempty_lines(blob.collections_git_shas_file)
        blob.git_shas = stripped_nonempty_lines(blob.git_shas_file)
        return blob
    def _cham_out(self, fn):
        fp = os.path.join(self.top_output_dir, fn)
        fo = codecs.open(fp, 'w', encoding='utf-8')
        return fo
    def render(self):
        src_dest_list = ((render_top_index, 'top_index.pt', 'index'),
                         (render_phylo_input_index, 'phylo_input_index.pt', 'phylo_input/index'),
                         (render_phylo_snapshot_index, 'phylo_snapshot_index.pt', 'phylo_snapshot/index'),
                         (render_cleaned_phylo_index, 'cleaned_phylo_index.pt', 'cleaned_phylo/index'),
                         (render_cleaned_ott_index, 'cleaned_ott_index.pt', 'cleaned_ott/index'),
                         (render_exemplified_phylo_index, 'exemplified_phylo_index.pt', 'exemplified_phylo/index'),
                         (render_subproblems_index, 'subproblems_index.pt', 'subproblems/index'),
                         (render_subproblem_solutions_index, 'subproblem_solutions_index.pt', 'subproblem_solutions/index'),
                         (render_grafted_solution_index, 'grafted_solution_index.pt', 'grafted_solution/index'),
                         (render_labelled_supertree_index, 'labelled_supertree_index.pt', 'labelled_supertree/index'),
                         (render_annotated_supertree_index, 'annotated_supertree_index.pt', 'annotated_supertree/index'),
                         (render_assessments_index, 'assessments_index.pt', 'assessments/index'),
                        )
        for func, template_path, prefix in src_dest_list:
            html_path = prefix + '.html'
            json_path = prefix + '.json'
            t = self.templates[template_path]
            html_o = self._cham_out(html_path)
            json_o = self._cham_out(json_path)
            try:
                func(self, t, html_o, json_o)
            finally:
                html_o.close()
                json_o.close()


if __name__ == '__main__':
    import argparse
    bin_dir, SCRIPT_NAME = os.path.split(__file__)
    propinquity_dir = os.path.dirname(bin_dir)
    parser = argparse.ArgumentParser(prog=SCRIPT_NAME, description='Writer of html files documenting the synthesis')
    parser.add_argument('--config',
                        default='config',
                        type=str,
                        required=False,
                        help='filepath of the config file (default is "config")')
    parser.add_argument('dir',
                        default='.',
                        type=str,
                        nargs='?',
                        help='prefix for inputs')
    args = parser.parse_args(sys.argv[1:])
    prefix_dir = args.dir
    dg = DocGen(propinquity_dir, prefix_dir, args.config)
    dg.render()
