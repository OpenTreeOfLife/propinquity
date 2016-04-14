#!/bin/sh
if test -z $PROPINQUITY_OUT_DIR
then
    export PROPINQUITY_OUT_DIR="$PWD"
fi
if test -z "${OTCETERA_LOGFILE}"
then
    export OTCETERA_LOGFILE="${PROPINQUITY_OUT_DIR}/logs/myeasylog.log"
fi
if ! test -d "${PROPINQUITY_OUT_DIR}/logs"
then
    mkdir -p "${PROPINQUITY_OUT_DIR}/logs" || exit
fi
rm -f "${PROPINQUITY_OUT_DIR}/logs/complete_log.txt"
bin/rebuild_from_latest.sh \
    2>${PROPINQUITY_OUT_DIR}/logs/complete_log_error.txt \
    | tee "${PROPINQUITY_OUT_DIR}/logs/complete_log.txt"