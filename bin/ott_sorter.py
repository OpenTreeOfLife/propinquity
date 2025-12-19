#!/usr/bin/env python
import json
import sys
import os
import re
import subprocess

def debug(msg):
    sys.stderr.write(f"{msg}\n")

def deal_with_queued_lines(out, ids_written, lines_queued):
    nlq = []
    for ott_id, par_id, line in lines_queued:
        if par_id in ids_written:
            out.write(line)
            ids_written.add(ott_id)
        else:
            nlq.append((ott_id, par_id, line))
    if len(nlq) == len(lines_queued):
        sys.exit(f"ERROR. No decrease in lines!\n{lines_queued}\n")
    if len(nlq) > 0:
        deal_with_queued_lines(out,ids_written, nlq)

def main():
    ott_tax_fp = sys.argv[1]
    out = sys.stdout
    ids_written = set()
    lines_queued = []
    with open(ott_tax_fp, "r", encoding="utf-8") as inf_fp:
        for idx, line in enumerate(inf_fp):
            if idx == 0:
                out.write(line)
                continue
            ls = line.split("\t|\t")
            ott_id, par_id = ls[0], ls[1]
            if (not par_id) or (par_id in ids_written):
                out.write(line)
                ids_written.add(ott_id)
            else:
                lines_queued.append((ott_id, par_id, line))

    if lines_queued:
        deal_with_queued_lines(out, ids_written, lines_queued)





if __name__ == "__main__":
    main()
