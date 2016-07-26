#!/bin/bash
# Takes 2 script args  and then the args that will be passed to otc-uncontested-decompose
#   1. the export dir (any .tre files here will be removed, and new ones will be written here
#   2. a filepath to store the .tre filenames for all of the tree files created by the
#       the decomposition. This will only be created if the decomposition exits without error.
#       if a relative path, it should be relative to the export dir!!
#   3. a filepath to JSON representation of contested OTT ID to list of trees that contest that
#       that taxon.
#       if a relative path, it should be relative to the export dir!!
exportdir="$1"
shift
dumpedidfile="$1"
shift
contestingtreesfile="$1"
shift
set -x
if test -z $exportdir
then
    echo "expecting the first arg to be an export directory, which will have its .tre files removed and repopulated."
    exit 1
fi
if test -z $dumpedidfile
then
    echo "expecting the second argument to be a filepath (absolute or relative to the export directory) for the subproblem IDs."
    exit 1
fi
if test -z $contestingtreesfile
then
    echo "expecting the third argument to be a filepath (absolute or relative to the export directory) for a JSON repr of the contesting trees for each taxon."
    exit 1
fi

if test -d "${exportdir}"
then
    rm -f "${exportdir}"/*.tre || exit
else
    mkdir "${exportdir}" || exit
fi
otc-uncontested-decompose -e"${exportdir}" -x"${dumpedidfile}" -c"${contestingtreesfile}" $@ || exit

