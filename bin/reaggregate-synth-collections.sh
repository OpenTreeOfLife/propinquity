#!/bin/sh

#set -x
outp="$1"
if test -z $outp
then
    echo "expecting an output file as an argument"
    exit 1
fi
if test -f "$outp"
then
    echo "${outp} is in the way"
    exit 1
fi

if [ -z "$COLLECTIONS_ROOT" ] ; then
    echo "COLLECTIONS_ROOT not set!"
    exit 1
fi

if [ ! -e "$COLLECTIONS_ROOT" ] ; then
    echo "'$COLLECTIONS_ROOT' does not exist!"
    exit 1
fi

if [ ! -d "$COLLECTIONS_ROOT" ] ; then
    echo "'$COLLECTIONS_ROOT' is not a directory!"
    exit 1
fi

COLLECTIONS_DIR=$COLLECTIONS_ROOT/shards/collections-1/collections-by-owner/

if [ ! -d "$COLLECTIONS_DIR" ] ; then
    echo "$COLLECTIONS_DIR does not exist!"
    exit 1
fi


COLLECTIONS=""
for s in $SYNTHESIS_COLLECTIONS
do
    FILENAME=$COLLECTIONS_DIR/${s}.json
    if [ ! -f "$FILENAME" ] ; then
	echo "Collection '$s' not found!"
	exit 1
    fi
    COLLECTIONS="$COLLECTIONS $FILENAME"
done

echo $PEYOTL_ROOT/scripts/concatenate_collections.py $COLLECTIONS --output="${outp}"
$PEYOTL_ROOT/scripts/concatenate_collections.py $COLLECTIONS --output="${outp}"
