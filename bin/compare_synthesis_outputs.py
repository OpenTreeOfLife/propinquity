# Given two directories of synthesis outputs, compares them
# Assumes that docs have been generated using `make html` and that
# index.json files exist where they should in various output directories

import simplejson as json
import argparse
import glob,os

# generic function to compare two lists: number of items in each,
# items in first but not second and items in second but not first
def compare_lists(type,list1,list2,verbose=False):
    s1 = set(list1)
    s2 = set(list2)
    if s1 != s2:
        if (verbose):
            print "{t}: ".format(t=type)
            # simple length check
            if len(s1) != len(s2):
                print " {l1} in dir1; {l2} in dir2".format(
                    l1=len(s1),l2=len(s2)
                    )
            common = s1.intersection(s2)
            if len(common) > 0:
                print " in common = {l}".format(t=type,l=len(common))
            diff1 = s1.difference(s2)
            if len(diff1) > 0:
                print " in dir1 but not dir2 = {l}".format(t=type,l=len(diff1))
            diff2 = s2.difference(s1)
            if len(diff2) > 0:
                print " in dir2 but not dir1 = {l}".format(t=type,l=len(diff2))
        return 1
    else:
        if (verbose):
            print "{t}: no differences".format(t=type)
        return 0

# list of collections, list of trees, compare SHAs
# look at phylo_snapshot/concrete_rank_collection.json for each run
def config_diffs(dir1,dir2):
    # get the data from both top-level index.json files
    jsonfile = "{d}/index.json".format(d=dir1)
    jsondata1 = json.load(open(jsonfile, 'r'))['config']
    jsonfile = "{d}/index.json".format(d=dir2)
    jsondata2 = json.load(open(jsonfile, 'r'))['config']

    countmismatch = 0
    # do roots match
    if (jsondata1["root_ott_id"] != jsondata2["root_ott_id"]):
        print "root id1 ({r1} != root id2 ({r2}))"
        countmismatch += 1

    # do collections match
    collections1 = jsondata1["collections"]
    collections2 = jsondata2["collections"]
    if (compare_lists("collections",collections1,collections2,False)):
        countmismatch += 1
        print "{d} collections: {c}".format(d=dir1,c=collections1)
        print "{d} collections: {c}".format(d=dir2,c=collections2)

    # do flags match
    flags1 = jsondata1["taxonomy_cleaning_flags"]
    flags2 = jsondata2["taxonomy_cleaning_flags"]
    countmismatch += compare_lists("flags",flags1,flags2,True)

    if (countmismatch == 0):
        print "no differences in root id, collections, or flags"

# check the lists of input trees
# does not check SHAs, just study@tree lists
def phylo_input_diff(dir1,dir2):
    # get the data from the phylo_input study_tree_pairs.txt files
    treefile = "{d}/phylo_input/study_tree_pairs.txt".format(d=dir1)
    treedata1 = open(treefile, 'r').read().splitlines()
    treefile = "{d}/phylo_input/study_tree_pairs.txt".format(d=dir2)
    treedata2 = open(treefile, 'r').read().splitlines()
    countmismatch = 0
    countmismatch += compare_lists("input trees",treedata1,treedata2,True)

    # check lists of non-empty tree files after cleaning
    searchstr = "{d}/cleaned_phylo/*[0-9].tre".format(d=dir1)
    nonempty1 = []
    for f in glob.glob(searchstr):
        if os.stat(f).st_size != 0:
            nonempty1.append(os.path.basename(f))
    searchstr = "{d}/cleaned_phylo/*[0-9].tre".format(d=dir2)
    nonempty2 = []
    for f in glob.glob(searchstr):
        if os.stat(f).st_size != 0:
            nonempty2.append(os.path.basename(f))
    countmismatch += compare_lists('non-empty trees',nonempty1,nonempty2,True)

    if (countmismatch == 0):
        print "no differences in input trees"

