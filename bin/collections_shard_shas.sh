#!/bin/sh
if test -z $COLLECTIONS_ROOT
then
    echo COLLECTIONS_ROOT must be set
    exit 1
fi
cd "${COLLECTIONS_ROOT}" || exit
TMPF="${PWD}/.shard-shas.tmp"
rm -f "${TMPF}"
for f in $(ls -d shards/collections-*)
do
    cd $f || exit
    git rev-parse HEAD >> "${TMPF}"
    cd - >/dev/null 2>&1
done
cat "${TMPF}" | sort
rm -f "${TMPF}"