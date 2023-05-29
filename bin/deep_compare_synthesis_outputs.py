#!/usr/bin/env python3
# Given two directories of synthesis outputs, compares them
# Assumes that docs have been generated for each run using `make html`
# Has options for quick checks, as well as formatted output for use in
#  release notes

import argparse
import csv
import glob
import json
import sys
import os
import re
import subprocess
from collections import defaultdict
from dendropy import Tree
from dendropy.calculate import treecompare
import peyotl.ott as ott
from peyotl import read_as_json
import requests

# From reference-taxonomy:org/opentreeoflife/taxa/Rank.java
#    and otcetera/otc/taxonomy/taxonomy.cpp
_ranks = (
    "domain",
    "superkingdom",
    "kingdom",
    "subkingdom",
    "division",  # h2007
    "infrakingdom",  # worms
    "superphylum",
    "phylum",
    "subphylum",
    "infraphylum",  # worms
    "subdivision",  # worms
    "superclass",
    "class",
    "subclass",
    "infraclass",
    "subterclass",  # worms Colobognatha
    "cohort",  # NCBI Polyneoptera
    "subcohort",
    "superorder",
    "order",
    "suborder",
    "infraorder",
    "parvorder",
    "section",  # worms
    "subsection",  # worms
    "superfamily",
    "family",
    "subfamily",
    "supertribe",  # worms
    "tribe",
    "subtribe",
    "genus",
    "subgenus",
    "section",
    "subsection",
    "species group",
    "species subgroup",
    "species",
    "infraspecificname",
    "subspecies",
    "natio",  # worms
    "variety",
    "varietas",
    "subvariety",
    "form",  # 2016 GBIF
    "forma",
    "subform",
    "cluster",
    "no rank - terminal",
    "no rank",
)

rank_of_rank = {rank: i for i, rank in enumerate(_ranks)}

_bold = "\u001b[1m"
_reset = "\u001b[0m"
_red = "\u001b[31m"
_blue = "\u001b[34m"
_cyan = "\u001b[36m"
_green = "\u001b[32m"
_yellow = "\u001b[33m"

bold_f = _bold + "{}" + _reset
red_f = _red + "{}" + _reset
blue_f = _blue + "{}" + _reset
cyan_f = _cyan + "{}" + _reset
green_f = _green + "{}" + _reset
yellow_f = _yellow + "{}" + _reset

HTML_OUT = False
_bold_html = "<b>{}</b>"
_red_html = '<span style="color:red;">{}</span>'
_blue_html = '<span style="color:blue;">{}</span>'
_cyan_html = '<span style="color:cyan;">{}</span>'
_green_html = '<span style="color:green;">{}</span>'
_yellow_html = '<span style="color:yellow;">{}</span>'
HTML_DIR = None

CONFLICT_FMT = "({}) {} / ({}) {} / ({}) {}"
LBL_CONFLICT_FMT = "{}{}: " + CONFLICT_FMT + "{}"


def to_html_out(html_dir=None):
    global bold_f, red_f, blue_f, cyan_f, green_f, yellow_f, HTML_OUT, HTML_DIR
    HTML_OUT = True
    bold_f = _bold_html
    red_f = _red_html
    blue_f = _blue_html
    cyan_f = _cyan_html
    green_f = _green_html
    yellow_f = _yellow_html
    if html_dir:
        HTML_DIR = html_dir
        if not os.path.isdir(HTML_DIR):
            os.mkdir(HTML_DIR)


def bold(x):
    return bold_f.format(x)


def red(x):
    return red_f.format(x)


def blue(x):
    return blue_f.format(x)


def cyan(x):
    return cyan_f.format(x)


def green(x):
    return green_f.format(x)


def yellow(x):
    return yellow_f.format(x)


R1N, R2N = "run1", "run2"


def set_run_names(r1, r2):
    global R1N, R2N
    R1N, R2N = r1, r2


def broken_taxa_diffs(out, bt1, bt2, verbose):
    compare_lists(out, "Broken taxa", bt1, bt2, verbose)


_status_str = sys.stderr


def status(msg, newline=True):
    if newline:
        _status_str.write("{}\n".format(msg))
    else:
        _status_str.write(msg)


def print_header(out, level, line):
    if HTML_OUT:
        t = "h{}".format(level)
        out.write("<{t}>{l}</{t}>\n".format(t=t, l=line))
    else:
        out.write("\n# {}\n".format(line))


def fmt_link(url, text):
    if HTML_OUT:
        return f'<a href="{url}" target="_blank">{text}</a>\n'
    return text

def print_link(out, url, text):
    if HTML_OUT:
        out.write(fmt_link(url, text))
    else:
        print(text)


def print_paragraph(out, line):
    if HTML_OUT:
        out.write("<p>{}</p>\n".format(line))
    else:
        out.write("{}\n".format(line))

def print_list_item(out, line):
    if HTML_OUT:
        out.write("<li>{}</li>\n".format(line))
    else:
        out.write("{}\n".format(line))

def open_list(out):
    if HTML_OUT:
        out.write("<ul>\n")

def close_list(out):
    if HTML_OUT:
        out.write("</ul>\n")

# NOTE: This section gets a rank for unranked nodes by looking at their descendants
#       If we didn't do this, then we didn't used to see Fungi being broken, since Nucletmycea
#         stands in for Fungi, and Nucletmycea has no rank.


def rank_unranked_nodes(taxonomy):
    id2ranks = taxonomy.ott_id_to_ranks
    status("  * Getting minimal ranks for unranked nodes ... ", newline=False)
    preorder = [v for k, v in taxonomy.preorder2ott_id.items() if isinstance(k, int)]
    ott_id2par_ott_id = taxonomy.ott_id2par_ott_id
    for ottID in reversed(preorder):
        parent = ott_id2par_ott_id[ottID]
        if parent is None:
            continue
        if id2ranks[parent] == "no rank" or (
            rank_of_rank[id2ranks[parent]] > rank_of_rank[id2ranks[ottID]]
        ):
            id2ranks[parent] = id2ranks[ottID]
    status("done.")
    return id2ranks


ott_pattern = re.compile(r"ott")


def get_id_from_ottnum(ottnum):
    return int(re.sub(ott_pattern, "", ottnum))


def get_color_rank(rank):
    color_rank = rank
    if rank_of_rank[rank] < rank_of_rank["genus"]:
        color_rank = red(color_rank)
    if rank_of_rank[rank] <= rank_of_rank["infrakingdom"]:
        color_rank = bold(color_rank)
    return color_rank


