# propinquity

Propinquity is a snakemake-based pipeline for constructing a synthetic tree of life.  See https://peerj.com/articles/3058/ for a description and comparison of its performance to the previous tool used to build the Open Tree of Life's summary tree.

It takes as input a collection of phylogenetic trees from the Open Tree of Life
datastore and a local copy of the Open Tree of Life Taxonomy. See the [collections documentation](https://github.com/OpenTreeOfLife/opentree/wiki/Working-with-tree-collections) for input on putting trees into collections.


# Installation
Using python 3.8 or 3.9 (probably installing in a virtualenv)

    pip install -r requirements.txt
    python setup.py develop

