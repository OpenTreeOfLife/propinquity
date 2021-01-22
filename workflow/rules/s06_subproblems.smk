from propinquity import (run_unhide_if_worked, 
                         solve_subproblem,
                         suppress_non_listed_ids_or_unnamed,
                         stripped_nonempty_lines,
                         validate_config,
                         write_if_needed)
from snakemake.logging import logger
import os

CFG = validate_config(config, logger)

rule all:
    input: "subproblem_solutions/solution-ids.txt"
    log: "logs/subproblems"

rule expand_path_to_nonempty_phylo:
    input: config = "config", \
           phylo_list_fp = "exemplified_phylo/nonempty_trees.txt"
    output: "subproblems/scratch/args.txt"
    run:
        ph_li_fp = input.phylo_list_fp
        fn = [i.strip() for i in open(ph_li_fp, "r") if i.strip()]
        ap = os.path.abspath(os.path.split(ph_li_fp)[0])
        fp = [os.path.join(ap, i) for i in fn]
        fp.append('') # for the newline at the end of the file
        fpc = '\n'.join(fp)
        write_if_needed(fp=output[0],
                        content=fpc,
                        name="nonempty tree fullpaths",
                        CFG=CFG)

include: "common.smk"

rule create_subproblem_scaffold:
    input: config = "config", \
           tax = "exemplified_phylo/taxonomy.tre", \
           sub = "subproblems/dumped_subproblem_ids.txt"
    output: scaff = "subproblem_solutions/subproblems-scaffold.tre", \
            tmp = temp("subproblem_solutions/poly_prob.tre"),
            sans_suff = "subproblem_solutions/ids_without_dot_tre.txt"
    run:
        prob_ids = []
        with open(input.sub, "r") as inp:
            for line in inp:
                ls = line.strip()
                if ls:
                    if not ls.endswith('.tre'):
                        m = "Expecting every line in {} to end in .tre, but found {}"
                        raise RuntimeError(m.format(input.sub, ls))
                    prob_ids.append(ls[:-4])
        with open(output.tmp, "w", encoding='utf-8') as o:
            o.write('({});\n'.format(', '.join(prob_ids)))
        content = '{}\n'.format('\n'.join(prob_ids))
        write_if_needed(fp=output.sans_suff, content=content, CFG=CFG)
        inv = ['otc-induced-subtree', input.tax, output.tmp]
        run_unhide_if_worked(inv, CFG=CFG, stdout_capture=output.scaff)

rule simplify_scaffold:
    input: config = "config", \
           tree = "subproblem_solutions/subproblems-scaffold.tre", \
           id_list = "subproblem_solutions/ids_without_dot_tre.txt"
    output: scaff = "subproblem_solutions/subproblems-scaffold-only.tre"
    run:
        suppress_non_listed_ids_or_unnamed(in_tree_fp=input.tree,
                                           id_fp=input.id_list,
                                           out_tree_fp=output.scaff,
                                           CFG=CFG)

rule solve:
    input: config = "config", \
           otcconfig = "otc-config", \
           subprob_id = "subproblems/dumped_subproblem_ids.txt", \
           incert = "exemplified_phylo/incertae_sedis.txt", \
           subprob = "subproblems/{ottid}.tre"
    output: soln = "subproblem_solutions/{ottid}.tre"
    run:
        solve_subproblem(incert_sed_fp=input.incert,
                         subprob_fp=input.subprob,
                         out_fp=output.soln,
                         CFG=CFG)


rule solve_rev:
    input: config = "config", \
           otcconfig = "otc-config", \
           subprob_id = "subproblems/dumped_subproblem_ids.txt", \
           incert = "exemplified_phylo/incertae_sedis.txt", \
           subprob = "reversed_subproblems/{ottid}.tre"
    output: soln = "reversed_subproblem_solutions/{ottid}.tre"
    run:
        solve_subproblem(incert_sed_fp=input.incert,
                         subprob_fp=input.subprob,
                         out_fp=output.soln,
                         CFG=CFG)