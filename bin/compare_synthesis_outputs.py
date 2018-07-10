#!/usr/bin/env python3
# Given two directories of synthesis outputs, compares them
# Assumes that docs have been generated for each run using `make html`
# Has options for quick checks, as well as formatted output for use in
#  release notes

import json
import argparse
import glob,os,re,csv
import requests
import peyotl.ott as ott
import subprocess
from collections import defaultdict


# From reference-taxonomy:org/opentreeoflife/taxa/Rank.java

_ranks = ["domain",
         "superkingdom",
         "kingdom",
         "subkingdom",
         "division",            # h2007
         "infrakingdom",        # worms
         "superphylum",
         "phylum",
         "subphylum",
         "infraphylum",         # worms
         "subdivision",         # worms
         "superclass",
         "class",
         "subclass",
         "infraclass",
         "subterclass",         # worms Colobognatha
         "cohort",              # NCBI Polyneoptera
         "superorder",
         "order",
         "suborder",
         "infraorder",
         "parvorder",
         "section",             # worms
         "subsection",          # worms
         "superfamily",
         "family",
         "subfamily",
         "supertribe",          # worms
         "tribe",
         "subtribe",
         "genus",
         "subgenus",
         "species group",
         "species subgroup",
         "species",
         "infraspecificname",
         "subspecies",
         "natio",               # worms
         "variety",
         "varietas",
         "subvariety",
         "form",                # 2016 GBIF
         "forma",
         "subform",
         "cluster",
          "no rank - terminal"
        ];

def rank_2_num_dict(ranks):
    i=0
    rank_dict = {}
    for rank in _ranks:
        rank_dict[rank] = i
        i += 1
    return rank_dict

rank_of_rank = rank_2_num_dict(_ranks);

def broken_taxa_diffs(bt1,bt2,verbose):
    compare_lists("Broken taxa",bt1,bt2,verbose)

# writes details of the broken taxa to a file that can be input by
# report_on_broken_taxa.py
def newly_broken_taxa_report(run1,run2):
    # load local copy of OTT
    print("Loading OTT...", end='',flush=True);
    taxonomy = ott.OTT()
    id2names = taxonomy.ott_id_to_names
    id2ranks = taxonomy.ott_id_to_ranks
    print("done.");

    # NOTE: This section gets a rank for unranked nodes by looking at their descendants
    #       If we don't do this, then we don't see Fungi being broken, since Nucletmycea
    #         stands in for Fungi, and Nucletmycea has no rank.
    print("Getting minimal ranks for unranked nodes...",end='',flush=True);
    preorder=[]
    for key,value in taxonomy.preorder2ott_id.items():
        if isinstance(key,int):
            preorder.append(value)
    ott_id2par_ott_id = taxonomy.ott_id2par_ott_id

    for ottID in reversed(preorder):
        parent = ott_id2par_ott_id[ottID]
        if parent is None:
            continue
        if id2ranks[parent] == "no rank" or (rank_of_rank[id2ranks[parent]] > rank_of_rank[id2ranks[ottID]]):
            id2ranks[parent] = id2ranks[ottID]
    print("done.");


    # print details of names in 2 but not in 1 (the 'newly broken names')
    bt1=set(run1.broken_taxa)
    bt2=set(run2.broken_taxa)
    diff = bt2.difference(bt1)
    broken_taxa_filename = 'broken_taxa_report.csv'
    print("printing details of {x} broken taxa to {f}".format(
        x=len(diff),
        f=broken_taxa_filename
        ))
    print("using OTT version {v}".format(v=taxonomy.version))

    victims = defaultdict(int)
    victims_rank = defaultdict(lambda: defaultdict(int))
    sole_victims = defaultdict(int)
    sole_victims_rank = defaultdict(lambda: defaultdict(int))
    with open(broken_taxa_filename, 'w') as f:
        for ottID in diff:
            # strip off the 'ott' part
            pattern = re.compile(r'ott')
            int_id = int(re.sub(pattern,'',ottID))
            name = "no name"
            rank = "no rank"
            if int_id in id2names:
                name = id2names[int_id]
                if (isinstance(name,tuple)):
                    name = name[0]
                if int_id in id2ranks:
                    rank = id2ranks[int_id]
            f.write("{i},{n},{r}\n".format(i=int_id,n=name,r=rank))

            if ottID not in run2.contested:
                print("{}: not contested\n".format(ottID))
            else:
                for tree in run2.contested[ottID]:
                    victims[tree] += 1
                    victims_rank[tree][rank] += 1
                    if len(run2.contested[ottID]) == 1:
                        sole_victims[tree] +=1
                        sole_victims_rank[tree][rank] += 1

    f.close()
    print("Here are the {} trees that broke taxa, starting with the most victims:\n".format(len(victims)))
    for tree in sorted(sole_victims, key=sole_victims.get, reverse=True):
        print("{}: {} ( {} )".format(tree, sole_victims[tree], victims[tree]))

        for rank in sorted(victims_rank[tree], key=lambda key:rank_of_rank[key]):
            if rank_of_rank[rank] < rank_of_rank["genus"]:
                print("\u001b[31m   {}\u001b[0m: {} ( {} )".format(rank,sole_victims_rank[tree][rank],victims_rank[tree][rank]))
            else:
                print("   {}: {} / ( {} )".format(rank, sole_victims_rank[tree][rank],victims_rank[tree][rank]))

