#!/usr/bin/env python
import sys
import os

# setup.py largely based on
#   http://hynek.me/articles/sharing-your-labor-of-love-pypi-quick-and-dirty/
# Also see Jeet Sukumaran's DendroPy

###############################################################################
# setuptools/distutils/etc. import and configuration
try:
    import ez_setup
    try:
        ez_setup_path = " ('" + os.path.abspath(ez_setup.__file__) + "')"
    except OSError:
        ez_setup_path = ""
    sys.stderr.write("using ez_setup%s\n" % ez_setup_path)
    ez_setup.use_setuptools()
    import setuptools

    try:
        setuptools_path = " ('" + os.path.abspath(setuptools.__file__) + "')"
    except OSError:
        setuptools_path = ""
    sys.stderr.write("using setuptools%s\n" % setuptools_path)
    from setuptools import setup
except ImportError as e:
    sys.stderr.write("using distutils\n")
    from distutils.core import setup


PACKAGES = ['propinquity', ]
EXTRA_KWARGS = {"include_package_data": True,
                "test_suite": "propinquity.test",
                "zip_safe": True,
                "scripts":  [],
               }
ENTRY_POINTS = {}

###############################################################################
# setuptools/distuils command extensions
try:
    from setuptools import Command
except ImportError:
    sys.stderr.write("setuptools.Command could not be imported: setuptools extensions not available\n")
else:
    sys.stderr.write("setuptools command extensions are available\n")
    command_hook = "distutils.commands"
    ENTRY_POINTS[command_hook] = []

setup(
    name='propinquity',
    version='2.0.dev1',  # sync with __version__ in peyotl/__init__.py
    description='Workflow for building synthetic phylogenetic trees for the Open Tree of Life project',
    long_description=(open('README.md').read()),
    url='https://github.com/OpenTreeOfLife/propinquity',
    license='BSD',
    author='Ben D. Redelings and Mark T. Holder',
    py_modules=['propinquity'],
    install_requires=["peyutil>=0.0.4",
                      "nexson>=0.0.4",
                      "peyotl>=1.0.1dev",
                      "chameleon>=3.8.1",
                      "DendroPy>=4.4.0",
                     ],
    packages=PACKAGES,
    package_data={'propinquity': ['static/*',
                                  'static/*/*.html',
                                  'static/*/*.md',
                                  'static/*/*/*.md',
                                  'static/templates/*.pt',
                                  ]},
    entry_points=ENTRY_POINTS,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.3',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
    ],
    **EXTRA_KWARGS
)