# Make dicts that index conflict info by [tree] and by [tree][rank]
def get_conflict_info_by_tree(conflict_info, id2ranks):
    tree_conflict = defaultdict(lambda: defaultdict(set))
    tree_conflict_at_rank = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    for ott_node, node_conflict in conflict_info.items():
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
    return tree_conflict, tree_conflict_at_rank


def union_over_trees(tree_conflict, tree_conflict_at_rank):
    conflict = defaultdict(set)
    for tree in tree_conflict:
        for rel in tree_conflict[tree]:
            conflict[rel].update(tree_conflict[tree][rel])

    conflict_at_rank = defaultdict(lambda: defaultdict(set))
    for tree in tree_conflict_at_rank:
        for rank in tree_conflict_at_rank[tree]:
            for rel in tree_conflict_at_rank[tree][rank]:
                conflict_at_rank[rank][rel].update(
                    tree_conflict_at_rank[tree][rank][rel]
                )

    return conflict, conflict_at_rank


def color_conf_summ(data):
    ret = []
    for n, el in enumerate(data):
        if isinstance(el, int) and el < 1:
            ret.append(el)
        else:
            ret.append(decorate[n](el))
    return ret


def conflict_summary_line_data(conflict1, conflict2):
    # This asks the wrong question!  I want the second term to be things that ANY tree has conflicted with
    d2 = conflict2["conflicts_with"] - conflict1["conflicts_with"]
    n_newly_broken = len(d2)
    n_conflicts_with = len(conflict2["conflicts_with"])
    n_newly_aligns_to = len(conflict2["aligns_to"] - conflict1["aligns_to"])
    n_aligns_to = len(conflict2["aligns_to"])
    n_newly_resolves = len(conflict2["resolves"] - conflict1["resolves"])
    n_resolves = len(conflict2["resolves"])
    ret = (
        n_newly_broken,
        n_conflicts_with,
        n_newly_aligns_to,
        n_aligns_to,
        n_newly_resolves,
        n_resolves,
    )
    if not HTML_OUT:
        ret = color_conf_summ(ret)
    return ret


def conflict_summary_line(conflict1, conflict2):
    d = conflict_summary_line_data(conflict1, conflict2)
    return CONFLICT_FMT.format(*d)


# writes details of the broken taxa to a file that can be input by
# report_on_broken_taxa.py
def newly_broken_taxa_report(out, run1, run2):
    # load local copy of OTT
    status("\nAnalyzing broken taxa:")
    status("  * Loading OTT ... ", newline=False)
    taxonomy = ott.OTT()
    status("done. (Using version {})".format(taxonomy.version))
    id2names = taxonomy.ott_id_to_names
    for idk in id2names:
        if isinstance(id2names[idk], tuple):
            id2names[idk] = id2names[idk][0]
    id2ranks = rank_unranked_nodes(taxonomy)

    # print details of names in 2 but not in 1 (the 'newly broken names')
    bt1 = set(run1.broken_taxa)
    bt2 = set(run2.broken_taxa)
    diff = bt2.difference(bt1)
    broken_taxa_fn = "broken_taxa_report.csv"
    btfp = (
        broken_taxa_fn if HTML_DIR is None else os.path.join(HTML_DIR, broken_taxa_fn)
    )
    btf_s = "  * Printing details of {x} broken taxa to {f}"
    btf_s = btf_s.format(x=len(diff), f=btfp)
    status(btf_s)

    conflict_status1 = run1.get_taxon_conflict_info()
    conflict_status2 = run2.get_taxon_conflict_info()
    #    print(conflict_status1)
    #    exit(0)
    with open(btfp, "w", encoding="utf-8") as f:
        for ott_id in diff:
            int_id = get_id_from_ottnum(ott_id)
            name = id2names.get(int_id, "no name")
            rank = id2ranks.get(int_id, "no rank")
            f.write("{i},{n},{r}\n".format(i=int_id, n=name, r=rank))

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

    (tree_conflict1, tree_conflict_at_rank1) = get_conflict_info_by_tree(
        conflict_status1, id2ranks
    )
    (conflict1, conflict_at_rank1) = union_over_trees(
        tree_conflict1, tree_conflict_at_rank1
    )
    (tree_conflict2, tree_conflict_at_rank2) = get_conflict_info_by_tree(
        conflict_status2, id2ranks
    )

    # FIXME: write out number of duplicate trees per study
    # NEW: show aligns_to last
    ret = [
        broken_taxa_fn,
    ]
    if HTML_DIR is not None:
        tbn = "trees_by_new_broken.html"
        out = open(os.path.join(HTML_DIR, tbn), "w", encoding="utf-8")
        ret.append(tbn)

    try:
        print_trees_by_new_broken(
            out,
            run2,
            conflict1,
            conflict_at_rank1,
            tree_conflict2,
            tree_conflict_at_rank2,
            id2names,
        )
    finally:
        if HTML_DIR is not None:
            out.close()
    return ret


decorate = [
    lambda x: bold(yellow(x)),
    yellow,
    lambda x: bold(cyan(x)),
    cyan,
    lambda x: bold(green(x)),
    green,
]


def print_trees_by_new_broken(
    out,
    run2,
    conflict1,
    conflict_at_rank1,
    tree_conflict2,
    tree_conflict_at_rank2,
    id2names,
):
    print_paragraph(
        out, "Here are the trees in order of NEW broken taxa, then all broken taxa:\n"
    )
    second = "by rank" if HTML_OUT else ""
    labels = ["change", "conflicts_with", "change", "aligns_to", "change", "resolves"]
    if not HTML_OUT:
        labels = color_conf_summ(labels)
    headers = (
        [
            "tree",
            second,
        ]
        + labels
        + ["examples"]
    )
    print_table_open(out, text_fmt=LBL_CONFLICT_FMT, headers=headers)

    for tree in sorted(
        tree_conflict2,
        key=lambda t: (
            len(tree_conflict2[t]["conflicts_with"] - conflict1["conflicts_with"]),
            len(tree_conflict2[t]["conflicts_with"]),
        ),
        reverse=True,
    ):
        ctree = tree
        if len(tree_conflict2[tree]["conflicts_with"]) > len(
            tree_conflict2[tree]["aligns_to"]
        ):
            ctree = bold(red(tree))
        cells = (
            [ctree, ""]
            + list(conflict_summary_line_data(conflict1, tree_conflict2[tree]))
            + [""]
        )
        print_table_row(out, text_fmt=LBL_CONFLICT_FMT, cells=cells)
        write_conf_by_rank(
            out, conflict_at_rank1, tree_conflict_at_rank2, tree, id2names
        )
    print_table_close(out)

    # Find duplicate trees per study
    print_header(out, 3, "Studies with duplicate trees")
    trees_for_study = defaultdict(set)
    for study_tree in run2.read_input_trees()["input_trees"]:
        (study, tree) = study_tree.split("@")
        trees_for_study[study].add(tree)
    print_table_open(out, headers=["study", "# trees", "trees"])
    for study, trees in trees_for_study.items():
        if len(trees) > 1:
            print_table_row(out, cells=[study, len(trees), trees])
    print_table_close(out)


