#!/bin/bash
DRAWTREE=../drawtree
OTT=../../examples/2/taxonomy
EXAMPLE=../example2

function draw {
    local file=$1
    mkdir -p $(dirname $file)
    otc-relabel-tree --taxonomy=$OTT $EXAMPLE/$file --format-tax=%N > $file
    $DRAWTREE --input=$file --output=$file.svg \
	      --edge.width=3 "$@"

}

draw cleaned_ott/cleaned_ott.tre
draw cleaned_phylo/ex_2@tree1.tre
draw cleaned_phylo/ex_2@tree2.tre
draw exemplified_phylo/ex_2@tree1.tre
draw exemplified_phylo/ex_2@tree2.tre
draw exemplified_phylo/taxonomy.tre --show.node.label=TRUE
draw grafted_solution/grafted_solution_ottnames.tre --show.node.label=TRUE
