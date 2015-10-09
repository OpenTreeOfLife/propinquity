CONFIG_FILENAME=config

OTT_FILENAMES=about.json \
	conflicts.tsv \
	deprecated.tsv \
	synonyms.tsv \
	taxonomy.tsv \
	version.txt

OTT_FILEPATHS=$(addprefix $(OTT_DIR)/, $(OTT_FILENAMES))

PRUNE_DUBIOUS_ARTIFACTS=cleaned_ott/cleaned_ott.tre \
	cleaned_ott/cleaned_ott.json \
	cleaned_ott/ott_version.txt \
	cleaned_ott/cleaning_flags.txt

INPUT_PHYLO_ARTIFACTS=phylo_input/studies.txt phylo_input/study_tree_pairs.txt phylo_input/rank_collection.json

STUDY_TREE_STEM=$(shell cat phylo_input/study_tree_pairs.txt)
STUDY_TREE_FN=$(addsuffix .json, $(STUDY_TREE_STEM))
SNAPSHOT_CACHE_STEM=$(addprefix phylo_snapshot/, $(STUDY_TREE_FN))
CLEANED_PHYLO=$(addprefix cleaned_phylo/, $(STUDY_TREE_FN))
SNAPSHOT_CACHE=$(addprefix phylo_snapshot/, $(STUDY_TREE_FN))

ARTIFACTS=$(PRUNE_DUBIOUS_ARTIFACTS) \
	$(INPUT_PHYLO_ARTIFACTS) \
	phylo_snapshot/git_shas.txt \
	phylo_snapshot/concrete_rank_collection.json \
	cleaned_phylo/cleaning_flags.txt \
	cleaned_phylo/phylo_inputs_cleaned.txt


# default is "all"
all: $(ARTIFACTS)
	echo $(CLEANED_PHYLO)

clean:
	rm -f $(ARTIFACTS)
	rm -f $(CLEANED_PHYLO)

# "cleaned_ott" has dubious taxa pruned off. should check against treemachine and smasher versions
cleaned_ott/cleaning_flags.txt: $(CONFIG_FILENAME)
	./bin/config_checker.py --config=$(CONFIG_FILENAME) --property=cleaning_flags > cleaned_ott/.raw_cleaning_flags.txt
	if ! diff cleaned_ott/.raw_cleaning_flags.txt cleaned_ott/cleaning_flags.txt ; then mv cleaned_ott/.raw_cleaning_flags.txt cleaned_ott/cleaning_flags.txt ; fi


cleaned_ott/ott_version.txt: $(OTT_DIR)/version.txt
	if ! diff $(OTT_DIR)/version.txt cleaned_ott/ott_version.txt >/dev/null 2>&1 ; then cp $(OTT_DIR)/version.txt cleaned_ott/ott_version.txt ; fi

cleaned_ott/cleaned_ott.tre: $(OTT_FILEPATHS) cleaned_ott/ott_version.txt cleaned_ott/cleaning_flags.txt
	$(PEYOTL_ROOT)/scripts/ott/suppress_by_flag.py \
	    --ott-dir=$(OTT_DIR) \
	    --output=cleaned_ott/cleaned_ott.tre \
	    --log=cleaned_ott/cleaned_ott.json \
	    --flags="$(shell cat cleaned_ott/cleaning_flags.txt)"

cleaned_ott/cleaned_ott.json: cleaned_ott/cleaned_ott.tre
	

# phylo_input holds the lists of study+tree pairs to be used during the supertree construction
phylo_input/rank_collection.json: 
	echo '***TEMPORARY WORKAROUND***!!!!'
	curl -o phylo_input/rank_collection.json http://phylo.bio.ku.edu/ot/synthesis-collection.json

phylo_input/studies.txt: phylo_input/rank_collection.json
	$(PEYOTL_ROOT)/scripts/collection_export.py --export=studyID phylo_input/rank_collection.json >phylo_input/studies.txt

phylo_input/study_tree_pairs.txt: phylo_input/rank_collection.json
	$(PEYOTL_ROOT)/scripts/collection_export.py --export=studyID_treeID phylo_input/rank_collection.json >phylo_input/study_tree_pairs.txt

phylo_snapshot/git_shas.txt:
	./bin/shard_shas.sh > .tmp_git_shas.txt
	if ! diff phylo_snapshot/git_shas.txt .tmp_git_shas.txt >/dev/null 2>&1 ; then mv .tmp_git_shas.txt phylo_snapshot/git_shas.txt ; else rm .tmp_git_shas.txt ; fi

phylo_snapshot/concrete_rank_collection.json: phylo_snapshot/git_shas.txt phylo_input/rank_collection.json
	$(PEYOTL_ROOT)/scripts/phylesystem/export_studies_from_collection.py \
	  --phylesystem-par=$(PHYLESYSTEM_ROOT)/shards \
	  --output-dir=phylo_snapshot \
	  phylo_input/rank_collection.json \
	  -v 2>&1 || tee phylo_snapshot/stdouterr.txt

$(SNAPSHOT_CACHE):  phylo_snapshot/git_shas.txt phylo_snapshot/concrete_rank_collection.json


define SNAPSHOT_CACHE_VAR
$(SNAPSHOT_CACHE)
endef
export SNAPSHOT_CACHE_VAR

cleaned_phylo/phylo_inputs_cleaned.txt: $(SNAPSHOT_CACHE) cleaned_ott/cleaning_flags.txt
	if ! diff cleaned_ott/cleaning_flags.txt cleaned_phylo/cleaning_flags.txt >/dev/null 2>&1 ; \
	then echo $$SNAPSHOT_CACHE_VAR | sed -E 's/ /\n/g' > cleaned_phylo/needs_updating.txt ;\
	fi
	$(PEYOTL_ROOT)/scripts/nexson/prune_to_clean_mapped.py \
	  --ott-dir=$(OTT_DIR) \
	  --input-files-list=cleaned_phylo/needs_updating.txt \
	  --out-dir=cleaned_phylo \
	  --ott-prune-flags="$(shell cat cleaned_ott/cleaning_flags.txt)"

cleaned_phylo/cleaning_flags.txt: cleaned_phylo/phylo_inputs_cleaned.txt
	cp cleaned_ott/cleaning_flags.txt cleaned_phylo/cleaning_flags.txt