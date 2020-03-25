#!/bin/sh

if [ "$#" -ne 2 ]; then
    echo "You must enter exactly 2 command line arguments:"
    echo " % build_at_dir2.sh <configfile> <dir>"
    echo
    echo "Example:"
    echo " % build_at_dir2.sh config synth-runs/opentree13.0"
    exit 1
fi

configfile=$1
dir=$2
otttag=$3

set -x

# This overrides ~/.opentree
# This should use a taxonomy that results from `otc-taxonomy-parser ott3.2 -E --write-taxonomy=ott3.2-extinct-flagged`
export OTC_CONFIG=~/.flag-mod-opentree

dir1="${dir}-stage1"
dir2="${dir}"
ottdir="$(./bin/config_checker.py opentree.ott)"
bumped_ott_dir=${ottdir%%/}-bumped-$(basename $dir2)

if test -d "$dir1"
then
    echo "Removing $dir1"
    rm -r "$dir1" || exit 1
fi

if test -d "$dir2"
then
    echo "Directory '$dir2' already exists!"
    exit 1
fi

if ! ./bin/build_at_dir.sh ${configfile} "${dir1}"
then
    jsonfp="${dir1}/cleaned_ott/move_extinct_higher_log.json"
    if ./bin/verify_taxon_edits_not_needed.py "${jsonfp}"
    then
       echo 'build failed for reason other than need of taxon bump'
       exit 1
    fi

    if test -d "${bumped_ott_dir}"
    then
        echo "Removing ${bumped_ott_dir}"
        rm -r "${bumped_ott_dir}" || exit
    fi

    ./bin/patch_taxonomy_by_bumping.py "${ottdir}" "${jsonfp}" "${bumped_ott_dir}" || exit

    cat "${OTC_CONFIG}"  | sed -E '/^ott/d' > ~/.bumped-opentree
    echo "ott = ${bumped_ott_dir}" >> ~/.bumped-opentree
    export OTC_CONFIG=~/.bumped-opentree
    ./bin/build_at_dir.sh ${configfile} "${dir2}" || exit 1
fi
