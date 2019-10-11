#!/bin/bash

# Makes the two tarballs for posting on the website:
# 1. A small summary archive called `opentree{#}_tree.tgz`, containing these files:
#   * `labelled_supertree/labelled_supertree.tre`
#   * `labelled_supertree/labelled_supertree_ottnames.tre`
#   * `grafted_solution/grafted_solution.tre`
#   * `grafted_solution/grafted_solution_ottnames.tre`
#   * `annotated_supertree/annotations.json`
#   * a README file that describes the files
# 2. A large archive called `opentree{#}_output.tgz` of all synthesis
#   outputs, including `*.html` files

# command line args
propinquity_bin_dir="`dirname $0`"
if test -z $1
then
  echo "expecting first argument to be an output directory"
  exit 1
fi
preoutputdir="$1"
if ! test -d $preoutputdir
then
    echo "$preoutputdir does not exist"
    exit 1
fi

if test -z $2
then
    echo "expecting second argument to be the synthesis tree id, e.g. opentree6.1"
    exit 1
fi
treeid="$2"

if test -z $3
then
    echo "expecting third argument to be the version number, e.g. 6.1"
    exit 1
fi
version="$3"

outputdir=opentree${version}
if [ "${preoutputdir}" != "${outputdir}" ] ; then
    if [ -e ${outputdir} ] ; then
	echo "Directory ${outputdir} already exists!"
	exit 1
    fi
    cp -a ${preoutputdir} ${outputdir}
fi


bash "${propinquity_bin_dir}/make_tree_tarball.sh" "${outputdir}" "${treeid}" "${version}"

# all synthesis outputs
tar -czf ${outputdir}_output.tgz $outputdir

exit 0

OUTPUT=opentree${version}_output.tgz
TREE=opentree${version}_tree.tgz

FILES=files.opentreeoflife.org
HOST=opentree@${FILES}
DIR="${FILES}/synthesis/opentree${version}"

ssh ${HOST} "mkdir ${DIR}"
scp ${OUTPUT} ${HOST}:${DIR}/
scp ${TREE}   ${HOST}:${DIR}/
ssh ${HOST} "cd ${DIR} ; tar -zxf ${OUTPUT}"
ssh ${HOST} "cd ${DIR} ; tar -zxf ${TREE}"
ssh ${HOST} "cd ${DIR} ; ln -s opentree${version} output" 