def write_conf_by_rank(out, conflict_at_rank1, tree_conflict_at_rank2, tree, id2names):
    for rank in sorted(tree_conflict_at_rank2[tree], key=lambda key: rank_of_rank[key]):
        c1 = conflict_at_rank1[rank]
        c2 = tree_conflict_at_rank2[tree][rank]

        examples = ""
        if rank_of_rank[rank] < rank_of_rank["genus"]:
            examples2 = set()
            for example_id in c2["conflicts_with"] - c1["conflicts_with"]:
                examples2.add(id2names[example_id])
            if len(examples2) > 0:
                examples = "{}".format(examples2)
        n_newly_broken = len(c2["conflicts_with"] - c1["conflicts_with"])
        crank = get_color_rank(rank) if n_newly_broken > 0 else rank
        cells = (
            ["", "  " + crank] + list(conflict_summary_line_data(c1, c2)) + [examples]
        )
        print_table_row(out, text_fmt=LBL_CONFLICT_FMT, cells=cells)


# generic function to compare two lists: number of items in each,
# items in first but not second and items in second but not first
# if verbose = True, then print contents of lists, not just number diffs
def compare_lists(out, rtype, list1, list2, verbose=False, list_to_str=None):
    if list_to_str is None:
        list_to_str = lambda ls: ", ".join(ls)

    s1 = set(list1)
    s2 = set(list2)
    if s1 == s2:
        print_paragraph(out, f"{rtype}: no differences")
        return 0
    print_header(out, 2, f"{rtype}: ")
    if len(s1) != len(s2):
        m = f" {len(s1)} in {R1N}; {len(s2)} in {R2N}"
        print_paragraph(out, m)
    common = s1.intersection(s2)
    print_paragraph(out, f" {len(common)} in common")
    diff1 = s1.difference(s2)
    print_paragraph(out, f" {len(diff1)} in {R1N} but not {R2N}")
    if verbose:
        print_paragraph(out, f" {rtype} in {R1N} but not {R2N}:")
        print_paragraph(out, list_to_str(diff1))
    diff2 = s2.difference(s1)
    print_paragraph(out, f" {len(diff2)} in {R2N} but not {R1N}")
    if verbose:
        print_paragraph(out, f" {rtype} in {R2N} but not {R1N}:")
        print_paragraph(out, list_to_str(diff2))
    return 1


_TREE_URL_TEMPLATE = (
    "https://tree.opentreeoflife.org/curator/study/view/{study}/?tab=home&tree={tree}"
)
_TREE_A_TEMPLATE = '<a target="_blank", href="{u}">{n}</a>'


def tree_name_to_link(tree_name):
    s = tree_name.split("@")
    assert len(s) == 2
    study, tree = s
    return _TREE_URL_TEMPLATE.format(study=study, tree=tree)


def display_tree_name(tree_name):
    if HTML_OUT:
        u = tree_name_to_link(tree_name)
        r = _TREE_A_TEMPLATE.format(u=u, n=tree_name)
        return r
    else:
        return tree_name


def treelist_to_display_str(tree_list):
    dsl = []
    for tn in tree_list:
        dsl.append(display_tree_name(tn))
    return ", ".join(dsl)


# check the lists of input trees
# does not check SHAs, just study@tree lists
def phylo_input_diffs(out, treedata1, treedata2, verbose):
    t = "input_trees"
    compare_lists(
        out,
        "Input trees",
        treedata1[t],
        treedata2[t],
        verbose,
        list_to_str=treelist_to_display_str,
    )
    t = "non_empty_trees"
    compare_lists(
        out,
        "Non-empty trees",
        treedata1[t],
        treedata2[t],
        verbose,
        list_to_str=treelist_to_display_str,
    )


def print_table_open(out, headers, text_fmt=None):
    if HTML_OUT:
        out.write('<table class="table table-condensed">\n')
        out.write(
            "<tr>{}</tr>\n".format("".join(["<th>{}</th>".format(i) for i in headers]))
        )
        return
    if text_fmt:
        line = text_fmt.format(*headers)
    else:
        line = ",".join(headers)
    dashes = "-" * len(line)
    out.write(" {}\n".format(line))
    out.write(" {}\n".format(dashes))


def print_table_row(out, cells, text_fmt=None):
    if HTML_OUT:
        out.write(
            "<tr>{}</tr>\n".format("".join(["<td>{}</td>".format(i) for i in cells]))
        )
        return
    if text_fmt:
        summary_str = text_fmt.format(*cells)
    else:
        summary_str = " {}".format(",".join([str(i) for i in cells]))
    print_paragraph(out, summary_str)


def print_table_close(out):
    if HTML_OUT:
        out.write("</table>\n")


# given subproblem dicts, compare
def compare_subproblems(out, subp1, subp2, verbose):
    # compare number of subproblems
    compare_lists(
        out, "Subproblems", subp1["subproblem_list"], subp2["subproblem_list"], verbose
    )
    # compare sizes of subproblems
    limits = [3, 20, 500]
    print_header(out, 2, "Subproblem size summary:")
    print_table_open(out, headers=["run", "trivial", "small", "med", "large"])
    size_summary(out, R1N, limits, subp1["subproblem_dist"])
    size_summary(out, R2N, limits, subp2["subproblem_dist"])
    print_table_close(out)


def size_summary(out, label, limits, data):
    trivial, small, med, large = 0, 0, 0, 0
    for tree in data.keys():
        size = int(data[tree])
        if size < limits[0]:
            trivial += 1
        elif size < limits[1]:
            small += 1
        elif size < limits[2]:
            med += 1
        else:
            large += 1
    print_table_row(out, cells=(label, trivial, small, med, large))


