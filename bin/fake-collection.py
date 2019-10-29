#!/usr/bin/env python
import json
import sys
import os
import re

def get_decisions():
    decisions = []
    sha = 0
    for x in sys.stdin:
        name = os.path.basename(x)
        study_tree = re.compile(r'([^_]+_[0-9]+)@([^@]+)\.tre')
        m = study_tree.match(name)
        if m is None:
            sys.stderr.write("\n\nError: Name '{}' does not match require pattern! Not generating fake collection.\n".format(name))
            exit(1)
        study = m.group(1)
        tree = m.group(2)
        sha += 1
        decisions.append({"studyID": study,
                          "treeID": tree,
                          "SHA": str(sha),
                          "name": name,
                          "decision": "INCLUDED"
                          })
    return decisions


if __name__ == '__main__':
    document = {"contributors": [],
                "creator": {"login":"",
                            "name":""},
                "description": "generated from newicks",
                "name":"",
                "queries": [],
                "url": ""};
    document["decisions"] = get_decisions();
    print json.dumps(document, indent=4);

