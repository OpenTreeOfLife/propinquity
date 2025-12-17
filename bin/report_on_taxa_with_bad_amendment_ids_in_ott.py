#!/usr/bin/env python
import json
import sys
import os
import re
import subprocess

def debug(msg):
    sys.stderr.write(f"{msg}\n")


def get_lines_for_name(ott_fp, curr_name):
    # debug(f"grepping for {curr_name} in {ott_fp} ...")
    resp = subprocess.run(["grep", "-P", f"\\t{curr_name}\\t", ott_fp], capture_output=True, encoding="utf-8")
    if resp.returncode == 0:
            lines = [i for i in resp.stdout.split("\n")]
            nonempty = [i for i in lines if i]
            return [i.split("\t|\t") for i in nonempty]
    else:
        debug(f" ... {curr_name} not found.")
    return []

def get_most_used(curr_used):
    num_uses = -1
    muid = None
    for oid, studies in curr_used.items():
        if len(studies) > num_uses:
            muid = oid
            num_uses = len(studies)
    return muid

def get_other_studies(curr_used, taboo_id):
    other_studies = []
    for oid, studies in curr_used.items():
        if oid != taboo_id:
            other_studies.extend(studies)
    return other_studies

TO_DEL = []
TO_ADD = []
FORWARDS = {}
def record_del_add(to_del, to_add):
    TO_DEL.append(f"sed -E '/^{to_del[0]}\\t/d'")
    TO_ADD.append("\t|\t".join(to_add))

def store_forwards(ott_id, curr_used, curr_unused):
    for oid in curr_unused:
        if oid != ott_id:
            assert(oid not in FORWARDS)
            FORWARDS[oid] = ott_id
    for oid in curr_used.keys():
        if oid != ott_id:
            assert(oid not in FORWARDS)
            FORWARDS[oid] = ott_id



AVOID_NAME_CHECK = False

def analyze_bad_id_set(ott_fp, curr_name, curr_used, curr_unused, all_ott_ids):
    ott_ids_found_in_all_ids = set()
    for oid in curr_unused:
        if oid in all_ott_ids:
            ott_ids_found_in_all_ids.add(oid)
    for oid in curr_used.keys():
        if oid in all_ott_ids:
            ott_ids_found_in_all_ids.add(oid)
    if len(ott_ids_found_in_all_ids) == 0:
        debug(f"No ID found for \"{curr_name}\" in all_ott_ids")
    elif len(ott_ids_found_in_all_ids) == 1:
        debug(f"Only 1 ID {list(ott_ids_found_in_all_ids)[0]} found for \"{curr_name}\" in all_ott_ids")
    else:
        debug(f"Multiple IDs ({list(ott_ids_found_in_all_ids)}) found for \"{curr_name}\" in all_ott_ids")
    
    if AVOID_NAME_CHECK:
        return
    debug(f"curr_name={curr_name} len(curr_used)={len(curr_used)} len(curr_unused)={len(curr_unused)}")
    split_lines = get_lines_for_name(ott_fp, curr_name)
    if not split_lines:
        print(f'Need to add "{curr_name}" to taxonomy')
    elif len(split_lines) == 1:
        only_line =  split_lines[0]
        ott_id = int(only_line[0])
        if len(curr_used) == 0:
            if ott_id not in curr_unused:
                sys.exit(f'"{curr_name}" assigned ID {ott_id} which was not expected')
            else:
                print(f"No change needed for {curr_name} staying {ott_id}")
                store_forwards(ott_id, curr_used, curr_unused)
        elif len(curr_used) == 1:
            ott_id_used_in_studies = list(curr_used.keys())[0]
            if ott_id == ott_id_used_in_studies:
                print(f"No change needed for {curr_name} staying {ott_id}")
                store_forwards(ott_id, curr_used, curr_unused)
            elif ott_id not in curr_unused:
                sys.exit(f'"{curr_name}" assigned ID {ott_id} which was not expected')
            else:
                mod_line = list(only_line)
                mod_line[0] = f"{ott_id_used_in_studies}"
                record_del_add(only_line, mod_line)
                print(f"Need to change OTT ID for {curr_name} from {ott_id} to {ott_id_used_in_studies} to avoid remapping studies")
                store_forwards(ott_id_used_in_studies, curr_used, curr_unused)
        else:
            most_commonly_used_id = get_most_used(curr_used)
            all_other_studies = get_other_studies(curr_used, most_commonly_used_id)
            os_str = ", ".join(all_other_studies)
            if ott_id == most_commonly_used_id:
                print(f"No change needed for {curr_name} staying {ott_id}, but need to update mapping in {os_str}")
                store_forwards(ott_id, curr_used, curr_unused)
            else:
                mod_line = list(only_line)
                mod_line[0] = f"{most_commonly_used_id}"
                record_del_add(only_line, mod_line)
                print(f"Need to change OTT ID for {curr_name} from {ott_id} to {most_commonly_used_id} and then remap studies {os_str}")
                store_forwards(most_commonly_used_id, curr_used, curr_unused)
            
    else:
        raise NotImplementedError(f"Dealing with names repeated. lines={nonempty}")

