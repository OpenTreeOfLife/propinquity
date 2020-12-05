#!/bin/sh
# runs make clean, pulls study and collections from GitHub and
# then builds the tree and docs 
if test -z "$PROPINQUITY_OUT_DIR"
then
    echo "PROPINQUITY_OUT_DIR must be defined in env. Define it to . if you want to build in place"
    exit 1
fi
mkdir -p "${PROPINQUITY_OUT_DIR}/logs" || exit
echo -n 'pulling ' > "${PROPINQUITY_OUT_DIR}/logs/timestamps" ; date >> "${PROPINQUITY_OUT_DIR}/logs/timestamps"
orig_dir="$(pwd)"
echo 'pulling the latest studies from the phylesystem shards'

cd $(python bin/config_checker.py opentree.phylesystem config "${OTC_CONFIG:-~/.opentree}")  || exit
cd shards || exit
for d in phylesystem-*
do
    cd $d || exit
    git pull origin --no-commit || exit
    cd - 2>/dev/null || exit
done
cd "${orig_dir}"

echo 'pulling the latest collections from the collections shards'
cd $(python bin/config_checker.py opentree.collections config "${OTC_CONFIG:-~/.opentree}") || exit
cd shards || exit
for d in collections-*
do
    cd $d || exit
    git pull origin --no-commit || exit
    cd - 2>/dev/null || exit
done
cd "${orig_dir}"

echo "Logs will show up in the ${PROPINQUITY_OUT_DIR}/logs directory (in the event that something fails, check there)."
echo 'cleaning previous outputs...'
echo -n 'makeclean ' >> "${PROPINQUITY_OUT_DIR}/logs/timestamps" ; date >> "${PROPINQUITY_OUT_DIR}/logs/timestamps"
if ! make clean \
    >${PROPINQUITY_OUT_DIR}/logs/log-of-make-clean.txt \
    2>${PROPINQUITY_OUT_DIR}/logs/log-of-make-clean-err.txt
then
    cat ${PROPINQUITY_OUT_DIR}/logs/log-of-make-clean-err.txt
    echo "Failed make clean"
    exit 1
fi

echo "Building the supertree"
set -x
rm -f ${PROPINQUITY_OUT_DIR}/logs/myeasylog.log || exit

echo 'cleaning the inputs...'
echo -n 'inputcleaning ' >> "${PROPINQUITY_OUT_DIR}/logs/timestamps" ; date >> "${PROPINQUITY_OUT_DIR}/logs/timestamps"
rm -f ${PROPINQUITY_OUT_DIR}/logs/log-of-input-cleaning.txt || exit
rm -f ${PROPINQUITY_OUT_DIR}/logs/log-of-input-cleaning-err.txt || exit
if ! make ${PROPINQUITY_OUT_DIR}/exemplified_phylo/regraft_cleaned_ott.tre \
    2>${PROPINQUITY_OUT_DIR}/logs/log-of-input-cleaning-err.txt \
    > ${PROPINQUITY_OUT_DIR}/logs/log-of-input-cleaning.txt
then
    cat ${PROPINQUITY_OUT_DIR}/logs/log-of-input-cleaning-err.txt
    echo "Failed cleaning of the input"
    exit 1
fi

bash bin/build_supertree_after_clean_and_prep.sh || exit