# outputs the table for the release notes, given input_output_stats and
# subproblem info
def summary_table(out, io_stats1, io_stats2, subp1, subp2):
    global HTML_OUT
    # print header; uses <th> for each cell

    headers = ["<!--statistic-->&nbsp;", R1N, R2N, "change"]

    # read summary files
    # jsonfile = "{d}/labelled_supertree/input_output_stats.json".format(d=run1)
    # data1 = json.load(open(jsonfile, 'r'))
    # jsonfile = "{d}/labelled_supertree/input_output_stats.json".format(d=run2)
    # data2 = json.load(open(jsonfile, 'r'))
    former_HTML_OUT = HTML_OUT
    try:
        print_table_open(out, headers=headers)
        # total tips
        d1 = io_stats1["input"]["num_taxonomy_leaves"]
        d2 = io_stats2["input"]["num_taxonomy_leaves"]
        print_table_row(out, cells=["total tips", d1, d2, d2 - d1])

        # tips from phylogeny
        d1 = io_stats1["input"]["num_solution_leaves"]
        d2 = io_stats2["input"]["num_solution_leaves"]
        print_table_row(out, cells=["tips from phylogeny", d1, d2, d2 - d1])

        # internal taxonomy nodes
        d1 = io_stats1["input"]["num_taxonomy_internals"]
        d2 = io_stats2["input"]["num_taxonomy_internals"]
        print_table_row(out, cells=["internal nodes in taxonomy", d1, d2, d2 - d1])

        # internal phylogeny nodes
        d1 = io_stats1["input"]["num_solution_internals"]
        d2 = io_stats2["input"]["num_solution_internals"]
        print_table_row(out, cells=["internal nodes from phylogeny", d1, d2, d2 - d1])

        # broken taxa
        d1 = io_stats1["output"]["num_taxa_rejected"]
        d2 = io_stats2["output"]["num_taxa_rejected"]
        print_table_row(out, cells=["broken taxa", d1, d2, d2 - d1])

        # subproblems
        d1 = len(subp1["subproblem_list"])
        d2 = len(subp2["subproblem_list"])
        print_table_row(out, cells=["subproblems", d1, d2, d2 - d1])
        print_table_close(out)
    finally:
        HTML_OUT = former_HTML_OUT


# given dicts of stats from input_output_stats.json, compare
def synthesis_tree_diffs(out, io_stats1, io_stats2):
    print_table_open(out, headers=["statistic", R1N, R2N, "difference"])
    # total tips
    tips1 = io_stats1["input"]["num_taxonomy_leaves"]
    tips2 = io_stats2["input"]["num_taxonomy_leaves"]
    diff = int(tips2 - tips1)
    print_table_row(out, cells=("total tips", tips1, tips2, diff))

    # number of taxonomy tips
    tips1 = io_stats1["output"]["num_leaves_added"]
    tips2 = io_stats2["output"]["num_leaves_added"]
    diff = int(tips2 - tips1)
    print_table_row(out, cells=("taxonomy tips", tips1, tips2, diff))

    # number of phylogeny leaves
    tips1 = io_stats1["input"]["num_solution_leaves"]
    tips2 = io_stats2["input"]["num_solution_leaves"]
    diff = int(tips2 - tips1)
    print_table_row(out, cells=("phylogeny tips", tips1, tips2, diff))

    # resolved nodes
    nodes1 = io_stats1["input"]["num_solution_splits"]
    nodes2 = io_stats2["input"]["num_solution_splits"]
    diff = int(nodes2 - nodes1)
    print_table_row(out, cells=("forking nodes", nodes1, nodes2, diff))

    # broken taxa
    taxa1 = io_stats1["output"]["num_taxa_rejected"]
    taxa2 = io_stats2["output"]["num_taxa_rejected"]
    diff = int(taxa2 - taxa1)
    print_table_row(out, cells=("broken taxa", taxa1, taxa2, diff))
    print_table_close(out)


