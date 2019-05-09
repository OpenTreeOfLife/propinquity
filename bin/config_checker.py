#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

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
    DEFAULT_CONFIG_LOCATION = os.path.expanduser('~/.opentree')
    DEFAULT_CONFIG_LOCATION = os.environ.get('OTC_CONFIG', DEFAULT_CONFIG_LOCATION)
    description = 'Reports the value of a option from the first config file that contains it'
    parser = argparse.ArgumentParser(prog='config_checker.py', description=description)
    parser.add_argument('property',
                        default=None,
                        nargs=1,
                        type=str,
#                        choices=('cleaning_flags', ),
                        help='which property value should be printed, as in taxonomy.cleaning_flags.')
    parser.add_argument('configs',
                        default=['config'],
                        nargs = '*',
                        type=str,
                        help='filepaths for a series of config files (default is ["config","~/.opentree"])')
    parser.add_argument('--default',
                        default=None,
                        type=str,
                        required=False,
                        help='What value should be returned if no config files contain it.')
    args = parser.parse_args(sys.argv[1:])

    prop = args.property[0]
    props = prop.split('.')
    if (len(props) != 2):
        errstream("Property '{}' should be of the form section.name".format(prop))
    if os.path.exists(DEFAULT_CONFIG_LOCATION):
        cf = list(args.configs) + [DEFAULT_CONFIG_LOCATION]
    else:
        cf = arg.configs
    # Look through the listed files for the the property
    for config in cf:
        p = configparser.SafeConfigParser()
        try:
            p.read(config)
        except:
            errstream('problem reading "{}"'.format(cf))
            raise

        try:
            value = p.get(props[0], props[1]).strip()
            print(value)
            sys.exit(0)
        except SystemExit:
            sys.exit(0)
        except:
            continue

    # If none of the files have the property, return the default, if any
    if args.default is not None:
        print(args.default)
        sys.exit(0)
        
    # If no default complain that none of the files have it
    errstream('Could not find a [{}] section with a valid "{}" setting.'.format(props[0],props[1]))
    sys.exit(1)
