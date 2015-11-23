#!/usr/bin/env python
try:
    import configparser  # pylint: disable=F0401
except ImportError:
    import ConfigParser as configparser
import json
import datetime
import os
import codecs

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
    cf = args.config
    p = configparser.RawConfigParser()
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
    with codecs.open(os.path.join(args.ott_dir, 'version.txt'), 'r', encoding='utf-8') as fo:
        version = fo.read().strip()

    document = {}
    document["date_completed"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    document["tree_id"] = "opentree4.1"
    document["taxonomy_version"] = version
    document["run_time"] = "30 minutes"
    document["root_taxon_name"] = "cellular organisms"
    document["generated_by"] = "propinquity"
    document["filtered_flags"] = clean_ott_flags.split(',')

    print json.dumps(document,indent=4)

    
