# propinquity

## Prerequisites

  1. a local version of the OTT taxonomy. See http://files.opentreeoflife.org/ott/
    with an environmental variable pointing to it:

    $ export OTT_DIR=/tmp/ott/aster

  2. [peyotl](https://github.com/mtholder/peyotl) should be downloaded and installed
    with an environmental variable pointing to it:

    export PEYOTL_ROOT=/tmp/peyotl

    currently requires non-merged branches of peyotl

  3. [tee](https://en.wikipedia.org/wiki/Tee_(command))

  4. a local copy of the phylesystem with an environmental variable pointing to the parent of the shards directory.

## Usage

After you have your environment set up (as described above), you'll need to

    $ cp config.example config

and tweak the settings as desired. Then:

    $ make

## Artifacts
### `cleaned_ott` subdirectory
  * `cleaned_ott.tre` has dubious taxa pruned off.
This implementation should check against treemachine and smasher versions.
  * `cleaned_ott.json` is a JSON file that report
  * `ott_version` is a copy of `$(OTT_DIR)/version.txt`. So, if you change
the version of OTT that you are using, this file should be copied and trigger
a rebuild of the pruned taxonomy in `cleaned_ott.tre`
  * `cleaning_flags.txt` holds the value for that setting from the config file. It is pulled
out as a separate file to make it obvious when the "cleaned" taxonomy needs to be changed.

### `phylo_input` subdirectory
  * `rank_collection.json` a complete study collection with the trees in ranked
order. **TEMPRORARY:** Currently just downloading a copy of the `synthesis-collections.json` from the Holder lab.
  * `studies.txt` a view of `rank_collection.json` that is just one line per tree
with the study ID alone.
  * `study_tree_pairs.txt` a view of `rank_collection.json`. Each line is a
studyID_treeID represenation of the tree's ID.


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