# generic function to compare two lists: number of items in each,
# items in first but not second and items in second but not first
# if verbose = True, then print contents of lists, not just number diffs
def compare_lists(type,list1,list2,verbose=False):
    s1 = set(list1)
    s2 = set(list2)
    if s1 != s2:
        print("{t}: ".format(t=type))
        # simple length check
        if len(s1) != len(s2):
            print(" {l1} in run1; {l2} in run2".format(
                l1=len(s1),l2=len(s2)
                ))
        common = s1.intersection(s2)
        if len(common) > 0:
            print(" in common = {l}".format(t=type,l=len(common)))
        diff1 = s1.difference(s2)
        if len(diff1) > 0:
            print(" in run1 but not run2 = {l}".format(l=len(diff1)))
            if (verbose):
                print(" {t} in run1 but not run2:".format(t=type))
                print(', '.join(diff1))
        diff2 = s2.difference(s1)
        if len(diff2) > 0:
            print(" in run2 but not run1 = {l}".format(l=len(diff2)))
            if (verbose):
                print(" {t} in run2 but not run1:".format(t=type))
                print(', '.join(diff2))
        return 1
    else:
        print("{t}: no differences".format(t=type))
        return 0

# list of collections, list of trees, compare SHAs
# look at phylo_snapshot/concrete_rank_collection.json for each run
def config_diffs(jsondata1,jsondata2,verbose):
    # do ott versions match
    ott1 = jsondata1['ott_version']
    ott2 = jsondata2['ott_version']
    if (ott1 != ott2):
        print("run1 ott ({v1}) != run2 ott ({v2})".format(v1=ott1,v2=ott2))

    # do roots match
    root1 = int(jsondata1["root_ott_id"])
    root2 = int(jsondata2["root_ott_id"])
    if root1 != root2:
        print("root id1 ({r1}) != root id2 ({r2})".format(r1=root1,r2=root2))

    # do collections match
    collections1 = jsondata1["collections"]
    collections2 = jsondata2["collections"]
    compare_lists("Collections",collections1,collections2,verbose)

    # do flags match
    flags1 = jsondata1["taxonomy_cleaning_flags"]
    flags2 = jsondata2["taxonomy_cleaning_flags"]
    compare_lists("Flags",flags1,flags2,verbose)

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
        print("no name returned for {id}".format(id=ottid))
    #print '{i}:{n}'.format(i=ottid,n=taxon_name)

# check the lists of input trees
# does not check SHAs, just study@tree lists
def phylo_input_diffs(treedata1,treedata2,verbose):
    compare_lists(
        "Input trees",
        treedata1['input_trees'],
        treedata2['input_trees'],
        verbose
        )
    compare_lists(
        'Non-empty trees',
        treedata1['non_empty_trees'],
        treedata2['non_empty_trees'],
        verbose
        )

# given subproblem dicts, compare
def compare_subproblems(subp1,subp2,verbose):
    # compare number of subproblems
    compare_lists(
        "Subproblems",
        subp1['subproblem_list'],
        subp2['subproblem_list'],
        verbose)
    # compare sizes of subproblems
    limits = [3,20,500]
    print("Subproblem size summary:")
    print(" run,trivial,small,med,large")
    print(" ---------------------------")
    size_summary("run1",limits,subp1['subproblem_dist'])
    size_summary("run2",limits,subp2['subproblem_dist'])

def size_summary(label,limits,data):
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
        r = label,
        a=summary['trivial'],
        b=summary['small'],
        c=summary['med'],
        d=summary['large']
    )
    print(summary_str)

def print_table_row(cells):
    print("<tr>")
    print("   <th>{first}</th>".format(first=cells.pop(0)))
    for i in cells:
        print("   <td>{value}</td>".format(value=i))
    print("</tr>")

