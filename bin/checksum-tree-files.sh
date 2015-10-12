#!/bin/bash
cd "$1" || exit
set -x
for i in *.tre
do
    b=$(echo $i | sed -e 's/\.tre$//')
    md5sum $i "${b}"-tree-names.txt > "${b}".md5
done
cd -