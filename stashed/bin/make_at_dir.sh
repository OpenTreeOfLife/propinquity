#!/bin/bash
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
echo "Calling make $@..."
make $@