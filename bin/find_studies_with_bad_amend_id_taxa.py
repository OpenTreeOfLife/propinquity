#!/usr/bin/env python
import json
import sys
import os
import re

def read_grep_of_studies(mapped_id_fp):
    lp = re.compile(r"^(.*[0-9]+)\.json: *([0-9]+) *$")
    # lp = re.compile(r"^ot.20.json: ([0-9]+) *$")
    id_2_studies = {}
    with open(mapped_id_fp, "r") as inp:
        for line in inp:
            m = lp.match(line)
            if m:
                study = m.group(1)
                ott_id = int(m.group(2))
                id_2_studies.setdefault(ott_id, set()).add(study)
                continue
            sys.exit(f"Unmatched line:\n{line}")
    return id_2_studies

def parse_amend_probfile(prob_fp):
    mpmr = re.compile(r'^"([^"]+)" was given \d+ ott_ids=\[([0-9, ]+)\]; *\d+ par_ids=\[([0-9, ]+)\]; *\d+ ranks=\[(.+)\]\.$')
    mpor = re.compile(r'^"([^"]+)" was given \d+ ott_ids=\[([0-9, ]+)\]; *\d+ par_ids=\[([0-9, ]+)\]; rank=(.+)\.$')
    opmr = re.compile(r'^"([^"]+)" was given \d+ ott_ids=\[([0-9, ]+)\]; par_id=([0-9]+); *\d+ ranks=\[(.+)\]\.$')
    opor = re.compile(r'^"([^"]+)" was given \d+ ott_ids=.*\[([0-9, ]+)\]; par_id=([0-9]+); rank=(.+)\.$')
    multi_ided_names = []
    with open(prob_fp, "r") as inp:
        for line in inp:
            m = mpmr.match(line)
            if m:
                sys.stderr.write(f"Skipping line with multiple parents: {line}")
                continue
            m = mpor.match(line)
            if m:
                sys.stderr.write(f"Skipping line with multiple parents: {line}")
                continue
            m = opmr.match(line)
            if m:
                sys.stderr.write(f"Skipping line with multiple ranks: {line}")
                continue
            m = opor.match(line)
            if m:
                name = m.group(1)
                ois = m.group(2)
                oisp = [i.strip() for i in ois.split(",")]
                ott_ids = [int(i) for i in oisp]
                multi_ided_names.append((name, ott_ids))
                continue
            sys.exit(f"Unmatched line:\n{line}")
    return multi_ided_names

def debug(msg):
    sys.stderr.write(f"{msg}\n")

def main():
    amend_dup_fp = "cruft/amend-name-dups.txt"
    if not os.path.isfile(amend_dup_fp):
        sys.exit(f"Error need to generalize this script or run:\n./bin/diagnose_amendment_problems.py ../phylesystem/shards/amendments-1/ > cruft/amend-name-dups.txt\nbefore executing this.\n")
    mapped_id_fp = "cruft/mapped-ot-ids.txt"
    if not os.path.isfile(mapped_id_fp):
        sys.exit(f"Error need to generalize this script or run:\n.bin/find-all-mapped-ids.sh\nbefore executing this.\n")
    multi_ided_names = parse_amend_probfile(amend_dup_fp)
    id_2_studies = read_grep_of_studies(mapped_id_fp)

    for name, ott_ids in multi_ided_names:
        print(f"name = {name}")
        for ott_id in ott_ids:
            studies = id_2_studies.get(ott_id)
            if studies is None:
                print(f"  ott_id={ott_id}: UNUSED")
            else:
                sl = list(studies)
                sl.sort()
                print(f"  ott_id={ott_id}: {sl}")

if __name__ == "__main__":
    main()
