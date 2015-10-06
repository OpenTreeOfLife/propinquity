#!/usr/bin/env python
try:
    import configparser  # pylint: disable=F0401
except ImportError:
    import ConfigParser as configparser
import sys
import os

_SCRIPT_NAME = os.path.split(sys.argv[0])[-1]

def errstream(msg):
    sys.stderr.write('{n}: ERROR: {m}\n'.format(n=_SCRIPT_NAME, m=msg))

if __name__ == '__main__':
    import argparse
    import os
    description = 'Reads the config file, validates options, and supports writing out options individually'
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
    p = args.property
    if p is None:
        sys.exit(0)
    if p == 'cleaning_flags':
        print clean_ott_flags