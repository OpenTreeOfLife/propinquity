#!/usr/bin/env python
import json
import sys
import os
import re
import subprocess

def debug(msg):
    sys.stderr.write(f"{msg}\n")

def analyze_bad_id_set(ott_fp, curr_name, curr_used, curr_unused):
    debug(f"curr_name={curr_name} len(curr_used)={len(curr_used)} len(curr_unused)={len(curr_unused)}")
    if len(curr_used) == 0:
        debug(f"grepping for {curr_name} in {ott_fp} ...")
        resp = subprocess.run(["grep", "-P", f"\\t{curr_name}\\t", ott_fp], capture_output=True, encoding="utf-8")
        if resp.returncode == 0:
            lines = [i for i in resp.stdout.split("\n")]
            nonempty = [i for i in lines if i]
            if len(nonempty) == 1:
                matched = lines[0]
                ls = matched.split("\t")
                debug(f"ls={ls}")
                ott_id = int(ls[0])
                if ott_id not in curr_unused:
                    sys.exit(f'"{curr_name}" assigned ID {ott_id} which was not expected')
                else:
                    debug(f"No change needed for {curr_name} staying {ott_id}")
            else:
                raise NotImplementedError(f"Dealing with names repeated. lines={nonempty}")
        else:
            debug(f" ... not found.")
    elif len(curr_used) == 1:
        pass
    else:
        raise NotImplementedError("dealing with names that have multiple IDs that are used in studies is not yet supported")

def parse_bad_amend_out_file(prob_fp, ott_fp):
    next_name_pat = re.compile(r'^name = (.*)$')
    unused_pat = re.compile(r"^  ott_id=([0-9]+): UNUSED$")
    used_pat = re.compile(r"^  ott_id=([0-9]+): \[(.+)\]$")
    curr_unused = set()
    curr_used = {}
    curr_name = None
    with open(prob_fp, "r") as inp:
        for line in inp:
            m = next_name_pat.match(line)
            if m:
                if curr_name is not None:
                    analyze_bad_id_set(ott_fp, curr_name, curr_used, curr_unused)
                curr_name = m.group(1).strip()
                curr_unused = set()
                curr_used = {}
                continue
            m = unused_pat.match(line)
            if m:
                uoi = int(m.group(1))
                curr_unused.add(uoi)
                continue
            m = used_pat.match(line)
            if m:
                uoi = int(m.group(1))
                studies = m.group(2).split(",")
                unquoted = []
                for s in studies:
                    ss = s.strip()
                    assert(len(ss) > 2)
                    assert(ss.endswith("'"))
                    assert(ss.startswith("'"))
                    unquoted.append(ss[1:-1])
                assert(uoi not in curr_used)
                curr_used[uoi] = unquoted
                continue
            sys.exit(f"Unmatched line:\n{line}")
    if curr_name is not None:
        analyze_bad_id_set(ott_fp, curr_name, curr_used, curr_unused)


def debug(msg):
    sys.stderr.write(f"{msg}\n")

def main():
    bad_amend_out_fp = "cruft/studies_with_bad_amend_id_taxa.txt"
    if not os.path.isfile(bad_amend_out_fp):
        sys.exit(f"Error need to generalize this script or run:\n./bin/find_studies_with_bad_amend_id_taxa.py > cruft/studies_with_bad_amend_id_taxa.txt\nbefore executing this.\n")
    taxonomy_filepath = "../ott/ott3.7.3/taxonomy.tsv"
    if not os.path.isfile(taxonomy_filepath):
        sys.exit(f"Error need to generalize this script or move the taxonomy file to ../ott/ott3.7.3/taxonomy.tsv.\n")
    parse_bad_amend_out_file(bad_amend_out_fp, taxonomy_filepath)


if __name__ == "__main__":
    main()
