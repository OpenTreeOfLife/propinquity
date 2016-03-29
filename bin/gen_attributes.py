#!/usr/bin/env python
# See https://github.com/OpenTreeOfLife/opentree/wiki/Open-Tree-of-Life-APIs-v3#synthetic-tree
try:
    import configparser  # pylint: disable=F0401
except ImportError:
    import ConfigParser as configparser
import json
import datetime
import os
import codecs

def num_studies():
    with open(os.path.join(out_dir, 'phylo_snapshot/concrete_rank_collection.json')) as data_file:
        snapshot_data = json.load(data_file)
    studies = set()
    for study_tree_object in snapshot_data["decisions"]:
        study_id = study_tree_object["studyID"]
        studies.add(study_id)
    return len(studies)

def num_trees():
    with open(os.path.join(out_dir, 'phylo_snapshot/concrete_rank_collection.json')) as data_file:
        snapshot_data = json.load(data_file)
    trees = set()
    for study_tree_object in snapshot_data["decisions"]:
        study_id = study_tree_object["studyID"]
        tree_id = study_tree_object["treeID"]
        name = study_id + "@" + tree_id # Using @, which will not be in treeid
        trees.add(name)
    return len(trees)

def extract_source_id_map():
    source_id_map = {}
    with open(os.path.join(out_dir, 'phylo_snapshot/concrete_rank_collection.json')) as data_file:
        snapshot_data = json.load(data_file)
    for study_tree_object in snapshot_data["decisions"]:
        study_id = study_tree_object["studyID"]
        tree_id = study_tree_object["treeID"]
        git_sha = study_tree_object["SHA"]
        name = study_id + "@" + tree_id # Using @, which will not be in treeid
        source_id_map[name] = {"study_id":study_id, "tree_id":tree_id, "git_sha":git_sha}
    return source_id_map

def ott_version(ott_dir):
    with codecs.open(os.path.join(ott_dir, 'version.txt'), 'r', encoding='utf-8') as fo:
        version = fo.read().strip()
    return version

def extract_filtered_flags(args):
    cf = args.config
    p = configparser.SafeConfigParser()
    try:
        p.read(cf)
    except:
        errstream('problem reading "{}"'.format(cf))
        raise
    try:
        clean_ott_flags = p.get('taxonomy', 'cleaning_flags').strip()
    except:
        errstream('Could not find a [taxonomy] section with a valid "cleaning_flags" setting.')
        raise
    return clean_ott_flags.split(',')

def root_taxon_name(args, ott_dir):
    import subprocess
    import os
    cf = args.config
    p = configparser.SafeConfigParser()
    try:
        p.read(cf)
    except:
        errstream('problem reading "{}"'.format(cf))
        raise
    try:
        root_ott_id = p.get('synthesis', 'root_ott_id').strip()
    except:
        errstream('Could not find a [synthesis] section with a valid "root_ott_id" setting.')
        raise
#    root_name = os.system("otc-taxonomy-parser -N",str(root_ott_id)])
    FNULL = open(os.devnull, 'w')
    proc = subprocess.Popen(["otc-taxonomy-parser", ott_dir,"-N",str(root_ott_id)], stdout=subprocess.PIPE, stderr=FNULL)
    root_name = proc.communicate()[0].strip()
    return root_name

def get_git_sha_from_dir(d):
    head = os.path.join(d, '.git', 'HEAD')
    head_branch_ref_frag = open(head, 'rU').read().split()[1]
    head_branch_ref = os.path.join(d, '.git', head_branch_ref_frag)
    return open(head_branch_ref, 'rU').read().strip()


def get_peyotl_version(peyotl_dir):
    peyotl_version, peyotl_sha = ['unknown'] * 2
    try:
        import peyotl
        peyotl_version = peyotl.__version__
    except:
        pass
    try:
        peyotl_sha = get_git_sha_from_dir(peyotl_dir)
    except:
        raise
        pass
    return peyotl_version, peyotl_sha

def get_otc_version():
    import subprocess
    import re
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

def get_synth_id(config_filename):
    p = configparser.SafeConfigParser()
    try:
        p.read(config_filename)
    except:
        errstream('problem reading "{}"'.format(config_filename))
        raise
    try:
        synth_id = p.get('synthesis', 'synth_id').strip()
    except:
        return '<UNKNOWN>'
    return synth_id

if __name__ == '__main__':
    import argparse
    import sys
    import os
    errstream = sys.stderr
    description = 'Write a JSON file with some of synthesis tree attributes'
    parser = argparse.ArgumentParser(prog='suppress-dubious', description=description)
    parser.add_argument('--config',
                        default='config',
                        type=str,
                        required=False,
                        help='filepath of the config file (default is "config")')
    parser.add_argument('--property',
                        default=None,
                        type=str,
                        required=False,
                        choices=('cleaning_flags', ),
                        help='which property value should be printed.')
    parser.add_argument('dir',
                        default='.',
                        type=str,
                        nargs='?',
                        help='prefix for inputs')
    args = parser.parse_args(sys.argv[1:])

    parsed_config = configparser.SafeConfigParser()
    try:
        parsed_config.read(args.config)
    except:
        errstream('problem reading "{}"'.format(args.config))
        raise

    ott_dir = parsed_config.get('opentree', 'ott')
    out_dir = args.dir

    otc_sha, otc_version, otc_boost_version = get_otc_version()

    peyotl_root = parsed_config.get('opentree', 'peyotl')
    peyotl_version, peyotl_sha = get_peyotl_version(peyotl_root)
    
    document = {}
    document["date_completed"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    synth_id = get_synth_id(args.config)

    propinquity_sha = 'unknown'
    try:
        bin_dir, SCRIPT_NAME = os.path.split(__file__)
        propinquity_dir = os.path.dirname(bin_dir)
        propinquity_sha = get_git_sha_from_dir(propinquity_dir)
    except:
        pass
    
    document["tree_id"] = synth_id
    document["synth_id"] = synth_id
    document["taxonomy_version"] = ott_version(ott_dir)
    #document["run_time"] = "15 minutes"
    document["root_taxon_name"] = root_taxon_name(args, ott_dir)
    document["generated_by"] = [
        {"name":"propinquity",
         "version":"N/A",
         "git_sha":propinquity_sha,
         "url":"https://github.com/OpenTreeOfLife/propinquity",
         "invocation":"cmd"},
        {"name":"peyotl",
         "version":peyotl_version,
         "git_sha":peyotl_sha,
         "url":"http://opentreeoflife.github.io/peyotl",
         "invocation":"N/A"},
        {"name":"otcetera",
         "version":otc_version,
         "git_sha":otc_sha,
         "url":"https://github.com/OpenTreeOfLife/otcetera",
         "invocation":"N/A"},
    ]
    document["filtered_flags"] = extract_filtered_flags(args)
    document["source_id_map"] = extract_source_id_map()
    document["num_source_trees"] = num_trees()
    document["num_source_studies"] = num_studies()

    print json.dumps(document,indent=4)
