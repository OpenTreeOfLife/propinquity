#!/bin/bash
# source this file with 2 arguments:
#     1. a filepath to your synth config file, and 
#     2. the filepath to the output directory
# This is just a helpful shortcut that:
#   1. creates out_dir if it does not exist,
#   2. copies the config file to output_dir/config
#   3. sets PROPINQUITY_OUT_DIR (irrelevant if you run this instead of sourcing)
#   4. sets OTCETERA_LOGFILE to out_dir/logs
#   5. creates that logs directory.
# After this you should be able to run commands like:
#    $ make $(PROPINQUITY_OUT_DIR)/phylo_input/studies.txt

d="$(dirname $0)"
cf="$1"
outd="$2"
if ! test -f "${cf}"
then
    echo "expecting the first argument to be a config file. ${cf} does not exist"
    exit 1
fi
if ! test -d "${outd}"
then
    mkdir "${outd}" || exit
fi
if ! diff "${cf}" "${outd}/config" >/dev/null 2>&1
then
    echo "Copying ${cf} to ${outd}/config"
    cp "${cf}" "${outd}/config" || exit
fi
echo "Setting PROPINQUITY_OUT_DIR to ${outd}"
export PROPINQUITY_OUT_DIR="${outd}"
if test -z "${OTCETERA_LOGFILE}"
then
    export OTCETERA_LOGFILE="${PROPINQUITY_OUT_DIR}/logs/myeasylog.log"
fi
if ! test -d "${PROPINQUITY_OUT_DIR}/logs"
then
    mkdir -p "${PROPINQUITY_OUT_DIR}/logs" || exit
fi
shift
shift
