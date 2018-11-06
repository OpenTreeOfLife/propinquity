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
          "no rank - terminal",
          "no rank"
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

_bold = "\u001b[1m"
_bold_off = "\u001b[21m"
_red = "\u001b[31m"
_reset = "\u001b[0m"
_black = "\u001b[30m"
_green = "\u001b[32m"
_yellow = "\u001b[33m"
_blue = "\u001b[34m"
_magenta = "\u001b[35m"
_cyan = "\u001b[36m"
_white = "\u001b[37m"


def bold(x):
    return _bold + str(x) + _reset

def red(x):
    return _red + str(x) + _reset

def blue(x):
    return _blue + str(x) + _reset

def cyan(x):
    return _cyan + str(x) + _reset

def green(x):
    return _green + str(x) + _reset

def yellow(x):
    return _yellow + str(x) + _reset

    # NOTE: This section gets a rank for unranked nodes by looking at their descendants
    #       If we didn't do this, then we didn't used to see Fungi being broken, since Nucletmycea
    #         stands in for Fungi, and Nucletmycea has no rank.
def rank_unranked_nodes(taxonomy):
    id2ranks = taxonomy.ott_id_to_ranks

    print("  * Getting minimal ranks for unranked nodes ... ",end='',flush=True);
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
    print("done.", flush=True);

    return id2ranks
    

ott_pattern = re.compile(r'ott')
def get_id_from_ottnum(ottnum):
    return int(re.sub(ott_pattern,'',ottnum))

def get_color_rank(rank):
    color_rank = rank
    if rank_of_rank[rank] < rank_of_rank["genus"]:
        color_rank = red(color_rank)
    if rank_of_rank[rank] <= rank_of_rank["infrakingdom"]:
        color_rank = bold(color_rank)
    return color_rank

# Make dicts that index conflict info by [tree] and by [tree][rank]
def get_conflict_info_by_tree(conflict_info, id2ranks):
    tree_conflict = defaultdict(lambda:defaultdict(set))
    tree_conflict_at_rank = defaultdict(lambda:defaultdict(lambda:defaultdict(set)))
    for ott_node,node_conflict in conflict_info.items():
        int_id = get_id_from_ottnum(ott_node)
        rank = id2ranks[int_id]
        for rel, tree_nodes in node_conflict.items():
            for tree, nodes in tree_nodes.items():
                if rel == "conflicts_with":
                    tree_conflict[tree]["conflicts_with"].add(int_id)
                    tree_conflict_at_rank[tree][rank]["conflicts_with"].add(int_id)
                elif rel == "supported_by" or rel == "partial_path_of":
                    tree_conflict[tree]["aligns_to"].add(int_id)
                    tree_conflict_at_rank[tree][rank]["aligns_to"].add(int_id)
                elif rel == "resolved_by":
                    tree_conflict[tree]["resolves"].add(int_id)
                    tree_conflict_at_rank[tree][rank]["resolves"].add(int_id)
    return (tree_conflict, tree_conflict_at_rank)

def union_over_trees(tree_conflict, tree_conflict_at_rank):

    conflict = defaultdict(set)
    for tree in tree_conflict:
        for rel in tree_conflict[tree]:
            conflict[rel].update(tree_conflict[tree][rel])

    conflict_at_rank = defaultdict(lambda:defaultdict(set))
    for tree in tree_conflict_at_rank:
        for rank in tree_conflict_at_rank[tree]:
            for rel in tree_conflict_at_rank[tree][rank]:
                conflict_at_rank[rank][rel].update(tree_conflict_at_rank[tree][rank][rel])

    return (conflict, conflict_at_rank)


def conflict_summary_line(conflict1, conflict2):
    # This asks the wrong question!  I want the second term to be things that ANY tree has conflicted with
    n_newly_broken = len(conflict2["conflicts_with"] - conflict1["conflicts_with"])

    if (n_newly_broken > 0):
        n_newly_broken = bold(yellow(n_newly_broken))

    n_conflicts_with = len(conflict2["conflicts_with"])
    if (n_conflicts_with > 0):
        n_conflicts_with = yellow(n_conflicts_with)

    n_newly_aligns_to = len(conflict2["aligns_to"] - conflict1["aligns_to"])
    if (n_newly_aligns_to > 0):
        n_newly_aligns_to = bold(cyan(n_newly_aligns_to))

    n_aligns_to = len(conflict2["aligns_to"])
    if (n_aligns_to > 0):
        n_aligns_to = cyan(n_aligns_to)

    n_newly_resolves = len(conflict2["resolves"] - conflict1["resolves"])
    if (n_newly_resolves > 0):
        n_newly_resolves = bold(green(n_newly_resolves))

    n_resolves = len(conflict2["resolves"])
    if (n_resolves > 0):
        n_resolves = green(n_resolves)

    return "({}) {} / ({}) {} / ({}) {}".format(n_newly_broken,
                                                n_conflicts_with,

                                                n_newly_aligns_to,
                                                n_aligns_to,

                                                n_newly_resolves,
                                                n_resolves)


