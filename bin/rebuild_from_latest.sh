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


echo 'creating the supertree...'
echo -n 'supertree ' >> "${PROPINQUITY_OUT_DIR}/logs/timestamps" ; date >> "${PROPINQUITY_OUT_DIR}/logs/timestamps"
rm -f ${PROPINQUITY_OUT_DIR}/logs/log-of-supertree.txt || exit
rm -f ${PROPINQUITY_OUT_DIR}/logs/log-of-supertree-err.txt || exit
if ! make ${PROPINQUITY_OUT_DIR}/labelled_supertree/labelled_supertree.tre \
    2>${PROPINQUITY_OUT_DIR}/logs/log-of-supertree-err.txt \
    >${PROPINQUITY_OUT_DIR}/logs/log-of-supertree.txt
then
    cat ${PROPINQUITY_OUT_DIR}/logs/log-of-supertree-err.txt
    echo "Failed supertree step"
    exit 1
fi

echo 'annotating the supertree...'
echo -n 'annotating ' >> "${PROPINQUITY_OUT_DIR}/logs/timestamps" ; date >> "${PROPINQUITY_OUT_DIR}/logs/timestamps"
rm -f ${PROPINQUITY_OUT_DIR}/logs/log-of-annotations.txt
rm -f ${PROPINQUITY_OUT_DIR}/logs/log-of-annotations-err.txt
if !  make ${PROPINQUITY_OUT_DIR}/annotated_supertree/annotations.json \
    2>${PROPINQUITY_OUT_DIR}/logs/log-of-annotations-err.txt \
    > ${PROPINQUITY_OUT_DIR}/logs/log-of-annotations.txt
then
    cat ${PROPINQUITY_OUT_DIR}/logs/log-of-annotations-err.txt
    echo "Failed annotations step"
    exit 1
fi

echo 'make extra...'
echo -n 'extra ' >> "${PROPINQUITY_OUT_DIR}/logs/timestamps" ; date >> "${PROPINQUITY_OUT_DIR}/logs/timestamps"
rm -f ${PROPINQUITY_OUT_DIR}/logs/log-of-extra.txt
rm -f ${PROPINQUITY_OUT_DIR}/logs/log-of-extra-err.txt
if !  make extra \
    2>${PROPINQUITY_OUT_DIR}/logs/log-of-extra-err.txt \
    > ${PROPINQUITY_OUT_DIR}/logs/log-of-extra.txt
then
    cat ${PROPINQUITY_OUT_DIR}/logs/log-of-extra-err.txt
    echo "Failed extra step"
    exit 1
fi


echo 'running the assessments of the tree...'
echo -n 'assessments ' >> "${PROPINQUITY_OUT_DIR}/logs/timestamps" ; date >> "${PROPINQUITY_OUT_DIR}/logs/timestamps"
rm -f ${PROPINQUITY_OUT_DIR}/logs/log-of-assessments.txt
rm -f ${PROPINQUITY_OUT_DIR}/logs/log-of-assessments-err.txt
if ! make ${PROPINQUITY_OUT_DIR}/assessments/summary.json \
    2>${PROPINQUITY_OUT_DIR}/logs/log-of-assessments-err.txt \
    > ${PROPINQUITY_OUT_DIR}/logs/log-of-assessments.txt
then
    cat ${PROPINQUITY_OUT_DIR}/logs/log-of-assessments-err.txt
    echo "Failed assessments step"
    exit 1
fi

echo -n 'html ' >> "${PROPINQUITY_OUT_DIR}/logs/timestamps" ; date >> "${PROPINQUITY_OUT_DIR}/logs/timestamps"
echo 'creating documentation of the outputs...'
rm -f ${PROPINQUITY_OUT_DIR}/logs/log-of-html.txt
rm -f ${PROPINQUITY_OUT_DIR}/logs/log-of-html-err.txt
if ! make html \
    2>${PROPINQUITY_OUT_DIR}/logs/log-of-html-err.txt \
    > ${PROPINQUITY_OUT_DIR}/logs/log-of-html.txt || exit
then
    cat ${PROPINQUITY_OUT_DIR}/logs/log-of-html-err.txt
    echo "Failed building of html step"
    exit 1
fi

echo -n 'make check ' >> "${PROPINQUITY_OUT_DIR}/logs/timestamps" ; date >> "${PROPINQUITY_OUT_DIR}/logs/timestamps"
if ! make check 2>${PROPINQUITY_OUT_DIR}/logs/log-of-make-check-err.txt \
    > ${PROPINQUITY_OUT_DIR}/logs/log-of-make-check.txt
then
    cat ${PROPINQUITY_OUT_DIR}/logs/log-of-make-check-err.txt
    echo "Failed make check step"
    exit 1
fi 

echo 'Done'
echo -n 'done ' >> "${PROPINQUITY_OUT_DIR}/logs/timestamps" ; date >> "${PROPINQUITY_OUT_DIR}/logs/timestamps"