# object that holds various stats for a synthesis run
class RunStatistics(object):
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self._config = None
        self._input_output_stats = None
        self._input_trees = None
        self._broken_taxa = None
        self._subproblems = None
        self._contested = None

    @property
    def config(self):
        if self._config is None:
            self._config = self.read_config()
        return self._config
    @property
    def input_output_stats(self):
        if self._input_output_stats is None:
            self._input_output_stats = self.read_input_output_stats()
        return self._input_output_stats
    @property
    def input_trees(self):
        if self._input_trees is None:
            self._input_trees = self.read_input_trees()
        return self._input_trees
    @property
    def broken_taxa(self):
        if self._broken_taxa is None:
            self._broken_taxa = self.read_broken_taxa()
        return self._broken_taxa
    @property
    def subproblems(self):
        if self._subproblems is None:
            self._subproblems = self.read_subproblems()
        return self._subproblems
    @property
    def contested(self):
        if self._contested is None:
            self._contested = self.read_contested()
        return self._contested

    def filepath_to(self, rel_path, required=True):
        rps = os.path.split(rel_path)
        fp = os.path.join(self.output_dir, *rps)
        if required and not os.path.exists(fp):
            raise RuntimeError(f"Required path {fp} not found")
        return fp

    def read_broken_taxa(self):
        d = os.path.join(self.output_dir, "labelled_supertree")
        jsonfile = os.path.join(d, "broken_taxa.json")
        lsbt = json.load(open(jsonfile, "r"))["non_monophyletic_taxa"]
        broken_taxa = lsbt.keys() if lsbt else set()
        return broken_taxa

    def read_config(self):
        jsonfile = os.path.join(self.output_dir, "index.json")
        jsondata = json.load(open(jsonfile, "r"))["config"]
        return jsondata

    def read_input_output_stats(self):
        d = os.path.join(self.output_dir, "labelled_supertree")
        jsonfile = os.path.join(d, "input_output_stats.json")
        jsondata = json.load(open(jsonfile, "r"))
        return jsondata

    def read_input_trees(self):
        treeblob = {"input_trees": [], "non_empty_trees": []}

        # read data on input trees
        d = os.path.join(self.output_dir, "phylo_input")
        treefile = os.path.join(d, "study_tree_pairs.txt")
        treelist = open(treefile, "r").read().splitlines()
        treeblob["input_trees"] = treelist

        # read data on non-empty trees after pruning
        d = os.path.join(self.output_dir, "cleaned_phylo")
        searchstr = "{dir}/*[0-9].tre".format(dir=d)
        nonempty = []
        for f in glob.glob(searchstr):
            if os.stat(f).st_size != 0:
                bn = os.path.basename(f)
                if bn.startswith("tree_"):
                    bn = bn[5:]
                nonempty.append(bn)
        treeblob["non_empty_trees"] = nonempty

        return treeblob

    def read_subproblem_file(self, fn):
        # Parsing logic from gen_degree_dist fn in document_outputs.py
        # return dict where keys are subproblems and values are number of tips
        found_tree = False
        data = {}
        currentTree = ""
        with open(fn, "r") as inp:
            for line in inp:
                line = line.strip()
                if line.endswith("tre"):
                    currentTree = line
                    found_tree = True
                if found_tree:
                    if line.startswith("0"):
                        row = line.split()
                        data[currentTree] = row[1]
                        currentTree = False
        return data

    def read_subproblems(self):
        subproblemblob = {"subproblem_list": [], "subproblem_dist": {}}
        d = os.path.join(self.output_dir, "subproblems")
        subpfile = os.path.join(d, "subproblem-ids.txt")
        if not os.path.exists(subpfile):
            subpfile = os.path.join(d, "dumped_subproblem_ids.txt")
        subproblems = open(subpfile, "r").read().splitlines()
        subproblemblob["subproblem_list"] = subproblems
        d = os.path.join(self.output_dir, "subproblem_solutions")
        subpdistfile = os.path.join(d, "solution-degree-distributions.txt")
        distribution = self.read_subproblem_file(subpdistfile)
        subproblemblob["subproblem_dist"] = distribution
        return subproblemblob

    def read_contested(self):
        contested_file = os.path.join(
            self.output_dir, "subproblems/contesting-trees.json"
        )
        if not os.path.exists(contested_file):
            contested_file = os.path.join(
                self.output_dir, "subproblems/contesting_trees.json"
            )
        return json.load(open(contested_file, "r"))

    def get_taxon_conflict_info(self):
        exemplified_phylo_dir = os.path.join(self.output_dir, "exemplified_phylo")
        taxonomy = os.path.join(exemplified_phylo_dir, "regraft_cleaned_ott.tre")
        trees_unf = glob.glob(os.path.join(exemplified_phylo_dir, "*_*@*.tre"))
        trees = [i for i in trees_unf if not os.path.split(i)[-1].startswith("tree_")]
        from subprocess import DEVNULL

        cmdline = ["otc-annotate-synth"] + [taxonomy] + trees
        #        print('cmdline = {}'.format('otc-annotate-synth {} {}'.format(taxonomy, os.path.join(exemplified_phylo_dir, '*_*@*.tre'))))
        status(
            "  * Running otc-annotate-synth to get fuller conflict info on trees and broken taxa ... ",
            newline=False,
        )
        output = subprocess.check_output(cmdline, stderr=DEVNULL)
        status("done.")
        j = json.loads(output)["nodes"]
        j2 = {}
        pattern = re.compile(r".*(ott.*)$")

        # otc-annotate-synth doesn't handle incertae sedis yet.  Therefore some input trees appear to conflict
        # with taxa when they actually don't conflict.  The current solution is to only list conflicts for
        # taxa that are actually broken.
        # not_really_broken = set()
        for key, annotations in j.items():
            m = re.search(pattern, key)
            if m is None:
                raise ValueError("Key {} doesn't match!".format(key))
            taxon = m.group(1)
            if taxon not in self.broken_taxa:
                annotations.pop("conflicts_with", None)
            j2[taxon] = annotations
        return j2

def _find_node_in_cleaned_phylo_json(blob, nd_id):
    for key, val in blob.items():
        if key == "revised_ingroup_node":
            if nd_id == val:
                return key
            continue
        node_list = val.get("nodes", [])
        if nd_id in node_list:
            return key
    return 'INCLUDED'

def _find_edge_in_cleaned_phylo_json(blob, edge_id):
    for key, val in blob.items():
        if key == "revised_ingroup_node":
            continue
        edge_list = val.get("edges", [])
        if edge_id in edge_list:
            return key
    return 'INCLUDED'

def get_tree_and_otus_from_nexson(nex, tree_id):
    """Returns the tree_blob, and otuById blob for the tree_id
    
    or None, None if tree_id is not found.
    """
    
    nexml = nex['nexml']
    tree_cont = nexml["treesById"]
    otu_cont = nexml["otusById"]
    tree, otu = None, None
    for trees_id, blob in tree_cont.items():
        tblobs = blob['treeById']
        tree_blob = tblobs.get(tree_id)
        if tree_blob is not None:
            return tree_blob, otu_cont[blob["@otus"]]['otuById']
    return None, None
def _list_elements(out, str_list):
    if str_list:
        open_list(out)
        for el in str_list:
            print_list_item(out, el)
        close_list(out)

_SNAPSHOT_JSON_TEMPLATE = 'phylo_snapshot/tree_{study_tree}.json'
_CLEANED_PHYLO_JSON_TEMPLATE = 'cleaned_phylo/tree_{study_tree}.json'
_CLEANED_PHYLO_TREE_TEMPLATE = 'cleaned_phylo/tree_{study_tree}.tre'
_EXEMPLAR_PHYLO_TREE_TEMPLATE = 'exemplified_phylo/{study_tree}.tre'