# outputs the table for the release notes, given input_output_stats and
# subproblem info
def summary_table(io_stats1,io_stats2, subp1, subp2):
    # print header; uses <th> for each cell
    print('<table class="table table-condensed">')
    print('<tr>')
    print('<th><!--statistic-->&nbsp;</th>')
    print('<th>version7.0</th>')
    print('<th>version8.0</th>')
    print('<th>change</th>')

    # read summary files
    # jsonfile = "{d}/labelled_supertree/input_output_stats.json".format(d=run1)
    # data1 = json.load(open(jsonfile, 'r'))
    # jsonfile = "{d}/labelled_supertree/input_output_stats.json".format(d=run2)
    # data2 = json.load(open(jsonfile, 'r'))

    # total tips
    d1 = io_stats1['input']['num_taxonomy_leaves']
    d2 = io_stats2['input']['num_taxonomy_leaves']
    print_table_row(['total tips',d1,d2,d2-d1])

    # tips from phylogeny
    d1 = io_stats1['input']['num_solution_leaves']
    d2 = io_stats2['input']['num_solution_leaves']
    print_table_row(['tips from phylogeny',d1,d2,d2-d1])

    # internal taxonomy nodes
    d1 = io_stats1['input']['num_taxonomy_internals']
    d2 = io_stats2['input']['num_taxonomy_internals']
    print_table_row(['internal nodes in taxonomy',d1,d2,d2-d1])

    # internal phylogeny nodes
    d1 = io_stats1['input']['num_solution_internals']
    d2 = io_stats2['input']['num_solution_internals']
    print_table_row(['internal nodes from phylogeny',d1,d2,d2-d1])

    # broken taxa
    d1 = io_stats1['output']['num_taxa_rejected']
    d2 = io_stats2['output']['num_taxa_rejected']
    print_table_row(['broken taxa',d1,d2,d2-d1])

    # subproblems
    # subpfile = "{d}/subproblems/subproblem-ids.txt".format(d=run1)
    # subproblems1 = open(subpfile, 'r').read().splitlines()
    d1=len(subp1['subproblem_list'])
    # subpfile = "{d}/subproblems/subproblem-ids.txt".format(d=run2)
    # subproblems2 = open(subpfile, 'r').read().splitlines()
    d2=len(subp2['subproblem_list'])
    print_table_row(['subproblems',d1,d2,d2-d1])

    print('</table>')

# given dicts of stats from input_output_stats.json, compare
def synthesis_tree_diffs(io_stats1,io_stats2):
    print("statistic,run1,run2,difference")
    print("-------------------------------")
    # total tips
    tips1 = io_stats1['input']['num_taxonomy_leaves']
    tips2 = io_stats2['input']['num_taxonomy_leaves']
    diff = int(tips2-tips1)
    print("total tips,{n1},{n2},{d}".format(n1=tips1,n2=tips2, d=diff))

    # number of taxonomy tips
    tips1 = io_stats1['output']['num_leaves_added']
    tips2 = io_stats2['output']['num_leaves_added']
    diff = int(tips2-tips1)
    print("taxonomy tips,{n1},{n2},{d}".format(n1=tips1,n2=tips2, d=diff))

    # number of phylogeny leaves
    tips1 = io_stats1['input']['num_solution_leaves']
    tips2 = io_stats2['input']['num_solution_leaves']
    diff = int(tips2-tips1)
    print("phylogeny tips,{n1},{n2},{d}".format(n1=tips1,n2=tips2, d=diff))

    # resolved nodes
    nodes1 = io_stats1['input']['num_solution_splits']
    nodes2 = io_stats2['input']['num_solution_splits']
    diff = int(nodes2-nodes1)
    print("forking nodes,{n1},{n2},{d}".format(n1=nodes1,n2=nodes2,d=diff))

    # broken taxa
    taxa1 = io_stats1['output']['num_taxa_rejected']
    taxa2 = io_stats2['output']['num_taxa_rejected']
    diff = int(taxa2-taxa1)
    print("broken taxa,{n1},{n2},{d}".format(n1=taxa1,n2=taxa2,d=diff))

