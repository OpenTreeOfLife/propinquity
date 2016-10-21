#!/bin/sh
set -x
td=../cnidaria
if test -d "$td"
then
   rm -r "$td" || exit
fi

time ./bin/build_at_dir.sh config.cnidaria.synth "${td}"

