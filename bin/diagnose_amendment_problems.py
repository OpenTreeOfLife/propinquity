#!/usr/bin/env python
import json
import sys
import os
import re

class Amend(object):
    def __init__(self, name, ott_id, par_id, rank):
        self.name = name
        self.ott_id = ott_id
        self.par_id = par_id
        self.rank = rank

    def __str__(self):
        return f"Amend(name={self.name}, ott_id={self.ott_id}, par_id={self.par_id}, rank={self.rank})"

by_name = {}
by_id = {}

def process_file(fp):
    with open(fp, "r") as inp:
        j = json.load(inp)
    for tax in j.get("taxa", []):
        amend = Amend(name=tax["name"],
                      ott_id=tax["ott_id"],
                      par_id=tax["parent"],
                      rank=tax.get("rank")
                      )
        by_name.setdefault(amend.name, []).append(amend)
        by_id.setdefault(amend.ott_id, []).append(amend)

def summarize_same_names(amend_list):
    out = sys.stdout
    assert(len(amend_list) > 1)
    name = amend_list[0].name
    ott_ids = []
    par_ids = []
    ranks = []
    for a in amend_list:
        assert(name == a.name)
        ott_ids.append(a.ott_id)
        par_ids.append(a.par_id)
        ranks.append(a.rank)
    soi = set(ott_ids)
    spi = set(par_ids)
    sr = set(ranks)
    assert(len(soi) == len(amend_list))
    if len(spi) > 1:
        if len(sr) > 1:
            out.write(f"\"{name}\" was given {len(soi)} ott_ids={ott_ids}; {len(spi)} par_ids={par_ids}; {len(sr)} ranks={ranks}.\n")
        else:
            out.write(f"\"{name}\" was given {len(soi)} ott_ids={ott_ids}; {len(spi)} par_ids={par_ids}; rank={ranks[0]}.\n")
    else:
        if len(sr) > 1:
            out.write(f"\"{name}\" was given {len(soi)} ott_ids={ott_ids}; par_id={par_ids[0]}; {len(sr)} ranks={ranks}.\n")
        else:
            out.write(f"\"{name}\" was given {len(soi)} ott_ids={ott_ids}; par_id={par_ids[0]}; rank={ranks[0]}.\n")

def diagnose_problems():
    for ott_id, amend_list in by_id.items():
        if len(amend_list) > 1:
            print(ott_id, [str(i) for i in amend_list])
            assert(False)
    for name, amend_list in by_name.items():
        if len(amend_list) > 1:
            summarize_same_names(amend_list)

def debug(msg):
    sys.stderr.write(f"{msg}\n")
def main():
    amend_dir = sys.argv[1]
    amend_container = os.path.join(amend_dir, "amendments")
    num_fn_list = []
    afile_pat = re.compile(re.compile(r"^additions-(\d+)-\d+\.json"))
    for fn in os.listdir(amend_container):
        m = afile_pat.match(fn)
        if m:
            num_fn_list.append((int(m.group(1)), fn))
        else:
            debug(f"{fn} does not match pattern.")
    num_fn_list.sort()
    for tup in num_fn_list:
        fn = tup[-1]
        fp = os.path.join(amend_container, fn)
        process_file(fp)
    debug(f"{len(by_id)} ids found.")
    debug(f"{len(by_name)} names found.")
    diagnose_problems()

if __name__ == "__main__":
    main()