# object that holds various stats for a synthesis run
class runStatistics(object):
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.config = self.read_config()
        self.input_output_stats = self.read_input_output_stats()
        self.input_trees = self.read_input_trees()
        self.broken_taxa = self.read_broken_taxa()
        self.subproblems = self.read_subproblems()
        self.contested = self.read_contested()
    def read_broken_taxa(self):
        d = os.path.join(self.output_dir, 'labelled_supertree')
        jsonfile = os.path.join(d,'broken_taxa.json')
        lsbt = json.load(open(jsonfile, 'r'))['non_monophyletic_taxa']
        broken_taxa = lsbt.keys() if lsbt else set()
        return broken_taxa
    def read_config(self):
        jsonfile = os.path.join(self.output_dir,'index.json')
        jsondata = json.load(open(jsonfile, 'r'))['config']
        return jsondata
    def read_input_output_stats(self):
        d = os.path.join(self.output_dir, 'labelled_supertree')
        jsonfile = os.path.join(d,'input_output_stats.json')
        jsondata = json.load(open(jsonfile, 'r'))
        return jsondata
    def read_input_trees(self):
        treeblob = { 'input_trees' : [], 'non_empty_trees': [] }

        # read data on input trees
        d = os.path.join(self.output_dir, 'phylo_input')
        treefile = os.path.join(d,'study_tree_pairs.txt')
        treelist = open(treefile, 'r').read().splitlines()
        treeblob['input_trees'] = treelist

        # read data on non-empty trees after pruning
        d = os.path.join(self.output_dir, 'cleaned_phylo')
        searchstr = "{dir}/*[0-9].tre".format(dir=d)
        nonempty = []
        for f in glob.glob(searchstr):
            if os.stat(f).st_size != 0:
                nonempty.append(os.path.basename(f))
        treeblob['non_empty_trees'] = nonempty

        return treeblob
    def read_subproblem_file(self,fn):
        # Parsing logic from gen_degree_dist fn in document_outputs.py
        # return dict where keys are subproblems and values are number of tips
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
    def read_subproblems(self):
        subproblemblob = { 'subproblem_list' : [], 'subproblem_dist': {} }
        d = os.path.join(self.output_dir, 'subproblems')
        subpfile = os.path.join(d,'subproblem-ids.txt')
        subproblems = open(subpfile, 'r').read().splitlines()
        subproblemblob['subproblem_list'] = subproblems
        d = os.path.join(self.output_dir, 'subproblem_solutions')
        subpdistfile = os.path.join(d,'solution-degree-distributions.txt')
        distribution = self.read_subproblem_file(subpdistfile)
        subproblemblob['subproblem_dist'] = distribution
        return subproblemblob
    def read_contested(self):
        contested_file = os.path.join(self.output_dir,'subproblems/contesting-trees.json')
        return json.load(open(contested_file, 'r'))
    def get_taxon_conflict_info(self):
        exemplified_phylo_dir = os.path.join(self.output_dir,'exemplified_phylo')
        taxonomy = os.path.join(exemplified_phylo_dir,'regraft_cleaned_ott.tre')
        path = os.path.join(exemplified_phylo_dir,'*_*@*.tre')
        trees = glob.glob(os.path.join(exemplified_phylo_dir,'*_*@*.tre'))
        from subprocess import DEVNULL
        output = subprocess.check_output(['otc-annotate-synth'] + [taxonomy] + trees, stderr=DEVNULL)
        j = json.loads(output)['nodes']
        j2 = {}
        pattern = re.compile(r'.*(ott.*)$')
        for key in j:
            m = re.search(pattern, key)
            if m is not None:
                key2 = m.group(1)
                j2[key2] = j[key]
            else:
                raise ValueError("Key {} doesn't match!".format(key))
        return j2

if __name__ == "__main__":
    # get command line arguments (the two directories to compare)
    parser = argparse.ArgumentParser(description='compare synthesis outputs')
    parser.add_argument('run1',
        help='path to the first (older) output directory'
        )
    parser.add_argument('run2',
        help='path to the second (newer) output directory'
        )
    parser.add_argument('-b',
        dest='print_broken_taxa',
        action='store_true',
        help='print info on newly-broken taxa; default false'
        )
    parser.add_argument('-t',
        dest='print_summary_table',
        action='store_true',
        help='print summary table for release notes; default false'
        )
    parser.add_argument('-v',
        dest='verbose',
        action='store_true',
        help='print details on diffs; default false'
        )
    args = parser.parse_args()
    print("run 1 output: {d}".format(d=args.run1))
    print("run 2 output: {d}".format(d=args.run2))

    # get stats object for each run
    run1 = runStatistics(args.run1)
    run2 = runStatistics(args.run2)

    print("\n# Comparing inputs")
    config_diffs(run1.config,run2.config,args.verbose)
    phylo_input_diffs(run1.input_trees,run2.input_trees,args.verbose)

    print("\n# Comparing subproblems")
    compare_subproblems(run1.subproblems,run2.subproblems,args.verbose)

    print("\n# Comparing broken taxa")
    broken_taxa_diffs(run1.broken_taxa,run2.broken_taxa,args.verbose)
    if args.print_broken_taxa:
        newly_broken_taxa_report(run1, run2)

    print("\n# Synthetic tree summary")
    #synthesis_tree_diffs(args.run1,args.run2)
    synthesis_tree_diffs(run1.input_output_stats,run2.input_output_stats)
    if args.print_summary_table:
        print("\n#Summary table for release notes")
        summary_table(
            run1.input_output_stats,
            run2.input_output_stats,
            run1.subproblems,
            run2.subproblems
            )
