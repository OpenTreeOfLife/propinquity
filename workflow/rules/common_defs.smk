from propinquity import (clean_contesting_tree_refs,
                         decompose_into_subproblems,
                         validate_config,
                         write_if_needed)
from snakemake.logging import logger
import os

def _agg_trees_impl(wildcards, soln_dir):
    solve_out = os.path.split(checkpoints.decompose.get(**wildcards).output[0])[0]
    gw = glob_wildcards(os.path.join(solve_out, '{ottid}.tre'))
    template = soln_dir + "/{ottid}.tre"
    return expand(template, ottid=gw.ottid)

def aggregate_trees(wildcards):
    return _agg_trees_impl(wildcards, "subproblem_solutions")

def aggregate_rev_trees(wildcards):
    return _agg_trees_impl(wildcards, "reversed_subproblem_solutions")

def aggregate_sdd_common(wildcards, solved_dir, dd_dir=None):
    if dd_dir is None:
        dd_dir = solved_dir
    gw = glob_wildcards(os.path.join(solved_dir, '{ottid,ott[0-9]+}.tre'))
    return expand(dd_dir + "/deg-dist-{ottid}.txt", ottid=gw.ottid)

def aggregate_sdd(wildcards):
    return aggregate_sdd_common(wildcards, directory("subproblem_solutions"))

def aggregate_rsdd(wildcards):
    solve_out = os.path.split(checkpoints.reverse_subproblems_flag.get(**wildcards).output[0])[0]
    return aggregate_sdd_common(wildcards, directory("reversed_subproblem_solutions"))

def aggregate_probdd(wildcards):
    return aggregate_sdd_common(wildcards, directory("subproblems"), "subproblems/deg-dist")
