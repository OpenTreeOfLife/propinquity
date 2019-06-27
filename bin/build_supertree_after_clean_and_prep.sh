

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
    > ${PROPINQUITY_OUT_DIR}/logs/log-of-html.txt
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
