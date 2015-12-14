#!/usr/bin/env python
import json
import sys
import os
import re

def get_decisions():
    decisions = []
    for x in sys.argv[1:]:
        name = os.path.basename(x)
        study_tree = re.compile(r'([^_]+_[0-9]+)_([^_]+)\.tre')
        m = study_tree.match(name)
        study = m.group(1)
        tree = m.group(2)
        decisions.append({"studyID":study,"treeID":tree,"SHA":0,"name":name})
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

