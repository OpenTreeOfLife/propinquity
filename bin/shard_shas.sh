#!/bin/sh
if test -z $PHYLESYSTEM_ROOT
then
    echo PHYLESYSTEM_ROOT must be set
    exit 1
fi
cd "${PHYLESYSTEM_ROOT}" || exit
TMPF="/tmp/shard-shas.tmp"
rm -f "${TMPF}"
for f in $(ls -d shards/phylesystem-*)
do
    cd $f || exit
    git rev-parse HEAD >> "${TMPF}"
    cd - >/dev/null 2>&1
done
cat "${TMPF}" | sort
rm "${TMPF}"