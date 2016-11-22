#!/bin/bash
if test -d test-output
then
	if ! rmdir test-output
	then
		echo 'test-output directory is in the way. Move it first!'
		exit 1
	fi
fi
mkdir -p test-output

function run_example_test {
	exnum=$1
	rankingfileprefix=$2
	if test -z $rankingfileprefix
	then
		echo 'need 2 args to run_example_test'
		exit 1
	fi
	export PROPINQUITY_OUT_DIR="test-output/e${exnum}-${rankingfileprefix}"
	export OTT_DIR="examples/${exnum}/taxonomy"
	./build-from-newicks.sh "examples/${exnum}/${rankingfileprefix}-phylo-rankings.txt" || exit
	make html || exit
	make clean || exit
	rm -f "$PROPINQUITY_OUT_DIR/config"
	rmdir "$PROPINQUITY_OUT_DIR" || exit 1
}

run_example_test 1 two || exit
run_example_test 2 two || exit
run_example_test 2 three || exit
run_example_test 3 one || exit
