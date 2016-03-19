#!/bin/sh
rm -f logs/complete_log.txt
time bin/rebuild_from_latest.sh 2>logs/complete_log_error.txt | tee logs/complete_log.txt