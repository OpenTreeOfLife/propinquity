OTT_FILENAMES=about.json \
	conflicts.tsv \
	deprecated.tsv \
	synonyms.tsv \
	taxonomy.tsv \
	version.txt

OTT_FILEPATHS=$(addprefix $(OTT_DIR)/, $(OTT_FILENAMES))

PRUNE_DUBIOUS_ARTIFACTS=cleaned_ott/cleaned_ott.tre \
	cleaned_ott/cleaned_ott.log \
	cleaned_ott/ott_version.txt

ARTIFACTS=$(PRUNE_DUBIOUS_ARTIFACTS)

# default is "all"
all: $(ARTIFACTS)

clean:
	rm -f $(ARTIFACTS)

cleaned_ott/ott_version.txt: $(OTT_DIR)/version.txt
	if ! test -d cleaned_ott ; then mkdir cleaned_ott ; fi
	if ! diff $(OTT_DIR)/version.txt cleaned_ott/ott_version.txt >/dev/null 2>&1 ; then cp $(OTT_DIR)/version.txt cleaned_ott/ott_version.txt ; fi

cleaned_ott/cleaned_ott.tre: $(OTT_FILEPATHS) cleaned_ott/ott_version.txt
	if ! test -d cleaned_ott ; then mkdir cleaned_ott ; fi
	$(PEYOTL_ROOT)/scripts/ott/suppress-dubious.py --ott-dir=$(OTT_DIR) --output=cleaned_ott/cleaned_ott.tre --log=cleaned_ott/cleaned_ott.log