#!/bin/sh
# runs make clean, pulls study and collections from GitHub and
# then builds the tree and docs 

orig_dir="$(pwd)"
echo 'pulling the latest studies from the phylesystem shards'
cd $(python bin/config_checker.py --config=config --property=opentree.phylesystem)
cd shards
for d in phylesystem-*
do
    cd $d
    git pull origin --no-commit
    cd - 2>/dev/null
done
cd "${orig_dir}"

echo 'pulling the latest collections from the collections shards'
cd $(python bin/config_checker.py --config=config --property=opentree.collections)
cd shards
for d in collections-*
do
    cd $d
    git pull origin --no-commit
    cd - 2>/dev/null
done
cd "${orig_dir}"

echo 'Logs will show up in the propinquity/logs directory (in the event that something fails, check there).'
echo 'cleaning previous outputs...'
make clean >logs/log-of-make-clean.txt 2>logs/log-of-make-clean-err.txt

echo "Building the supertree"
set -x
rm -f logs/myeasylog.log

echo 'cleaning the inputs...'
rm -f logs/log-of-input-cleaning.txt
rm -f logs/log-of-input-cleaning-err.txt
time make exemplified_phylo/taxonomy.tre 2>logs/log-of-input-cleaning-err.txt > logs/log-of-input-cleaning.txt || exit


echo 'creating the supertree...'
rm -f logs/log-of-supertree.txt
rm -f logs/log-of-supertree-err.txt
time make labelled_supertree/labelled_supertree.tre 2>logs/log-of-supertree-err.txt > logs/log-of-supertree.txt || exit

echo 'annotating the supertree...'
rm -f logs/log-of-annotations.txt
rm -f logs/log-of-annotations-err.txt
time make annotated_supertree/annotations.json 2>logs/log-of-annotations-err.txt > logs/log-of-annotations.txt || exit

echo 'running the assessments of the tree...'
rm -f logs/log-of-assessments.txt
rm -f logs/log-of-assessments-err.txt
time make assessments/summary.json 2>logs/log-of-assessments-err.txt > logs/log-of-assessments.txt || exit

make check || exit

echo 'creating documentation of the outputs...'
rm -f logs/log-of-html.txt
rm -f logs/log-of-html-err.txt
time make html 2>logs/log-of-html-err.txt > logs/log-of-html.txt || exit


echo 'Done'