class RunComparison(object):
    def __init__(self, run1, run2, outstream, verbose=False, html_dir=None):
        self.run1 = run1
        self.run2 = run2
        self.out = outstream
        self.verbose = verbose
        self.html_dir = html_dir
        self.ott_to_depth_fp = None

    def input_diffs(self):
        print_header(self.out, 1, "Comparing inputs")
        self.config_diffs()
        if False:
            self.phylo_input_diffs()
        print("Skipping phylo_input_diffs", file=sys.stderr)
        self.contested_taxa_diffs()

    def compare_lists(self, tag, l1, l2, list_to_str=None):
        compare_lists(self.out, tag, l1, l2, self.verbose, list_to_str)

    # list of collections, list of trees, compare SHAs
    # look at phylo_snapshot/concrete_rank_collection.json for each run
    def config_diffs(self):
        j1, j2 = self.run1.config, self.run2.config
        # do ott versions match
        print_header(self.out, 2, "OTT versions")
        ott1, ott2 = j1["ott_version"], j2["ott_version"]
        if ott1 != ott2:
            para = f"{R1N} ott ({ott1}) != {R2N} ott ({ott2})"
        else:
            para = f"Both runs used {ott1}"
        print_paragraph(self.out, para)

        # do roots match
        root1, root2 = int(j1["root_ott_id"]), int(j2["root_ott_id"])
        if root1 != root2:
            para = f"root id1 ({root1}) != root id2 ({root2})"
        else:
            para = f"Both runs used root id {root1}"
        print_paragraph(self.out, para)

        # do collections match
        collections1, collections2  = j1["collections"], j2["collections"]
        self.compare_lists("Collections included", collections1, collections2)

        # do flags match
        flags1, flags2 = j1["taxonomy_cleaning_flags"], j2["taxonomy_cleaning_flags"]
        self.compare_lists("Flags", flags1, flags2)

    def cmp_cleaned_trees(self, tid):
        fp = f"cleaned_phylo/tree_{tid}.json"
        path1, path2 = self.run1.filepath_to(fp), self.run2.filepath_to(fp)
        j1 = read_as_json(path1)
        j2 = read_as_json(path2)
        if j1 == j2:
            return None
        # keys = {'unmapped_otu', 
        #          'mapped_to_taxon_containing_other_mapped_tips', 
        #          'replaced_by_exemplar_node', 
        #          'replaced_by_arbitrary_node', 
        #          'empty-after-higher-taxon-tip-prune', 
        #          'unrecognized_ott_id', 
        #          'outgroup', 
        #          'flagged', 
        #          'higher-taxon-tip', 
        #          'revised_ingroup_node', 
        #          'became_trivial'}
        node_diffs = {}
        edge_diffs = {}
        nds_done = set()
        edges_done = set()
        print(path2)
        for k, v in j2.items():
            corresp = j1.get(k, {})
            if k == "revised_ingroup_node":
                v = {'nodes':[v]}
                if corresp == {}:
                    cnodes, cedges = [], []
                else:
                    cnodes, cedges = {'nodes':[corresp]}, []
            else:
                cnodes, cedges = corresp.get("nodes", []), corresp.get("edges", [])
            nodes, edges = v.get("nodes", []), v.get("edges", [])
            
            for nd in nodes:
                nds_done.add(nd)
                if nd in cnodes:
                    continue
                prev_tag = _find_node_in_cleaned_phylo_json(j1, nd)
                new_key = f"{prev_tag} -> {k}"
                node_diffs.setdefault(new_key, []).append(nd)
            for edge in edges:
                if edge in cedges:
                    continue
                prev_tag = _find_edge_in_cleaned_phylo_json(j1, edge)
                new_key = f"{prev_tag} -> {k}"
                edge_diffs.setdefault(new_key, []).append(edge)
        for k, v in j1.items():
            if k == "revised_ingroup_node":
                v = {'nodes':[v]}
            nodes, edges = v.get("nodes", []), v.get("edges", [])
            for nd in nodes:
                if nd in nds_done:
                    continue
                new_key = f"{k} -> INCLUDED"
                node_diffs.setdefault(new_key, []).append(nd)
            for edge in edges:
                if nd in edges_done:
                    continue
                new_key = f"{k} -> INCLUDED"
                edge_diffs.setdefault(new_key, []).append(edge)
        tks = set()
        tks.update(node_diffs.keys())
        tks.update(edge_diffs.keys())
        tkl = list(tks)
        tkl.sort()
        sn = []
        for k in tkl:
            nd_strs = node_diffs.get(k, [])
            nd_strs.sort()
            edge_strs = edge_diffs.get(k, [])
            edge_strs.sort()
            row = f"{k}: nodes = {nd_strs} edges = {edge_strs}"
            sn.append(row)
        return sn

    def do_phylo_comparison(self, study_tree):
        if self.html_dir is None:
            return self._do_phylo_comparison(study_tree, self.out)
        fp = os.path.join(self.html_dir, f"tree_{study_tree}.html")
        with open(fp, "w") as curr_out:
            return self._do_phylo_comparison(study_tree, curr_out)
    
    def _describe_nexson_diff(self, curr_out, study_tree, nex1, nex2):
        sys.stderr.write(f"comparing nexson for {study_tree}\n")
        study_id, tree_id = study_tree.split('@')
        tree_1, otu_1 = get_tree_and_otus_from_nexson(nex1, tree_id)
        assert tree_1 is not None
        tree_2, otu_2 = get_tree_and_otus_from_nexson(nex2, tree_id)
        assert tree_2 is not None
        try:
            otus_done = set()
            unmapped = []
            remapped = []
            mapped = []
            for k, v in otu_2.items():
                # print(f"otu key {k} => {v}")
                otus_done.add(k)
                other = otu_1.get(k)
                if other is None:
                    raise RuntimeError(f"new otu_id {k} in {study_tree}")
                ott_id_2 = v.get("^ot:ottId")
                ott_id_1 = other.get("^ot:ottId")
                if ott_id_1 is not None:
                    assert isinstance(ott_id_1, int)
                if ott_id_2 is not None:
                    assert isinstance(ott_id_2, int)
                    if ott_id_1 is None:
                        mapped.append((k, ott_id_2, v.get("^ot:ottTaxonName", "")))
                    elif ott_id_1 != ott_id_2:
                        remapped.append((k, ott_id_1, other.get("^ot:ottTaxonName", ""), 
                                            ott_id_2, v.get("^ot:ottTaxonName", "")))
                else:
                    if ott_id_1 is None:
                        pass # still unmapped
                    else:
                        unmapped.append((k, ott_id_1, other.get("^ot:ottTaxonName", "")))
            for k, v in otu_1.items():
                if k not in otus_done:
                    raise RuntimeError(f"deletion of otu_id {k} in {study_tree}")
            if mapped or unmapped or remapped:
                print_paragraph(curr_out, f"{len(unmapped)} taxa unmapped")
                if unmapped:
                    open_list(curr_out)
                    for u in unmapped:
                        print_list_item(curr_out, f"{u[0]} no longer mapped to OTT '{u[2]}' ({u[1]})")
                    close_list(curr_out)
                print_paragraph(curr_out, f"{len(mapped)} newly taxa mapped")
                if mapped:
                    open_list(curr_out)
                    for u in mapped:
                        print_list_item(curr_out, f"{u[0]} now mapped to OTT '{u[2]}' ({u[1]})")
                    close_list(curr_out)
                    
                print_paragraph(curr_out, f"{len(remapped)} remapped taxa")
                if remapped:
                    open_list(curr_out)
                    for u in remapped:
                        print_list_item(curr_out, f"{u[0]} changed from OTT '{u[2]}' ({u[1]}) to '{u[4]}'' ({u[3]}) ")
                    close_list(curr_out)
            else:
                print_paragraph(curr_out, "No OTU mapping changes")
        except:
            sys.stderr.write(f"Writing (possibly modified) otus for {study_tree} to cruft1.json and cruft2.json")
            with open("cruft1.json", "w") as o:
                o.write(json.dumps(otu_1, sort_keys=True, indent=2))
                o.write('\n')
            with open("cruft2.json", "w") as o:
                o.write(json.dumps(otu_2, sort_keys=True, indent=2))
                o.write('\n')
            raise

        if tree_1 == tree_2:
            print_paragraph(curr_out, "No tree changes")
        else:
            try:
                o1, o2 = tree_1.get("^ot:inGroupClade"), tree_2.get("^ot:inGroupClade")
                if o1 != o2:
                    print_paragraph(curr_out, f"ingroup node changed from {o1} to {o2}")
                o1, o2 = tree_1.get("^ot:rootNodeId"), tree_2.get("^ot:rootNodeId")
                if o1 != o2:
                    print_paragraph(curr_out, f"root node changed from {o1} to {o2}")
                o1, o2 = tree_1.get("^ot:specifiedRoot"), tree_2.get("^ot:specifiedRoot")
                if o1 != o2:
                    print_paragraph(curr_out, f"specifiedRoot node changed from {o1} to {o2}")
                nbi_1, nbi_2 = tree_1.get("nodeById"), tree_2.get("nodeById")
                exemplar_del = []
                nonexemplar_del = []
                exemplar_add = []
                nonexemplar_add = []
                exemplar_mod = []
                nonexemplar_mod = []
            
                if nbi_1 != nbi_2:
                    for nd_id, nd_blob in nbi_2.items():
                        prev_blob = nbi_1[nd_id]
                        if prev_blob != nd_blob:
                            k = '^ot:isTaxonExemplar'
                            e_1, e_2 = prev_blob.get(k), nd_blob.get(k)
                            if e_1 != e_2:
                                if e_2 is None:
                                    if e_1:
                                        exemplar_del.append(nd_id)
                                    else:
                                        nonexemplar_del.append(nd_id)
                                    del prev_blob[k]
                                else:
                                    if e_1 is None:
                                        if e_2:
                                            exemplar_add.append(nd_id)
                                        else:
                                            nonexemplar_add.append(nd_id)
                                    else:
                                        if e_2:
                                            exemplar_mod.append(nd_id)
                                        else:
                                            nonexemplar_mod.append(nd_id)
                                    prev_blob[k] = e_2
                                assert prev_blob == nd_blob
                print_paragraph(curr_out, f"{len(exemplar_del)} exemplar nodes unflagged")
                _list_elements(curr_out, exemplar_del)
                print_paragraph(curr_out, f"{len(nonexemplar_del)} nonexemplar nodes unflagged")
                _list_elements(curr_out, nonexemplar_del)
                print_paragraph(curr_out, f"{len(exemplar_add)} nodes flagged as exemplar")
                _list_elements(curr_out, exemplar_add)
                print_paragraph(curr_out, f"{len(nonexemplar_add)} nodes flagged as nonexemplar")
                _list_elements(curr_out, nonexemplar_add)
                print_paragraph(curr_out, f"{len(exemplar_mod)} nodes flags changed to exemplar")
                _list_elements(curr_out, exemplar_mod)
                print_paragraph(curr_out, f"{len(nonexemplar_mod)} nodes flags changed to nonexemplar")
                _list_elements(curr_out, nonexemplar_mod)
                assert tree_1.get("edgeBySourceId") == tree_2.get("edgeBySourceId")
            except:
                sys.stderr.write(f"Writing (possibly modified) trees for {study_tree} to cruft1.json and cruft2.json")
                sys.stderr.write(f"NOTE: the _describe_nexson_diff function of this script currently does not deal with rerooting annotations in nodes, so... yeah... that's a thing.")
                with open("cruft1.json", "w") as o:
                    o.write(json.dumps(tree_1, sort_keys=True, indent=2))
                    o.write('\n')
                with open("cruft2.json", "w") as o:
                    o.write(json.dumps(tree_2, sort_keys=True, indent=2))
                    o.write('\n')
                raise
    
    def _do_nexson_comparison(self, study_tree, curr_out):
        run1, run2 = self.run1, self.run2
        rel_path = _SNAPSHOT_JSON_TEMPLATE.format(study_tree=study_tree)
        snap_fp1 = run1.filepath_to(rel_path)
        snap_fp2 = run2.filepath_to(rel_path)
        nex1 = read_as_json(snap_fp1)
        nex2 = read_as_json(snap_fp2)
        
        print_header(curr_out, 1, f"Input {study_tree}")
        print_paragraph(curr_out, "curation link: " + display_tree_name(study_tree))
        changed = False
        print_header(curr_out, 2, "Curated NexSON")
        if nex2 == nex1:
            print_paragraph(curr_out, "No change")
        else:
            changed = True
            self._describe_nexson_diff(curr_out, study_tree, nex1, nex2)
        return changed

    def _do_cleaned_phylo_comparison(self, study_tree, curr_out):
        run1, run2 = self.run1, self.run2
        rel_path = _CLEANED_PHYLO_TREE_TEMPLATE.format(study_tree=study_tree)
        print_header(curr_out, 2, "Cleaned phylogeny")
        tree_fp1 = run1.filepath_to(rel_path, required=False)
        tree_fp2 = run2.filepath_to(rel_path, required=False)
        if not os.path.exists(tree_fp1):
            if os.path.exists(tree_fp2):
                print_paragraph(curr_out, "Cleaned tree is now empty")
                return True
            print_paragraph(curr_out, "Cleaned tree remained empty")
            return False
        if not os.path.exists(tree_fp2):
            print_paragraph(curr_out, "Cleaned tree was previously empty")
            return True
        
        tree1 = Tree.get_from_path(tree_fp1, schema="newick")
        tree1.is_rooted = True
        tree2 = Tree.get_from_path(tree_fp2, schema="newick", taxon_namespace=tree1.taxon_namespace)
        tree2.is_rooted = True
        sd = treecompare.symmetric_difference(tree1, tree2)
        if sd > 0:
            print_paragraph(curr_out, f"Cleaned trees differ symmetric_difference = {sd} (may not be reliable if leafsets differ)")
            return True
        print_paragraph(curr_out, "Cleaned tree are the same")
        return False

    def _do_exemplified_phylo_comparison(self, study_tree, curr_out):
        run1, run2 = self.run1, self.run2
        rel_path = _EXEMPLAR_PHYLO_TREE_TEMPLATE.format(study_tree=study_tree)
        print_header(curr_out, 2, "Exemplified phylogeny")
        tree_fp1 = run1.filepath_to(rel_path, required=False)
        tree_fp2 = run2.filepath_to(rel_path, required=False)
        if not os.path.exists(tree_fp1):
            if os.path.exists(tree_fp2):
                print_paragraph(curr_out, "Exemplified tree is now empty")
                return True
            print_paragraph(curr_out, "Exemplified tree remained empty")
            return False
        if not os.path.exists(tree_fp2):
            print_paragraph(curr_out, "Exemplified tree was previously empty")
            return True
        
        tree1 = Tree.get_from_path(tree_fp1, schema="newick")
        tree1.is_rooted = True
        tree2 = Tree.get_from_path(tree_fp2, schema="newick", taxon_namespace=tree1.taxon_namespace)
        tree2.is_rooted = True
        sd = treecompare.symmetric_difference(tree1, tree2)
        if sd > 0:
            print_paragraph(curr_out, f"Exemplified trees differ symmetric_difference = {sd} (may not be reliable if leafsets differ)")
            return True
        print_paragraph(curr_out, "Exemplified tree are the same")
        return False
        
    def _do_phylo_comparison(self, study_tree, curr_out):
        changed = self._do_nexson_comparison(study_tree, curr_out)
        changed = self._do_cleaned_phylo_comparison(study_tree, curr_out) or changed
        changed = self._do_exemplified_phylo_comparison(study_tree, curr_out) or changed
        print_link(curr_out, "./index.html", "back to main index")
        return changed

        # 
        #     prev_index = it1.index(tid)
        #     if tid in set_net2:
        #         if tid in set_net1:
        #             clean_diff = self.cmp_cleaned_trees(tid)
        #             if clean_diff:
        #                 x = '\n  '.join(clean_diff)
        #                 print(f"{tid} : \n  {x}")
        #         else:
        #             print(f"{tid} no longer empty")
        #     elif tid in set_net1:
        #         print(f"{tid} newly empty")
        #     else:
        #         print(f"{tid} still empty")   
        # elif tid in set_net2:
        #     print(f"{tid} new non-empty tree")
        # else:
        #     print(f"{tid} new tree, but empty")

    def phylo_input_diffs(self):
        run1, run2 = self.run1, self.run2
        td1, td2 = run1.input_trees, run2.input_trees
        ttds = treelist_to_display_str
        it1, it2 = td1["input_trees"], td2["input_trees"]
        set_it1, set_it2 = set(it1), set(it2)
        net1 = [i[:-4] if i.endswith('.tre') else i for i in td1["non_empty_trees"]]
        net2 = [i[:-4] if i.endswith('.tre') else i for i in td2["non_empty_trees"]]
        set_net1, set_net2 = set(net1), set(net2)
        out = self.out
        compare_lists(out, "Input trees", it1, it2, False)
        compare_lists(out, "Non-empty trees", net1, net2, False)
        idx_offset = 0
        open_list(out)
        for curr_index, study_tree in enumerate(it2):
            if study_tree in set_it1:
                if self.do_phylo_comparison(study_tree):
                    u = f"tree_{study_tree}.html"
                    print_list_item(out, fmt_link(u, f"{study_tree} changed"))
                else:
                    print_list_item(out, f"{study_tree} unchanged")
        for study_tree in it1:
            if study_tree not in set_it2:
                if study_tree in set_net1:
                    print_list_item(out, f"{study_tree} non-empty tree deleted")
                else:
                    print_list_item(out, f"{study_tree} empty tree deleted")
        close_list(out)

    def contested_taxa_diffs(self):
        run1, run2 = self.run1, self.run2
        ott_to_depth = self._read_ott_to_depth()

    def _read_ott_to_depth(self):
        if not self.ott_to_depth_fp:
            return None
        with open(self.ott_to_depth_fp, 'r') as inp:
            o2d = {}
            for line in inp:
                ls = [int(i) for i in line.strip().split()]
                o2d[ls[0]] = ls[1]

