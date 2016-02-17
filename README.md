# propinquity

## Configuration file

Before you set up other prequisite software, you'll need to initialize your
`config` file.  You do this by copying an example config file:

    $ cd propinquity
    $ cp config.example config

This config file contains sections, each of which contain settings for variables,
as described [here](https://en.wikipedia.org/wiki/INI_file).  These
settings may be tweaked to describe the location of installed
software, the collections used for synthesis, etc.

The [opentree] section might look like this:

    [opentree]
    home = /home/USER/OpenTree
    peyotl = %(home)s/peyotl
    phylesystem = %(home)s/phylesystem
    ott = %(home)s/ott/ott2.9draft12/
    collections = %(home)s/collections

This describes a configuration file the where peyotl, propinquity,
phylesystem, collections, and the OTT directories are all located
inside a single `OpenTree` directory. This is not necessary, but is
one way of doing things.

If you do install multiple packages under the same parent directory,
you can define a variable such as `home` to point to the parent directory.
Then you can reference that directory by writing `%(home)s` in other
variables in the same section.

To save space, from now on we will write {opentree.peyotl} to mean the location of Peyotl
as defined in the `config` file.  Thus a command line

    $ ls {opentree.ott}/taxonomy.tsv

really means

    $ ls /home/USER/OpenTree/ott/ott2.9draft12/taxonomy.tsv

if the variables in the config file are defined as above.


## Prerequisites

  1. A local version of the OTT taxonomy. See http://files.opentreeoflife.org/ott/
  with a config entry pointing to it in the `opentree` section.
    
      [opentree]
      ...
      ott = %(home)s/ott/ott2.9draft12
      ...


  1. [peyotl](https://github.com/mtholder/peyotl) should be downloaded and installed
  with an config entry pointing to it:

       [opentree]
       ...
       peyotl = %(home)s/peyotl
       ...

  Note that (as of 2015-Oct-10) the master branch of peyotl on mtholder's
  GitHub page (not the Open Tree of Life group). See the link above.


  1. A local copy of the [phylesystem-1](https://github.com/opentreeoflife/phylesystem-1)
  repo with a config entry pointing to the parent of the shards directory

       [opentree]
       ...
       phylesystem = %(home)s/phylesystem
       ...

  The actual phylesystem-1 repo cloned from git should be in a directory {opentree.phylesystem}/shards/phylesystem-1
   

  1. A local copy of the collections-1 repo with a config entry
  pointing to the parent of the shards directory

       [opentree]
       ...
       phylesystem = %(home)s/collections
       ...

  The actual [collections-1](https://github.com/opentreeoflife/collections-1) repo cloned from git should be in a directory {opentree.collections}/shards/collections-1

  1. [otcetera](https://github.com/mtholder/otcetera)

  1. [tee](https://en.wikipedia.org/wiki/Tee_(command))


## Usage

After you have installed the software and tweaked the seting in your `config` file as
described above, you may run synthesis just by typing

    $ make

## Artifacts
  1. [cleaned_ott](cleaned_ott/README.md)
  1. [phylo_input](phylo_input/README.md)
  1. [phylo_snapshot](phylo_snapshot/README.md)
  1. [cleaned_phylo](cleaned_phylo/README.md)
  1. [exemplified_phylo](exemplified_phylo/README.md)


## Sketch
A cartoon of the pipeline with peyotl tools in pink and otcetera tools in blue.
Input from other components of Open Tree of Life are ovals.
Settings of the propinquity config file are in diamonds.

The products of this repo are contents of directories, and the rectangles show these directories.
Don't take this too literally.
In some cases, there are multiple targets created with 
different tools in a subdirectory.
In these cases this sketch just shows the most interesting tool.

![pipeline](https://github.com/mtholder/propinquity/blob/master/doc/pipeline-tools.png)

### Example configuration

    $ ls $PEYOTL_ROOT 
    ...
    peyotl
    ...
    setup.py
    ...
    $ echo $OTT_DIR
    /tmp/ott2.9draft9
    $ ls $OTT_DIR
    ...
    taxonomy.tsv
    ...
    $ ls $PHYLESYSTEM_ROOT/shards/phylesystem-1
    next_study_id.json  README.md  study
    $ cat config
    [taxonomy]
    cleaning_flags = major_rank_conflict,major_rank_conflict_direct,major_rank_conflict_inherited,environmental,viral,nootu,barren,not_otu,extinct_inherited,extinct_direct,hidden,tattered


### Checking the synthetic tree

```sh
cd exemplified_phylo
otc-displayed-stats ../cleaned_ott/cleaned_ott.tre ../full_supertree/full_supertree.tre $(cat nonempty_trees.txt)
```

```sh
cd exemplified_phylo
otc-displayed-stats ../cleaned_ott/cleaned_ott.tre draftversion4.tre $(cat nonempty_trees.txt)
```

### To do
**TODO**: check flags for pruning

**TODO** examine the behavior of nodes with outdegree=1 in inputs

**TODO** many of the steps in the Makefile use the presence of a file to signal
  the successful completion of a step that generates multiple artifacts. I've pretty
  much been trying to get this pipeline up to the point that Ben Redelings can
  run otcetera-based tools on the latter stages of the pipeline. So there has been
  little checking of the logic of each of the make steps is correct for rebuilding.