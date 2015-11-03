# propinquity

## Prerequisites

  1. a local version of the OTT taxonomy. See http://files.opentreeoflife.org/ott/
    with an environmental variable pointing to it:

    $ export OTT_DIR=/tmp/ott/aster

  2. [peyotl](https://github.com/mtholder/peyotl) should be downloaded and installed
    with an environmental variable pointing to it:

    export PEYOTL_ROOT=/tmp/peyotl

    Note that (as of 2015-Oct-10) the master branch of peyotl on mtholder's
    GitHub page (not the Open Tree of Life group). See the link above.

  3. [tee](https://en.wikipedia.org/wiki/Tee_(command))

  4. a local copy of the phylesystem with an environmental variable PHYLESYSTEM_ROOT pointing to the parent of the shards directory.


## Usage

After you have your environment set up (as described above), you'll need to

    $ cp config.example config

and tweak the settings as desired. Then:

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