# number (and size) of subproblems
def subproblem_diff(dir1,dir2):
    # number of subproblems
    subpfile = "{d}/subproblems/subproblem-ids.txt".format(d=dir1)
    subproblems1 = open(subpfile, 'r').read().splitlines()
    subpfile = "{d}/subproblems/subproblem-ids.txt".format(d=dir2)
    subproblems2 = open(subpfile, 'r').read().splitlines()
    countmismatch = 0
    countmismatch += compare_lists("subproblems",subproblems1,subproblems2,True)

def synthesis_tree_diffs(dir1,dir2):
# file of interest is labelled_supertree/input_output_stats.json
    jsonfile = "{d}/labelled_supertree/input_output_stats.json".format(d=dir1)
    data1 = json.load(open(jsonfile, 'r'))
    jsonfile = "{d}/labelled_supertree/input_output_stats.json".format(d=dir2)
    data2 = json.load(open(jsonfile, 'r'))
    print "\n#Synthetic tree summary"
    print "stat,run1,run2,difference"
    print "-------------------------"
    print "taxonomy tips,{n1},{n2},{d}".format(
        n1=data1['input']['num_taxonomy_leaves'],
        n2=data2['input']['num_taxonomy_leaves'],
        d=int(data1['input']['num_taxonomy_leaves'])-int(data2['input']['num_taxonomy_leaves'])
    )
    print "phylogeny tips,{n1},{n2},{d}".format(
        n1=data1['output']['num_leaves_added'],
        n2=data2['output']['num_leaves_added'],
        d=int(data1['output']['num_leaves_added'])-int(data2['output']['num_leaves_added'])
    )
    print "total tips,{n1},{n2},{d}".format(
        n1=data1['input']['num_solution_leaves'],
        n2=data2['input']['num_solution_leaves'],
        d=int(data1['input']['num_solution_leaves'])-int(data2['input']['num_solution_leaves'])
    )
    print "forking nodes,{n1},{n2},{d}".format(
        n1=data1['input']['num_solution_splits'],
        n2=data2['input']['num_solution_splits'],
        d=int(data1['input']['num_solution_splits'])-int(data2['input']['num_solution_splits'])
    )
    print "broken taxa,{n1},{n2},{d}".format(
        n1=data1['output']['num_taxa_rejected'],
        n2=data2['output']['num_taxa_rejected'],
        d=int(data1['output']['num_taxa_rejected'])-int(data2['output']['num_taxa_rejected'])
    )

def broken_taxa_diffs(dir1,dir2):
# file of interest is labelled_supertree/broken_taxa.json
    jsonfile = "{d}/labelled_supertree/broken_taxa.json".format(d=dir1)
    broken_taxa1 = json.load(open(jsonfile, 'r'))['non_monophyletic_taxa'].keys()
    jsonfile = "{d}/labelled_supertree/broken_taxa.json".format(d=dir2)
    broken_taxa2 = json.load(open(jsonfile, 'r'))['non_monophyletic_taxa'].keys()
    countmismatch = 0
    countmismatch += compare_lists("broken taxa",broken_taxa1,broken_taxa2,True)

if __name__ == "__main__":
    # get command line arguments (the two directories to compare)
    parser = argparse.ArgumentParser(description='set up database tables')
    parser.add_argument('dir1',
        help='path to the first output directory'
        )
    parser.add_argument('dir2',
        help='path to the second output directory'
        )
    args = parser.parse_args()
    print "run 1 output: {d}".format(d=args.dir1)
    print "run 2 output: {d}".format(d=args.dir2)
    print "\n# Comparing inputs"
    config_diffs(args.dir1,args.dir2)
    phylo_input_diff(args.dir1,args.dir2)
    print "\n# Comparing outputs"
    subproblem_diff(args.dir1,args.dir2)
    broken_taxa_diffs(args.dir1,args.dir2)
    synthesis_tree_diffs(args.dir1,args.dir2)
