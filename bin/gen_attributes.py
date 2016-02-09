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
    with open('phylo_snapshot/concrete_rank_collection.json') as data_file:
        snapshot_data = json.load(data_file)
    studies = set()
    for study_tree_object in snapshot_data["decisions"]:
        study_id = study_tree_object["studyID"]
        studies.add(study_id)
    return len(studies)

def num_trees():
    with open('phylo_snapshot/concrete_rank_collection.json') as data_file:
        snapshot_data = json.load(data_file)
    trees = set()
    for study_tree_object in snapshot_data["decisions"]:
        study_id = study_tree_object["studyID"]
        tree_id = study_tree_object["treeID"]
        name = study_id + "_" + tree_id # This line seems a bit arbitrary.
        trees.add(name)
    return len(trees)

def extract_source_id_map():
    source_id_map = {}
    with open('phylo_snapshot/concrete_rank_collection.json') as data_file:
        snapshot_data = json.load(data_file)
    for study_tree_object in snapshot_data["decisions"]:
        study_id = study_tree_object["studyID"]
        tree_id = study_tree_object["treeID"]
        git_sha = study_tree_object["SHA"]
        name = study_id + "_" + tree_id # This line seems a bit arbitrary.
        source_id_map[name] = {"study_id":study_id, "tree_id":tree_id, "git_sha":git_sha}
    return source_id_map

def extract_version(args):
    with codecs.open(os.path.join(args.ott_dir, 'version.txt'), 'r', encoding='utf-8') as fo:
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

if __name__ == '__main__':
    import argparse
    import sys
    import os
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
    parser.add_argument('--ott-dir',
                        default=os.environ['OTT_DIR'],
                        type=str,
                        required=False,
                        help='directory containing ott files (e.g "taxonomy.tsv")')
    args = parser.parse_args(sys.argv[1:])
    ott_dir = args.ott_dir
    document = {}
    document["date_completed"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    document["tree_id"] = "opentree4.1"
    document["taxonomy_version"] = extract_version(args)
    document["run_time"] = "30 minutes"
    document["root_taxon_name"] = root_taxon_name(args, ott_dir)
    document["generated_by"] = [
        {"name":"propinquity",
         "version":"x",
         "git_sha":"aaa",
         "url":"link",
         "invocation":"cmd"},
        {"name":"peyotl",
         "version":"x",
         "git_sha":"aaa",
         "url":"link",
         "invocation":"cmd"},
        {"name":"otcetera",
         "version":"x",
         "git_sha":"aaa",
         "url":"link",
         "invocation":"cmd"},
    ]
    document["filtered_flags"] = extract_filtered_flags(args)
    document["source_id_map"] = extract_source_id_map()
    document["num_source_trees"] = num_trees()
    document["num_source_studies"] = num_studies()

    print json.dumps(document,indent=4)