def parse_bad_amend_out_file(prob_fp, ott_fp, all_ott_ids):
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
                    analyze_bad_id_set(ott_fp, curr_name, curr_used, curr_unused, all_ott_ids)
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
        analyze_bad_id_set(ott_fp, curr_name, curr_used, curr_unused, all_ott_ids)


def debug(msg):
    sys.stderr.write(f"{msg}\n")

def main():
    bad_amend_out_fp = "cruft/studies_with_bad_amend_id_taxa.txt"
    if not os.path.isfile(bad_amend_out_fp):
        sys.exit(f"Error need to generalize this script or run:\n./bin/find_studies_with_bad_amend_id_taxa.py > cruft/studies_with_bad_amend_id_taxa.txt\nbefore executing this.\n")
    taxonomy_filepath = "../ott/ott3.7.3/taxonomy.tsv"
    if not os.path.isfile(taxonomy_filepath):
        sys.exit(f"Error need to generalize this script or move the taxonomy file to ../ott/ott3.7.3/taxonomy.tsv.\n")
    
    ott_ids_file = "cruft/all_ott3.7.3_ids.txt"
    if not os.path.isfile(ott_ids_file):
        sys.exit("Error need to generalize this script or run:\ncat ../ott/ott3.7.3/taxonomy.tsv | awk '{print $1}' > cruft/all_ott3.7.3_ids.txt.\n")
    
    all_ott_ids = set()
    with open(ott_ids_file, "r") as inp:
        for line in inp:
            ls = line.strip()
            if not ls:
                continue
            all_ott_ids.add(int(ls))

    parse_bad_amend_out_file(bad_amend_out_fp, taxonomy_filepath, all_ott_ids)

    out_scriptfn = "cruft/ott_mod_script.sh"
    out_tax = "cruft/ott-taxonomy-modified.tsv"
    out_fwd = "cruft/ott-forwards-suffix.tsv"
    if TO_DEL:
        del_lines = "\\\n  | ".join(TO_DEL)
        del_lines = f" | {del_lines}"
    else:
        del_lines = ""

    if TO_ADD:
        add_lines = "\n".join([f'echo -e {repr(i)} >> "{out_tax}"' for i in TO_ADD])
    else:
        add_lines = ""

    fwd_lines = ""
    if FORWARDS:
        flines = []
        for old, new in FORWARDS.items():
            flines.append(f'echo -e "{old}\t{new}" >> "{out_fwd}"')
        fwd_lines = "\n".join(flines)

    with open(out_scriptfn, "w") as out_script:
        out_script.write(f"""#/bin/bash

cat "{taxonomy_filepath}" {del_lines} > "{out_tax}"

{add_lines}

{fwd_lines}
""")
    debug(f"Script {out_scriptfn} written")



if __name__ == "__main__":
    main()
