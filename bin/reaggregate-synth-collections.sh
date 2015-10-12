#!/bin/sh
set -x
outp="$1"
if test -z $outp
then
    echo "expecing an output file as an argument"
    exit 1
fi
if test -f "$outp"
then
    echo "${outp} is in the way"
    exit 1
fi

for s in plants metazoa fungi safe-microbes
do
    if test -f "${s}.json"
    then
        echo "${s}.json is in the way!"
        exit 1
    fi
done

for s in plants metazoa fungi safe-microbes
do
    wget https://raw.githubusercontent.com/OpenTreeOfLife/collections-1/master/collections-by-owner/opentreeoflife/${s}.json
done

$PEYOTL_ROOT/scripts/concatenate_collections.py plants.json metazoa.json fungi.json safe-microbes.json --output="${outp}"
