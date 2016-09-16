#!/bin/bash
d="$(dirname $0)"
cf="$1"
outd="$2"
# we won't source because sh and dash won't pass arg to sourced files
bash "${d}/augment_env_for_make.bash" "${cf}" "${outd}" || exit 1
echo "Setting PROPINQUITY_OUT_DIR to ${outd}"
export PROPINQUITY_OUT_DIR="${outd}"
if test -z "${OTCETERA_LOGFILE}"
then
    export OTCETERA_LOGFILE="${PROPINQUITY_OUT_DIR}/logs/myeasylog.log"
fi
master="${d}/opentree_rebuild_from_latest.sh"
echo "Calling ${master} ..."
"${master}"
