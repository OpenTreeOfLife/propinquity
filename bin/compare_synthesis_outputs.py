# Given two directories of synthesis outputs, compares them
# Assumes that docs have been generated using `make html` and that
# index.json files exist where they should in various output directories

import simplejson as json
import argparse
import glob,os,re
import requests

# generic function to compare two lists: number of items in each,
# items in first but not second and items in second but not first
# if verbose = True, then print contents of lists, not just number diffs
def compare_lists(type,list1,list2,verbose=False):
    s1 = set(list1)
    s2 = set(list2)
    if s1 != s2:
        print "{t}: ".format(t=type)
        # simple length check
        if len(s1) != len(s2):
            print " {l1} in run1; {l2} in run2".format(
                l1=len(s1),l2=len(s2)
                )
        common = s1.intersection(s2)
        if len(common) > 0:
            print " in common = {l}".format(t=type,l=len(common))
        diff1 = s1.difference(s2)
        if len(diff1) > 0:
            print " in run1 but not run2 = {l}".format(t=type,l=len(diff1))
            if (verbose):
                print " {t} in run1 but not run2:".format(t=type)
                print ', '.join(diff1)
        diff2 = s2.difference(s1)
        if len(diff2) > 0:
            print " in run2 but not run1 = {l}".format(t=type,l=len(diff2))
            if (verbose):
                print " {t} in run2 but not run1:".format(t=type)
                print ', '.join(diff2)
        return 1
    else:
        print "{t}: no differences".format(t=type)
        return 0

# list of collections, list of trees, compare SHAs
# look at phylo_snapshot/concrete_rank_collection.json for each run
def config_diffs(run1,run2):
    # get the data from both top-level index.json files
    jsonfile = "{d}/index.json".format(d=run1)
    jsondata1 = json.load(open(jsonfile, 'r'))['config']
    jsonfile = "{d}/index.json".format(d=run2)
    jsondata2 = json.load(open(jsonfile, 'r'))['config']

    countmismatch = 0
    # do ott versions match
    ott1 = jsondata1['ott_version']
    ott2 = jsondata2['ott_version']
    if (ott1 != ott2):
        print "run1 ott ({v1}) != run2 ott ({v2})".format(v1=ott1,v2=ott2)

    # do roots match
    root1 = int(jsondata1["root_ott_id"])
    root2 = int(jsondata2["root_ott_id"])
    if root1 != root2:
        print "root id1 ({r1}) != root id2 ({r2})".format(r1=root1,r2=root2)
        countmismatch += 1

    # do collections match
    collections1 = jsondata1["collections"]
    collections2 = jsondata2["collections"]
    if (compare_lists("collections",collections1,collections2,False)):
        countmismatch += 1
        print "{d} collections: {c}".format(d=run1,c=collections1)
        print "{d} collections: {c}".format(d=run2,c=collections2)

    # do flags match
    flags1 = jsondata1["taxonomy_cleaning_flags"]
    flags2 = jsondata2["taxonomy_cleaning_flags"]
    countmismatch += compare_lists("flags",flags1,flags2,True)

    if (countmismatch == 0):
        print "no differences in root id, collections, or flags"

# check the lists of input trees
# does not check SHAs, just study@tree lists
def phylo_input_diff(run1,run2):
    # get the data from the phylo_input study_tree_pairs.txt files
    treefile = "{d}/phylo_input/study_tree_pairs.txt".format(d=run1)
    treedata1 = open(treefile, 'r').read().splitlines()
    treefile = "{d}/phylo_input/study_tree_pairs.txt".format(d=run2)
    treedata2 = open(treefile, 'r').read().splitlines()
    countmismatch = 0
    countmismatch += compare_lists("input trees",treedata1,treedata2,True)

    # check lists of non-empty tree files after cleaning
    searchstr = "{d}/cleaned_phylo/*[0-9].tre".format(d=run1)
    nonempty1 = []
    for f in glob.glob(searchstr):
        if os.stat(f).st_size != 0:
            nonempty1.append(os.path.basename(f))
    searchstr = "{d}/cleaned_phylo/*[0-9].tre".format(d=run2)
    nonempty2 = []
    for f in glob.glob(searchstr):
        if os.stat(f).st_size != 0:
            nonempty2.append(os.path.basename(f))
    countmismatch += compare_lists('non-empty trees',nonempty1,nonempty2,False)

    if (countmismatch == 0):
        print "no differences in input trees"

# number (and size) of subproblems
def subproblem_diff(run1,run2):
    # number of subproblems
    subpfile = "{d}/subproblems/subproblem-ids.txt".format(d=run1)
    subproblems1 = open(subpfile, 'r').read().splitlines()
    subpfile = "{d}/subproblems/subproblem-ids.txt".format(d=run2)
    subproblems2 = open(subpfile, 'r').read().splitlines()
    countmismatch = 0
    countmismatch += compare_lists("subproblems",subproblems1,subproblems2,False)

# Summary of subproblem size distributions
# Relevent file is subproblem_solutions/solution-degree-distributions.txt
def subproblem_distributions(run1,run2):
    fn = "subproblem_solutions/solution-degree-distributions.txt"
    datafile1 = "{d}/{f}".format(d=run1,f=fn)
    data1 = read_subproblem_file(datafile1)
    datafile2 = "{d}/{f}".format(d=run2,f=fn)
    data2 = read_subproblem_file(datafile2)
    # summarize based on some arbitrary limits on ntips
    # trivial < 3, small < 20, med < 100-499, large > 500
    limits = [3,20,500]

    print "subproblem size summary:"
    print " run,trivial,small,med,large"
    print " ---------------------------"
    size_summary("run1",limits,data1)
    size_summary("run2",limits,data2)

