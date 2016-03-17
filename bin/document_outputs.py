#!/usr/bin/env python
'''Writes html files that explains the synthesis run that was completed
'''

from __future__ import absolute_import, division, print_function, unicode_literals
try:
    from chameleon import PageTemplateLoader
except:
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


def parse_config(config_filepath):
    parsed_config = configparser.SafeConfigParser()
    try:
        parsed_config.read(config_filepath)
    except:
        errstream('problem reading "{}"'.format(config_filepath))
        raise
    config = Extensible()
    config.config_filepath = os.path.abspath(config_filepath)
    config.taxonomy_cleaning_flags = [i.strip() for i in parsed_config.get('taxonomy', 'cleaning_flags').split(',')]
    config.taxonomy_cleaning_flags.sort()
    config.collections = [i.strip() for i in parsed_config.get('synthesis', 'collections').strip().split()]
    config.root_ott_id = parsed_config.getint('synthesis', 'root_ott_id')
    config.peyotl_root = parsed_config.get('opentree', 'peyotl')
    config.phylesystem_root = parsed_config.get('opentree', 'phylesystem')
    config.collections_root = parsed_config.get('opentree', 'collections')
    config.ott_root = parsed_config.get('opentree', 'ott')
    ott_version_file = os.path.join(config.ott_root, 'version.txt')
    config.ott_version = codecs.open(ott_version_file, 'rU', encoding='utf-8').read().strip()
    ott_major_pat = re.compile('^([0-9.]+)[a-z]?.*')
    m = ott_major_pat.match(config.ott_version)
    config.ott_major_minor_version = m.group(1)
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
def get_peyotl_version(peyotl_dir):
    peyotl_version, peyotl_sha = ['unknown'] * 2
    try:
        peyotl_version = peyotl.__version__
    except:
        pass
    try:
        head = os.path.join(peyotl_dir, '.git', 'HEAD')
        head_branch_ref_frag = open(head, 'rU').read().split()[1]
        head_branch_ref = os.path.join(peyotl_dir, '.git', head_branch_ref_frag)
        peyotl_sha = open(head_branch_ref, 'rU').read().strip()
    except:
        pass
    return peyotl_version, peyotl_sha

def get_runtime_configuration(config_filepath):
    config = parse_config(config_filepath)
    x = get_otc_version() 
    config.otc_sha, config.otc_version, config.otc_boost_version = x
    x = get_peyotl_version(config.peyotl_root)
    config.peyotl_version, config.peyotl_sha = x
    return config

def stripped_nonempty_lines(fn):
    x = []
    with open(fn, 'rU') as inp:
        for line in inp:
            ls = line.strip()
            if ls:
                x.append(ls)
    return x    

def write_as_json(obj, out_stream):
    json.dump(obj, out_stream, indent=2, sort_keys=True, separators=(',', ': '))
    out_stream.write('\n')

def render_top_index(container, template, html_out, json_out):
    write_as_json({'config' : container.config.__dict__}, json_out)
    html_out.write(template(config=container.config,
                            phylo_input=container.phylo_input,
                            exemplified_phylo=container.exemplified_phylo))

def render_phylo_input_index(container, template, html_out, json_out):
    write_as_json({'phylo_input' : container.phylo_input.__dict__}, json_out)
    html_out.write(template(phylo_input=container.phylo_input))

def render_phylo_snapshot_index(container, template, html_out, json_out):
    html_out.write(template(phylo_input=container.phylo_input,
                            phylo_snapshot=container.phylo_snapshot))

def render_cleaned_phylo_index(container, template, html_out, json_out):
    html_out.write(template(phylo_input=container.phylo_input,
                            phylo_snapshot=container.phylo_snapshot,
                            exemplified_phylo=container.exemplified_phylo))
def render_exemplified_phylo_index(container, template, html_out, json_out):
    write_as_json({'exemplified_phylo' : container.exemplified_phylo.__dict__}, json_out)
    html_out.write(template(exemplified_phylo=container.exemplified_phylo))

class DocGen(object):
    def __init__(self, propinquity_dir, config_filepath):
        self.top_output_dir = propinquity_dir #TEMP should be read from config
        self.propinquity_dir = propinquity_dir
        templates_dir = os.path.join(propinquity_dir, 'doc', 'templates')
        self.templates = PageTemplateLoader(templates_dir)
        self.config = get_runtime_configuration(config_filepath)
        self.phylo_input = self.read_phylo_input()
        self.phylo_snapshot = self.read_phylo_snapshot()
        self.exemplified_phylo = self.read_exemplified_phylo()
    def read_exemplified_phylo(self):
        d = os.path.join(self.top_output_dir, 'exemplified_phylo')
        x = read_as_json(os.path.join(d, 'exemplified_log.json'))
        tx = x['taxa_exemplified']
        by_source_tree = {}
        for ott_id, exdict in tx.items():
            tm = exdict['trees_modified']
            for tree in tm:
                key = '.'.join(tree.split('.')[:-1])
                by_source_tree.setdefault(key, []).append(ott_id)
        for v in by_source_tree.values():
            v.sort()
        ptdd = os.path.join(d, 'pruned_taxonomy_degree_distribution.txt')
        if not os.path.exists(ptdd):
            subprocess.call(['make', 'exemplified_phylo/pruned_taxonomy_degree_distribution.txt'])
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
                         (render_exemplified_phylo_index, 'exemplified_phylo_input.pt', 'exemplified_phylo/index'),
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
    args = parser.parse_args(sys.argv[1:])
    dg = DocGen(propinquity_dir, args.config)
    dg.render()