# writes details of the broken taxa to a file that can be input by
# report_on_broken_taxa.py
def newly_broken_taxa_report(run1,run2):
    # load local copy of OTT
    print("\nAnalyzing broken taxa:")
    print("  * Loading OTT ... ", end='',flush=True);
    taxonomy = ott.OTT()
    print("done. (Using version {})".format(taxonomy.version), flush=True);

    id2names = taxonomy.ott_id_to_names
    for id in id2names:
        if isinstance(id2names[id],tuple):
            id2names[id] = id2names[id][0]

    id2ranks = rank_unranked_nodes(taxonomy)

    # print details of names in 2 but not in 1 (the 'newly broken names')
    bt1=set(run1.broken_taxa)
    bt2=set(run2.broken_taxa)
    diff = bt2.difference(bt1)
    broken_taxa_filename = 'broken_taxa_report.csv'
    print("  * Printing details of {x} broken taxa to {f}".format(
        x=len(diff),
        f=broken_taxa_filename
        ))

    conflict_status1 = run1.get_taxon_conflict_info()
    conflict_status2 = run2.get_taxon_conflict_info()
#    print(conflict_status1)
#    exit(0)
    with open(broken_taxa_filename, 'w') as f:
        for ottID in diff:
            # 1. Get name and rank for ottID
            int_id = get_id_from_ottnum(ottID)
            name = "no name"
            rank = "no rank"
            if int_id in id2names:
                name = id2names[int_id]
            if int_id in id2ranks:
                rank = id2ranks[int_id]
            f.write("{i},{n},{r}\n".format(i=int_id,n=name,r=rank))


    # We want to know:
    #   For each tree,
    #     For each rank, and for all ranks put together
    #       How many taxa does this tree (a) conflict with, (b) resolve (c) align to
    # Then, for the conflict, we want to know how many of each rank are NEW with run2?
    # Maybe we also want to know how many trees from the same study are being used?

    # tree:
    #   total:  (newly broken) conflicts / resolves / aligns
    #   rank1:  (newly broken) conflicts / resolves / aligns: newly-broken names
    #   rank2:  (newly broken) conflicts / resolves / aligns: newly-broken names
    #   genus:  (newly broken) conflicts / resolves / aligns

    (tree_conflict1,tree_conflict_at_rank1) = get_conflict_info_by_tree(conflict_status1, id2ranks)
    (conflict1,conflict_at_rank1) = union_over_trees(tree_conflict1, tree_conflict_at_rank1)
    (tree_conflict2,tree_conflict_at_rank2) = get_conflict_info_by_tree(conflict_status2, id2ranks)

# FIXME: write out number of duplicate trees per study
# NEW: show aligns_to last
    
    print("Here are the trees in order of NEW broken taxa, then all broken taxa:\n")
    print("\n\n{}: ({}) {} / ({}) {} / ({}) {} ".format("tree",
                                              bold(yellow("change")),
                                              yellow("conflicts_with"),
                                              bold(cyan("change")),
                                              cyan("aligns_to"),
                                              bold(green("change")),
                                              green("resolves")))

    for tree in sorted(tree_conflict2,
                       key=lambda tree:( len(tree_conflict2[tree]["conflicts_with"] - conflict1["conflicts_with"]),
                                         len(tree_conflict2[tree]["conflicts_with"]) ),
                       reverse=True):
        ctree=tree
        if len(tree_conflict2[tree]["conflicts_with"]) > len(tree_conflict2[tree]["aligns_to"]):
            ctree=bold(red(tree))
        print("\n\n{}: {}".format(ctree, conflict_summary_line(conflict1, tree_conflict2[tree])))

        for rank in sorted(tree_conflict_at_rank2[tree], key=lambda key:rank_of_rank[key]):

            c1 = conflict_at_rank1[rank]
            c2 = tree_conflict_at_rank2[tree][rank]

            examples=''
            if rank_of_rank[rank] < rank_of_rank["genus"]:
                examples2 = set()
                for example_id in c2["conflicts_with"] - c1["conflicts_with"]:
                    examples2.add(id2names[example_id])
                if (len(examples2) > 0):
                    examples = '{}'.format(examples2)
                
            n_newly_broken = len(c2["conflicts_with"] - c1["conflicts_with"])

            if (n_newly_broken > 0):
                crank = get_color_rank(rank)
            else:
                crank = rank

            print("   {}: {}    {}".format(crank,
                                           conflict_summary_line(c1, c2),
                                           examples))

    # Find duplicate trees per study
    print ("Studies with duplicate trees:\n\n")
    trees_for_study = defaultdict(set)
    for study_tree in run2.read_input_trees()['input_trees']:
        (study,tree) = study_tree.split('@')
        trees_for_study[study].add(tree)
    for study,trees in trees_for_study.items():
        if len(trees) > 1:
            print("{} : {} : {}".format(study,len(trees),trees))


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
        cmdline = ['otc-annotate-synth'] + [taxonomy] + trees
#        print('cmdline = {}'.format('otc-annotate-synth {} {}'.format(taxonomy,os.path.join(exemplified_phylo_dir,'*_*@*.tre'))))
        print("  * Running otc-annotate-synth to get fuller conflict info on trees and broken taxa ... ",end='',flush=True)
        output = subprocess.check_output(cmdline, stderr=DEVNULL)
        print("done.")
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