def do_compare(
    out, run1, run2, verbose=False, print_broken_taxa=False, print_summary_table=False, 
    ott_to_depth_fp=None, html_dir=None
):
    rc = RunComparison(run1, run2, outstream=out, verbose=verbose, html_dir=html_dir)
    rc.ott_to_depth_fp = ott_to_depth_fp
    rc.input_diffs()

    

def main():
    # get command line arguments (the two directories to compare)
    parser = argparse.ArgumentParser(description="compare synthesis outputs")
    parser.add_argument("run1", help="path to the first (older) output directory")
    parser.add_argument("run2", help="path to the second (newer) output directory")
    parser.add_argument("--html", action="store_true", help="print output as html")
    parser.add_argument(
        "--html-dir", help="specify a directory for multi-file html output"
    )
    parser.add_argument("--ott-to-depth-fp",
                        dest="ott_to_depth_fp",
                        default=None,
                        required=False,
                        help="path output of a run from: otc-taxonomy-parser --report-dist-to-root ")
    parser.add_argument(
        "-b",
        dest="print_broken_taxa",
        action="store_true",
        help="print info on newly-broken taxa; default false",
    )
    parser.add_argument(
        "-t",
        dest="print_summary_table",
        action="store_true",
        help="print summary table for release notes; default false",
    )
    parser.add_argument(
        "-v",
        dest="verbose",
        action="store_true",
        help="print details on diffs; default false",
    )
    args = parser.parse_args()
    if args.html:
        to_html_out()
    html_dir = args.html_dir
    if html_dir:
        to_html_out(html_dir)
        out = open(os.path.join(html_dir, "index.html"), "w", encoding="utf-8")
    else:
        out = sys.stdout
    status("run 1 output: {d}".format(d=args.run1))
    status("run 2 output: {d}".format(d=args.run2))

    r1_fn = os.path.split(args.run1)[-1]
    r2_fn = os.path.split(args.run2)[-1]
    if r1_fn == r2_fn:
        r1_fn = args.run1
        r2_fn = args.run2
    set_run_names(r1_fn, r2_fn)

    # get stats object for each run
    run1 = RunStatistics(args.run1)
    run2 = RunStatistics(args.run2)

    try:
        do_compare(
            out,
            run1,
            run2,
            verbose=args.verbose,
            print_broken_taxa=args.print_broken_taxa,
            print_summary_table=args.print_summary_table,
            html_dir=html_dir,
            ott_to_depth_fp=args.ott_to_depth_fp
        )
    finally:
        if html_dir:
            out.close()


if __name__ == "__main__":
    main()
