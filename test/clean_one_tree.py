#!/usr/bin/env python3
import logging
import json
import sys
import os
from propinquity import (clean_one_phylo_input,
                         is_int_type,
                         OTT,
                         read_as_json,
                         validate_config,
                         )

logger = logging.getLogger('propinquity.clean_one_tree')
level = logging.DEBUG
logger.setLevel(level)
ch = logging.StreamHandler()
ch.setLevel(level)
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def main(args):
    configfile = args[0]
    output_dir = args[1]
    nexson_fp = args[2]
    pruned_from_ott_json_fp = None if len(args) == 3 else args[3]
    to_prune_for_reasons = {}
    if pruned_from_ott_json_fp is not None:
        try:
            nonflagged_blob = read_as_json(pruned_from_ott_json_fp)
        except:
            nonflagged_blob = None
        if nonflagged_blob:
            for reason, id_list in nonflagged_blob.items():
                for ott_id in id_list:
                    to_prune_for_reasons[ott_id] = reason
    
    config = read_as_json(configfile)
    CFG = validate_config(config, logger)
    if os.path.exists(output_dir):
        assert os.path.isdir(output_dir)
    else:
        os.mkdir(output_dir)
    assert os.path.isfile(nexson_fp)
    CFG.debug(f"Reading OTT at {CFG.ott_dir}")
    ott = OTT(ott_dir=CFG.ott_dir)
    cleaning_flags = CFG.cleaning_flags
    if cleaning_flags is None:
        cleaning_flags = OTT.TREEMACHINE_SUPPRESS_FLAGS
    flags = [i.strip() for i in cleaning_flags.split(',') if i.strip()]
    CFG.debug(f"cleaning_flags={cleaning_flags}")
    to_prune_fsi_set = ott.convert_flag_string_set_to_union(flags)
    root_ott_id = CFG.root_ott_id
    if (root_ott_id is not None) and (not is_int_type(root_ott_id)):
        root_ott_id = int(root_ott_id)


    clean_one_phylo_input(output_dir,
                          nexson_fp,
                          ott,
                          to_prune_fsi_set,
                          root_ott_id,
                          to_prune_for_reasons,
                          CFG)

if __name__ == '__main__':
    main(sys.argv[1:])