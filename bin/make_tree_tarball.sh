#!/bin/bash

# Makes the two tarballs for posting on the website:
# 1. A small summary archive called `opentree{#}_tree.tgz`, containing these files:
#   * `labelled_supertree/labelled_supertree.tre`
#   * `labelled_supertree/labelled_supertree_ottnames.tre`
#   * `grafted_solution/grafted_solution.tre`
#   * `grafted_solution/grafted_solution_ottnames.tre`
#   * `annotated_supertree/annotations.json`
#   * a README file that describes the files
# 2. A large archive called `opentree{#}_output.tgz` of all synthesis
#   outputs, including `*.html` files

# command line args
if test -z $1
then
  echo "expecting first argument to be an output directory"
  exit 1
fi
outputdir="$1"
if ! test -d $outputdir
then
    echo "$outputdir does not exist"
    exit 1
fi

if test -z $2
then
    echo "expecting second argument to be the synthesis tree id, e.g. opentree6.1"
    exit 1
fi
treeid="$2"

if test -z $3
then
    echo "expecting third argument to be the version number, e.g. 6.1"
    exit 1
fi
version="$3"
set -x
# first (smaller) tarball
tar_dir1="${treeid}_tree"
mkdir -p $tar_dir1 || exit
mkdir -p $tar_dir1/labelled_supertree || exit
mkdir -p $tar_dir1/grafted_solution || exit
cp -p $outputdir/labelled_supertree/labelled_supertree.tre $tar_dir1/labelled_supertree/ || exit
cp -p $outputdir/labelled_supertree/labelled_supertree_ottnames.tre $tar_dir1/labelled_supertree/ || exit
cp -p $outputdir/grafted_solution/grafted_solution.tre $tar_dir1/grafted_solution/ || exit
cp -p $outputdir/grafted_solution/grafted_solution_ottnames.tre $tar_dir1/grafted_solution/ || exit
cp -p $outputdir/annotated_supertree/annotations.json $tar_dir1/ || exit

# readme file
echo 'printing readme file'
files_url="http://files.opentreeoflife.org/synthesis/$treeid/output" || exit
touch $tar_dir1/README.md || exit
printf "[Release notes for version %s](https://github.com/OpenTreeOfLife/germinator/blob/master/doc/ot-synthesis-v%s.md)\n" $version $version > $tar_dir1/README.md || exit
printf "\nContents of \`%s_tree.tgz\`" $treeid >> $tar_dir1/README.md || exit
printf "\n* \`output/annotated_supertree/annotations.json\` - synthetic tree annotations; see [docs](%s/annotated_supertree/index.html) for explanation" $files_url >> $tar_dir1/README.md || exit
printf "\n* \`output/labelled_supertree/\` - see [docs](%s/labelled_supertree/index.html) for explanation; contains:" $files_url >> $tar_dir1/README.md || exit
printf "\n   * \`labelled_supertree.tre\` - full synthetic tree; labels are ottids" >> $tar_dir1/README.md || exit
printf "\n   * \`labelled_supertree_ottnames.tre\` - full synthetic tree; labels are name_ottid" >> $tar_dir1/README.md || exit
printf "\n* \`output/grafted_solution\` - see [docs](%s/grafted-solution/index.html) for explanation; contains:" $files_url >> $tar_dir1/README.md || exit
printf "\n   * \`grafted_solution.tre\` - synthetic tree without taxonomy-only outputs; labels as ottids" >> $tar_dir1/README.md || exit
printf "\n   * \`grafted_solution_ottnames.tre\` - synthetic tree without taxonomy-only outputs; labels are name_ottid" >> $tar_dir1/README.md || exit

# tar these babies up
echo 'creating full archive'
# tar -czf $tar_dir1.tgz $tar_dir1 || exit