def size_summary(run,limits,data):
    summary = {'trivial':0,'small':0, 'med':0, 'large':0}
    for tree in data.keys():
        size = int(data[tree])
        if size<limits[0]:
            summary['trivial'] += 1
        elif size<limits[1]:
            summary['small'] += 1
        elif size<limits[2]:
            summary['med'] += 1
        else:
            summary['large'] += 1
    summary_str = " {r},{a},{b},{c},{d}".format(
        r = run,
        a=summary['trivial'],
        b=summary['small'],
        c=summary['med'],
        d=summary['large']
    )
    print summary_str

# Parsing logic from gen_degree_dist fn in document_outputs.py
# return dict where keys are subproblems and values are number of tips
def read_subproblem_file(fn):
    found_tree = False
    data = {}
    currentTree = ""
    with open(fn, 'rU') as inp:
        for line in inp:
            line = line.strip()
            if line.endswith('tre'):
                currentTree = line
                found_tree = True
            if found_tree:
                if line.startswith('0'):
                    row = line.split()
                    data[currentTree] = row[1]
                    currentTree = False
    return data

def synthesis_tree_diffs(run1,run2):
# file of interest is labelled_supertree/input_output_stats.json
    jsonfile = "{d}/labelled_supertree/input_output_stats.json".format(d=run1)
    data1 = json.load(open(jsonfile, 'r'))
    jsonfile = "{d}/labelled_supertree/input_output_stats.json".format(d=run2)
    data2 = json.load(open(jsonfile, 'r'))
    print "\n# Synthetic tree summary"
    print "statistic,run1,run2,difference"
    print "-------------------------------"
    # number of taxonomy tips
    tips1 = data1['output']['num_leaves_added']
    tips2 = data2['output']['num_leaves_added']
    diff = int(tips2-tips1)
    print "taxonomy tips,{n1},{n2},{d}".format(n1=tips1,n2=tips2, d=diff)

    # number of phylogeny leaves
    tips1 = data1['input']['num_solution_leaves']
    tips2 = data2['input']['num_solution_leaves']
    diff = int(tips2-tips1)
    print "phylogeny tips,{n1},{n2},{d}".format(n1=tips1,n2=tips2, d=diff)

    # resolved nodes
    nodes1 = data1['input']['num_solution_splits']
    nodes2 = data2['input']['num_solution_splits']
    diff = int(nodes2-nodes1)
    print "forking nodes,{n1},{n2},{d}".format(n1=nodes1,n2=nodes2,d=diff)

    # broken taxa
    taxa1 = data1['output']['num_taxa_rejected']
    taxa2 = data2['output']['num_taxa_rejected']
    diff = int(taxa2-taxa1)
    print "broken taxa,{n1},{n2},{d}".format(n1=taxa1,n2=taxa2,d=diff)

def broken_taxa_diffs(run1,run2,names=False):
# file of interest is labelled_supertree/broken_taxa.json
    jsonfile = "{d}/labelled_supertree/broken_taxa.json".format(d=run1)
    broken_taxa1 = json.load(open(jsonfile, 'r'))['non_monophyletic_taxa'].keys()
    jsonfile = "{d}/labelled_supertree/broken_taxa.json".format(d=run2)
    broken_taxa2 = json.load(open(jsonfile, 'r'))['non_monophyletic_taxa'].keys()
    countmismatch = 0
    countmismatch += compare_lists("broken taxa",broken_taxa1,broken_taxa2,True)
    if (names):
        s1 = set(broken_taxa1)
        s2 = set(broken_taxa2)
        # names in 2 but not in 1 (the 'newly broken names')
        diff = s2.difference(s1)
        if len(diff) > 0:
            print "broken taxa in run2:"
            #broken_names={}
            for i in diff:
                (name,rank)=get_taxon_details(i)
                print "{id}\t{n}\t{r}".format(id=i,n=name,r=rank)
                # if (taxon_name):
                #     broken_names[i]=taxon_name

# note that ottid is in form 'ott####'
def get_taxon_details(ottid):
    pattern = re.compile(r'ott')
    int_id = re.sub(pattern,'',ottid)
    method_url = "https://api.opentreeoflife.org/v3/taxonomy/taxon_info"
    header = {'content-type':'application/json'}
    payload = {"ott_id":int_id}
    r = requests.post(method_url,headers=header,data=json.dumps(payload))
    try:
        taxon_name = r.json()['name']
        rank = r.json()["rank"]
        return (taxon_name,rank)
    except KeyError:
        print "no name returned for {id}".format(id=ottid)
    #print '{i}:{n}'.format(i=ottid,n=taxon_name)

if __name__ == "__main__":
    # get command line arguments (the two directories to compare)
    parser = argparse.ArgumentParser(description='set up database tables')
    parser.add_argument('run1',
        help='path to the first output directory'
        )
    parser.add_argument('run2',
        help='path to the second output directory'
        )
    parser.add_argument('-b',
        dest='print_broken_taxa',
        action='store_true',
        help='whether to print info on newly-broken taxa'
        )
    args = parser.parse_args()
    print "run 1 output: {d}".format(d=args.run1)
    print "run 2 output: {d}".format(d=args.run2)
    print "\n# Comparing inputs"
    config_diffs(args.run1,args.run2)
    phylo_input_diff(args.run1,args.run2)
    print "\n# Comparing subproblems"
    subproblem_diff(args.run1,args.run2)
    subproblem_distributions(args.run1,args.run2)
    print "\n# Comparing broken taxa"
    broken_taxa_diffs(args.run1,args.run2,args.print_broken_taxa)
    synthesis_tree_diffs(args.run1,args.run2)
