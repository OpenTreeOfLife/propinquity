#!/bin/bash
d="$(dirname $0)"
cf="$1"
outd="$2"
if ! test -f config
then
    echo "expecting the first argument to be a config file. ${cf} does not exist"
    exit 1
fi
if test -f config
then
    echo 'file "config" exists. Moving it to config.BAK (overwriting that file if it exists)'
    mv config confg.BAK
fi
echo "Copying ${cf} to config"
cp "${cf}" config
echo "Setting PROPINQUITY_OUT_DIR to ${outd}"
export PROPINQUITY_OUT_DIR="${outd}"
master="${d}/opentree_rebuild_from_latest.sh"
echo "Calling make clean ..."
make clean