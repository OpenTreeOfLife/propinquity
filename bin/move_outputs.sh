#!/bin/sh

# move propinquity output to a new subdirectory

if test -z $1
then
    echo "expecting a directory as an argument"
    exit 1
fi
outputdir="$1"
outputdirs=(
  annotated_supertree
  assessments
  cleaned_ott
  cleaned_phylo
  exemplified_phylo
  full_supertree
  grafted_solution
  labelled_supertree
  logs
  phylo_input
  phylo_induced_taxonomy
  phylo_snapshot
  subproblems
  subproblem_solutions
  )
# it would be quicker to move the files rather than cp them
# but using mv, you run into issues with arg list too long, plus then
# have to move back the readme files
mkdir -p $outputdir
for d in ${outputdirs[@]}; do
  echo "copying $d files"
  cp -Rp $d $outputdir
done

# and now copy the doc files
cp -Rp index* $outputdir
