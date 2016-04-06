#!/bin/sh

orig_dir="$(pwd)"
echo 'Pulling the latest studies from the phylesystem shards:'
cd $(python bin/config_checker.py opentree.phylesystem config ~/.opentree)
cd shards
for d in phylesystem-*
do
    cd $d
    git pull origin --no-commit
    cd - >/dev/null 2>&1
done
cd "${orig_dir}"

echo
echo 'Pulling the latest collections from the collections shards:'
cd $(python bin/config_checker.py opentree.collections config ~/.opentree)
cd shards
for d in collections-*
do
    cd $d
    git pull origin --no-commit
    cd - >/dev/null 2>&1
done
cd "${orig_dir}"
