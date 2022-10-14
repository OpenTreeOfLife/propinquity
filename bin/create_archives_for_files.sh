#!/bin/bash
set -x
res="${1}"
if ! test -d "${res}" ; then
	echo "expecting 1 arg: the results directory. ${res} is not a directory"
	exit 1
fi
bn=`basename "${res}"`
dn=`dirname "${res}"`
version=`echo "${bn}" | sed -E 's/opentree//'`
echo $dn
echo $bn
echo $version
cd "${dn}" || exit
cod="${bn}_cruft"
if ! test -d "${cod}" ; then
    mkdir "${cod}" || exit
fi

mv "${bn}/.snakemake" "${cod}/.snakemake" || exit
mkdir "${bn}/.snakemake" || exit
mv "${cod}/.snakemake/log" "${bn}/.snakemake/" || exit

mv "${bn}/subott_dir" "${cod}/subott_dir" || exit
mkdir "${bn}/subott_dir" || exit
cp "${cod}/subott_dir"/index.* "${bn}/subott_dir"

if ! test -d "${cod}/bumped_ott" ; then
    mkdir "${cod}/bumped_ott" || exit
fi
find "${bn}/bumped_ott" -name "*.pickle" -exec mv {} "${cod}/bumped_ott" \; || exit

tar cfvz "${bn}.tgz" "${bn}" || exit

tod="${bn}_tree"
if test -d "${tod}" ; then
	echo "${tod} is in the way"
	exit 1
fi
mkdir "${tod}" || exit
mkdir "${tod}/grafted_solution" || exit
mkdir "${tod}/labelled_supertree" || exit

cp "${bn}/labelled_supertree/labelled_supertree_ottnames.tre" "${tod}/labelled_supertree/" || exit
cp "${bn}/labelled_supertree/labelled_supertree.tre" "${tod}/labelled_supertree/" || exit
cp "${bn}/grafted_solution/grafted_solution_ottnames.tre" "${tod}/grafted_solution/" || exit
cp "${bn}/grafted_solution/grafted_solution.tre" "${tod}/grafted_solution/" || exit
cp "${bn}/annotated_supertree/annotations.json" "${tod}/" || exit

cat << ___HERE > "${tod}/README.md" || exit
[Release notes for version ${version}](https://github.com/OpenTreeOfLife/germinator/blob/master/doc/ot-synthesis-v${version}.md)

Contents of \`opentree${version}_tree.tgz\`
* \`output/annotated_supertree/annotations.json\` - synthetic tree annotations; see [docs](http://files.opentreeoflife.org/synthesis/opentree${version}output/annotated_supertree/index.html) for explanation
* \`output/labelled_supertree/\` - see [docs](http://files.opentreeoflife.org/synthesis/opentree${version}/output/labelled_supertree/index.html) for explanation; contains:
   * \`labelled_supertree.tre\` - full synthetic tree; labels are ottids
   * \`labelled_supertree_ottnames.tre\` - full synthetic tree; labels are name_ottid
* \`output/grafted_solution\` - see [docs](http://files.opentreeoflife.org/synthesis/opentree${version}/output/grafted-solution/index.html) for explanation; contains:
   * \`grafted_solution.tre\` - synthetic tree without taxonomy-only outputs; labels as ottids
   * \`grafted_solution_ottnames.tre\` - synthetic tree without taxonomy-only outputs; labels are name_ottid
___HERE

tar cfvz "${tod}.tgz" "${tod}" || exit

